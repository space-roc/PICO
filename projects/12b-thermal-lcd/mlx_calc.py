# MLX90640 temperature calculation for the Pico (MicroPython).
#
# A port of the calculation in Adafruit's CircuitPython MLX90640 driver (MIT
# licence, by ladyada for Adafruit Industries), which follows Melexis'
# reference code, with the I2C code removed. It is the same maths as project
# 12's mlx90640.py, reorganised to run quickly on a Pico: everything that
# doesn't change from frame to frame is worked out once in Calibration(), and
# the per-pixel values are kept in compact float arrays.
#
# It uses no Pico-only modules, so it also runs on a PC.

import math
from array import array

WIDTH = 32
HEIGHT = 24
PIXELS = WIDTH * HEIGHT
EEPROM_WORDS = 832
OPENAIR_TA_SHIFT = 8 # Reflected temperature is this much below the sensor's
EMISSIVITY = 0.95
SCALEALPHA = 0.000001
MOTION_FULL_C = 1.5 # See smooth_stale()


def signed(value, limit, modulus):
    return value - modulus if value > limit else value


def nibbles(words):
    # Four signed 4-bit values per word, lowest nibble first.
    return [signed((word >> shift) & 0xF, 7, 16) for word in words for shift in (0, 4, 8, 12)]


def round_away(value):
    return int(value - 0.5) if value < 0 else int(value + 0.5)


def scale_factor(values, limit):
    # Number of doublings that bring the largest value up to `limit`.
    largest = max(values)
    doublings = 0
    while largest < limit:
        largest *= 2
        doublings += 1
    return doublings


class Calibration:
    def __init__(self, eeprom):
        """`eeprom` is the sensor's 832 EEPROM words as unsigned numbers."""
        if len(eeprom) != EEPROM_WORDS:
            raise ValueError("EEPROM data must be {} words".format(EEPROM_WORDS))
        ee = eeprom

        self.k_vdd = signed((ee[51] & 0xFF00) >> 8, 127, 256) * 32
        self.vdd25 = (((ee[51] & 0x00FF) - 256) << 5) - 8192

        self.kv_ptat = signed((ee[50] & 0xFC00) >> 10, 31, 64) / 4096
        self.kt_ptat = signed(ee[50] & 0x03FF, 511, 1024) / 8
        self.v_ptat25 = ee[49]
        self.alpha_ptat = (ee[16] & 0xF000) / math.pow(2, 14) + 8

        self.gain_ee = signed(ee[48], 32767, 65536)
        self.tgc = signed(ee[60] & 0xFF, 127, 256) / 32
        self.resolution_ee = (ee[56] & 0x3000) >> 12
        self.ks_ta = signed((ee[60] & 0xFF00) >> 8, 127, 256) / 8192

        step = ((ee[63] & 0x3000) >> 12) * 10
        self.ct = [-40, 0, ((ee[63] & 0x00F0) >> 4) * step, 0]
        self.ct[3] = self.ct[2] + ((ee[63] & 0x0F00) >> 8) * step
        ks_scale = 1 << ((ee[63] & 0x000F) + 8)
        self.ks_to = [signed(value, 127, 256) / ks_scale
                      for value in (ee[61] & 0x00FF, (ee[61] & 0xFF00) >> 8,
                                    ee[62] & 0x00FF, (ee[62] & 0xFF00) >> 8)]

        self._extract_cp(ee)
        self._extract_pixels(ee)

        self.calibration_mode_ee = ((ee[10] & 0x0800) >> 4) ^ 0x80
        self.il_chess_c = [
            signed(ee[53] & 0x003F, 31, 64) / 16.0,
            signed((ee[53] & 0x07C0) >> 6, 15, 32) / 2.0,
            signed((ee[53] & 0xF800) >> 11, 15, 32) / 8.0,
        ]
        self._build_patterns()
        self._pixel_lists = {}

    def _extract_cp(self, ee):
        # The two "compensation pixels" that correct for temperature and gain.
        alpha_scale = ((ee[32] & 0xF000) >> 12) + 27

        offset0 = signed(ee[58] & 0x03FF, 511, 1024)
        offset1 = signed((ee[58] & 0xFC00) >> 10, 31, 64) + offset0

        alpha0 = signed(ee[57] & 0x03FF, 511, 1024) / math.pow(2, alpha_scale)
        alpha1 = (1 + signed((ee[57] & 0xFC00) >> 10, 31, 64) / 128) * alpha0

        kta_scale = ((ee[56] & 0x00F0) >> 4) + 8
        self.cp_kta = signed(ee[59] & 0x00FF, 127, 256) / math.pow(2, kta_scale)
        kv_scale = (ee[56] & 0x0F00) >> 8
        self.cp_kv = signed((ee[59] & 0xFF00) >> 8, 127, 256) / math.pow(2, kv_scale)

        self.cp_alpha = [alpha0, alpha1]
        self.cp_offset = [offset0, offset1]

    def _extract_pixels(self, ee):
        # Per-pixel constants, kept as float arrays (4 bytes each).
        rem_scale = ee[32] & 0x000F
        column_scale = (ee[32] & 0x00F0) >> 4
        row_scale = (ee[32] & 0x0F00) >> 8
        alpha_scale = ((ee[32] & 0xF000) >> 12) + 30
        alpha_ref = ee[33]
        acc_row = nibbles(ee[34:40])
        acc_column = nibbles(ee[40:48])

        alpha_temp = []
        for i in range(HEIGHT):
            for j in range(WIDTH):
                p = WIDTH * i + j
                value = signed((ee[64 + p] & 0x03F0) >> 4, 31, 64)
                value *= 1 << rem_scale
                value += alpha_ref + (acc_row[i] << row_scale) + (acc_column[j] << column_scale)
                value /= math.pow(2, alpha_scale)
                value -= self.tgc * (self.cp_alpha[0] + self.cp_alpha[1]) / 2
                alpha_temp.append(SCALEALPHA / value)
        scale = math.pow(2, scale_factor(alpha_temp, 32768))
        self.alpha = array("f", (SCALEALPHA * scale / int(value * scale + 0.5)
                                 for value in alpha_temp))
        del alpha_temp

        rem_scale = ee[16] & 0x000F
        column_scale = (ee[16] & 0x00F0) >> 4
        row_scale = (ee[16] & 0x0F00) >> 8
        offset_ref = signed(ee[17], 32767, 65536)
        occ_row = nibbles(ee[18:24])
        occ_column = nibbles(ee[24:32])

        self.offset = array("f")
        for i in range(HEIGHT):
            for j in range(WIDTH):
                p = WIDTH * i + j
                value = signed((ee[64 + p] & 0xFC00) >> 10, 31, 64)
                value *= 1 << rem_scale
                value += offset_ref + (occ_row[i] << row_scale) + (occ_column[j] << column_scale)
                self.offset.append(value)

        # Index: 0 odd row/odd column, 1 odd row/even column, 2 even/odd, 3 even/even
        kta_rc = [signed((ee[54] & 0xFF00) >> 8, 127, 256),
                  signed((ee[55] & 0xFF00) >> 8, 127, 256),
                  signed(ee[54] & 0x00FF, 127, 256),
                  signed(ee[55] & 0x00FF, 127, 256)]
        scale1 = ((ee[56] & 0x00F0) >> 4) + 8
        scale2 = ee[56] & 0x000F
        kta_temp = []
        for p in range(PIXELS):
            split = 2 * (p // 32 - (p // 64) * 2) + p % 2
            value = signed((ee[64 + p] & 0x000E) >> 1, 3, 8)
            value *= 1 << scale2
            value += kta_rc[split]
            kta_temp.append(value / math.pow(2, scale1))
        scale = math.pow(2, scale_factor([abs(value) for value in kta_temp], 64))
        self.kta = array("f", (round_away(value * scale) / scale for value in kta_temp))
        del kta_temp

        kv_t = [signed((ee[52] & 0xF000) >> 12, 7, 16),
                signed((ee[52] & 0x00F0) >> 4, 7, 16),
                signed((ee[52] & 0x0F00) >> 8, 7, 16),
                signed(ee[52] & 0x000F, 7, 16)]
        scale = (ee[56] & 0x0F00) >> 8
        kv_temp = []
        for p in range(PIXELS):
            split = 2 * (p // 32 - (p // 64) * 2) + p % 2
            kv_temp.append(kv_t[split] / math.pow(2, scale))
        scale = math.pow(2, scale_factor([abs(value) for value in kv_temp], 64))
        self.kv = array("f", (round_away(value * scale) / scale for value in kv_temp))
        del kv_temp

        # Pixels with no calibration data (0) or flagged as outliers (bit 0).
        self.bad_pixels = [p for p in range(PIXELS)
                           if ee[64 + p] == 0 or ee[64 + p] & 0x0001]
        self.bad = bytearray(PIXELS)
        for p in self.bad_pixels:
            self.bad[p] = 1

    def _build_patterns(self):
        # Which subpage each pixel belongs to in each mode, and the correction
        # added to the pixels when the sensor isn't in its calibration mode.
        self.il_pattern = bytearray(PIXELS)
        self.chess_pattern = bytearray(PIXELS)
        self.chess_correction = array("f")
        for p in range(PIXELS):
            interlaced = p // 32 - (p // 64) * 2
            conversion = ((p + 2) // 4 - (p + 3) // 4 + (p + 1) // 4 - p // 4) \
                * (1 - 2 * interlaced)
            self.il_pattern[p] = interlaced
            self.chess_pattern[p] = interlaced ^ (p - (p // 2) * 2)
            self.chess_correction.append(self.il_chess_c[2] * (2 * interlaced - 1)
                                         - self.il_chess_c[1] * conversion)

    def _pixels(self, mode, sub_page):
        # The good pixels measured by this subpage in this mode.
        key = (mode, sub_page)
        if key not in self._pixel_lists:
            pattern = self.il_pattern if mode == 0 else self.chess_pattern
            self._pixel_lists[key] = [p for p in range(PIXELS)
                                      if pattern[p] == sub_page and not self.bad[p]]
        return self._pixel_lists[key]

    def supply_voltage(self, frame, control):
        resolution_ram = (control & 0x0C00) >> 10
        correction = math.pow(2, self.resolution_ee) / math.pow(2, resolution_ram)
        return (correction * frame[810] - self.vdd25) / self.k_vdd + 3.3

    def sensor_temperature(self, frame, vdd):
        ptat = frame[800]
        ptat_art = (ptat / (ptat * self.alpha_ptat + frame[768])) * math.pow(2, 18)
        ta = ptat_art / (1 + self.kv_ptat * (vdd - 3.3)) - self.v_ptat25
        return ta / self.kt_ptat + 25

    def update(self, frame, control, sub_page, temperatures):
        """Update `temperatures` (768 values, C) with the pixels measured by this
        subpage. `frame` is the 832 signed words read from the sensor's RAM;
        `control` is its control register. Pixels that fail to calculate keep
        their previous value. Sets `self.fresh` to flag the pixels updated, and
        returns the sensor's own temperature."""
        vdd = self.supply_voltage(frame, control)
        ta = self.sensor_temperature(frame, vdd)
        tr = ta - OPENAIR_TA_SHIFT

        ta4 = (ta + 273.15) ** 4
        tr4 = (tr + 273.15) ** 4
        ta_tr = tr4 - (tr4 - ta4) / EMISSIVITY

        ks_to, ct = self.ks_to, self.ct
        alpha_corr_r = [1 / (1 + ks_to[0] * 40), 1, 1 + ks_to[1] * ct[2], 0]
        alpha_corr_r[3] = alpha_corr_r[2] * (1 + ks_to[2] * (ct[3] - ct[2]))

        gain = self.gain_ee / frame[778]
        mode = (control & 0x1000) >> 5
        ir_cp = [frame[776] * gain, frame[808] * gain]
        cp_factor = (1 + self.cp_kta * (ta - 25)) * (1 + self.cp_kv * (vdd - 3.3))
        ir_cp[0] -= self.cp_offset[0] * cp_factor
        if mode == self.calibration_mode_ee:
            ir_cp[1] -= self.cp_offset[1] * cp_factor
        else:
            ir_cp[1] -= (self.cp_offset[1] + self.il_chess_c[0]) * cp_factor
        tgc_cp = self.tgc * ir_cp[sub_page]

        dta = ta - 25
        dvdd = vdd - 3.3
        ks_ta_factor = 1 + self.ks_ta * dta
        chess_fix = mode != self.calibration_mode_ee
        ks1 = ks_to[1]
        k0 = 1 - ks1 * 273.15
        ct1, ct2, ct3 = ct[1], ct[2], ct[3]

        offset, kta, kv, alpha_all = self.offset, self.kta, self.kv, self.alpha
        chess = self.chess_correction
        sqrt = math.sqrt
        fresh = bytearray(PIXELS)

        for p in self._pixels(mode, sub_page):
            ir = frame[p] * gain
            ir -= offset[p] * (1 + kta[p] * dta) * (1 + kv[p] * dvdd)
            if chess_fix:
                ir += chess[p]
            ir = (ir - tgc_cp) / EMISSIVITY

            alpha = alpha_all[p] * ks_ta_factor
            try:
                sx = alpha * alpha * alpha * (ir + alpha * ta_tr)
                sx = sqrt(sqrt(sx)) * ks1
                to = sqrt(sqrt(ir / (alpha * k0 + sx) + ta_tr)) - 273.15

                if to < ct1:
                    t_range = 0
                elif to < ct2:
                    t_range = 1
                elif to < ct3:
                    t_range = 2
                else:
                    t_range = 3

                to = sqrt(sqrt(
                    ir / (alpha * alpha_corr_r[t_range]
                          * (1 + ks_to[t_range] * (to - ct[t_range]))) + ta_tr)) - 273.15
            except (ValueError, ZeroDivisionError):
                continue
            temperatures[p] = to
            fresh[p] = 1

        self.fresh = fresh
        self._fill_bad_pixels(temperatures)
        return ta

    def _fill_bad_pixels(self, temperatures):
        # Replace each bad pixel with the average of its good neighbours.
        bad = self.bad
        for p in self.bad_pixels:
            row, column = divmod(p, WIDTH)
            total = 0
            count = 0
            for r, c in ((row - 1, column), (row + 1, column),
                         (row, column - 1), (row, column + 1)):
                n = r * WIDTH + c
                if 0 <= r < HEIGHT and 0 <= c < WIDTH and not bad[n]:
                    total += temperatures[n]
                    count += 1
            if count:
                temperatures[p] = total / count


def smooth_stale(temperatures, fresh, result):
    """The sensor updates half the pixels (in a chessboard pattern) at a time, so
    when something moves the other half is out of date and shows as a
    checkerboard. Copy `temperatures` into `result`, pulling each stale pixel
    towards the average of its fresh neighbours, more strongly the more they
    disagree."""
    for p in range(PIXELS):
        result[p] = temperatures[p]
    for p in range(PIXELS):
        if fresh[p]:
            continue
        row, column = divmod(p, WIDTH)
        total = 0
        count = 0
        if row > 0 and fresh[p - WIDTH]:
            total += temperatures[p - WIDTH]
            count += 1
        if row < HEIGHT - 1 and fresh[p + WIDTH]:
            total += temperatures[p + WIDTH]
            count += 1
        if column > 0 and fresh[p - 1]:
            total += temperatures[p - 1]
            count += 1
        if column < WIDTH - 1 and fresh[p + 1]:
            total += temperatures[p + 1]
            count += 1
        if count:
            average = total / count
            weight = abs(average - temperatures[p]) / MOTION_FULL_C
            if weight > 1:
                weight = 1
            result[p] = temperatures[p] + (average - temperatures[p]) * weight
