# MLX90640 temperature calculation. Runs on the PC (not the Pico).
#
# The Pico sends the sensor's raw EEPROM and raw frame data; this module turns
# them into 32x24 temperatures in degrees C. It is a port of the calculation in
# Adafruit's CircuitPython MLX90640 driver (MIT licence, by ladyada for Adafruit
# Industries), which follows Melexis' reference code, with the I2C code removed.

import math

WIDTH = 32
HEIGHT = 24
PIXELS = WIDTH * HEIGHT
EEPROM_WORDS = 832
FRAME_WORDS = 834 # 832 of pixel data, then the control register and subpage
OPENAIR_TA_SHIFT = 8 # Reflected temperature is this much below the sensor's
EMISSIVITY = 0.95
SCALEALPHA = 0.000001


def signed(value, limit, modulus):
    return value - modulus if value > limit else value


def nibbles(words):
    # Four signed 4-bit values per word, lowest nibble first.
    return [signed((word >> shift) & 0xF, 7, 16) for word in words for shift in (0, 4, 8, 12)]


def round_away(value):
    return int(value - 0.5) if value < 0 else int(value + 0.5)


class MLX90640Calibration:
    def __init__(self, eeprom):
        if len(eeprom) != EEPROM_WORDS:
            raise ValueError("EEPROM data must be {} words".format(EEPROM_WORDS))
        self.ee = eeprom
        self._extract_vdd()
        self._extract_ptat()
        self.gain_ee = signed(eeprom[48], 32767, 65536)
        self.tgc = signed(eeprom[60] & 0xFF, 127, 256) / 32
        self.resolution_ee = (eeprom[56] & 0x3000) >> 12
        self.ks_ta = signed((eeprom[60] & 0xFF00) >> 8, 127, 256) / 8192
        self._extract_ks_to()
        self._extract_cp()
        self._extract_alpha()
        self._extract_offset()
        self._extract_kta()
        self._extract_kv()
        self._extract_chess_correction()
        self._extract_bad_pixels()
        self._build_patterns()

    def _extract_vdd(self):
        ee = self.ee
        self.k_vdd = signed((ee[51] & 0xFF00) >> 8, 127, 256) * 32
        self.vdd25 = (((ee[51] & 0x00FF) - 256) << 5) - 8192

    def _extract_ptat(self):
        ee = self.ee
        self.kv_ptat = signed((ee[50] & 0xFC00) >> 10, 31, 64) / 4096
        self.kt_ptat = signed(ee[50] & 0x03FF, 511, 1024) / 8
        self.v_ptat25 = ee[49]
        self.alpha_ptat = (ee[16] & 0xF000) / math.pow(2, 14) + 8

    def _extract_ks_to(self):
        ee = self.ee
        step = ((ee[63] & 0x3000) >> 12) * 10
        self.ct = [-40, 0, ((ee[63] & 0x00F0) >> 4) * step, 0]
        self.ct[3] = self.ct[2] + ((ee[63] & 0x0F00) >> 8) * step
        scale = 1 << ((ee[63] & 0x000F) + 8)
        raw = [ee[61] & 0x00FF, (ee[61] & 0xFF00) >> 8,
               ee[62] & 0x00FF, (ee[62] & 0xFF00) >> 8]
        self.ks_to = [signed(value, 127, 256) / scale for value in raw]

    def _extract_cp(self):
        ee = self.ee
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

    def _extract_alpha(self):
        ee = self.ee
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

        largest = max(alpha_temp)
        self.alpha_scale = 0
        while largest < 32768:
            largest *= 2
            self.alpha_scale += 1
        scale = math.pow(2, self.alpha_scale)
        self.alpha = [int(value * scale + 0.5) for value in alpha_temp]

    def _extract_offset(self):
        ee = self.ee
        rem_scale = ee[16] & 0x000F
        column_scale = (ee[16] & 0x00F0) >> 4
        row_scale = (ee[16] & 0x0F00) >> 8
        offset_ref = signed(ee[17], 32767, 65536)
        occ_row = nibbles(ee[18:24])
        occ_column = nibbles(ee[24:32])

        self.offset = []
        for i in range(HEIGHT):
            for j in range(WIDTH):
                p = WIDTH * i + j
                value = signed((ee[64 + p] & 0xFC00) >> 10, 31, 64)
                value *= 1 << rem_scale
                value += offset_ref + (occ_row[i] << row_scale) + (occ_column[j] << column_scale)
                self.offset.append(value)

    def _extract_kta(self):
        ee = self.ee
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

        largest = max(abs(value) for value in kta_temp)
        self.kta_scale = 0
        while largest < 64:
            largest *= 2
            self.kta_scale += 1
        scale = math.pow(2, self.kta_scale)
        self.kta = [round_away(value * scale) for value in kta_temp]

    def _extract_kv(self):
        ee = self.ee
        kv_t = [signed((ee[52] & 0xF000) >> 12, 7, 16),
                signed((ee[52] & 0x00F0) >> 4, 7, 16),
                signed((ee[52] & 0x0F00) >> 8, 7, 16),
                signed(ee[52] & 0x000F, 7, 16)]
        scale = (ee[56] & 0x0F00) >> 8

        kv_temp = []
        for p in range(PIXELS):
            split = 2 * (p // 32 - (p // 64) * 2) + p % 2
            kv_temp.append(kv_t[split] / math.pow(2, scale))

        largest = max(abs(value) for value in kv_temp)
        self.kv_scale = 0
        while largest < 64:
            largest *= 2
            self.kv_scale += 1
        scale = math.pow(2, self.kv_scale)
        self.kv = [round_away(value * scale) for value in kv_temp]

    def _extract_chess_correction(self):
        ee = self.ee
        self.calibration_mode_ee = ((ee[10] & 0x0800) >> 4) ^ 0x80
        self.il_chess_c = [
            signed(ee[53] & 0x003F, 31, 64) / 16.0,
            signed((ee[53] & 0x07C0) >> 6, 15, 32) / 2.0,
            signed((ee[53] & 0xF800) >> 11, 15, 32) / 8.0,
        ]

    def _extract_bad_pixels(self):
        # Pixels with no calibration data (0) or flagged as outliers (bit 0).
        self.bad_pixels = [p for p in range(PIXELS)
                           if self.ee[64 + p] == 0 or self.ee[64 + p] & 0x0001]

    def _build_patterns(self):
        self.il_pattern = []
        self.chess_pattern = []
        self.conversion_pattern = []
        for p in range(PIXELS):
            interlaced = p // 32 - (p // 64) * 2
            self.il_pattern.append(interlaced)
            self.chess_pattern.append(interlaced ^ (p - (p // 2) * 2))
            self.conversion_pattern.append(
                ((p + 2) // 4 - (p + 3) // 4 + (p + 1) // 4 - p // 4) * (1 - 2 * interlaced))

    def supply_voltage(self, frame):
        vdd = signed(frame[810], 32767, 65536)
        resolution_ram = (frame[832] & 0x0C00) >> 10
        correction = math.pow(2, self.resolution_ee) / math.pow(2, resolution_ram)
        return (correction * vdd - self.vdd25) / self.k_vdd + 3.3

    def sensor_temperature(self, frame):
        vdd = self.supply_voltage(frame)
        ptat = signed(frame[800], 32767, 65536)
        ptat_art = signed(frame[768], 32767, 65536)
        ptat_art = (ptat / (ptat * self.alpha_ptat + ptat_art)) * math.pow(2, 18)
        ta = ptat_art / (1 + self.kv_ptat * (vdd - 3.3)) - self.v_ptat25
        return ta / self.kt_ptat + 25

    def update(self, frame, temperatures):
        """Update `temperatures` (768 values, C) with the pixels in this frame's
        subpage. Pixels that fail to calculate keep their previous value."""
        if len(frame) != FRAME_WORDS:
            raise ValueError("Frame data must be {} words".format(FRAME_WORDS))

        sub_page = frame[833]
        vdd = self.supply_voltage(frame)
        ta = self.sensor_temperature(frame)
        tr = ta - OPENAIR_TA_SHIFT

        ta4 = (ta + 273.15) ** 4
        tr4 = (tr + 273.15) ** 4
        ta_tr = tr4 - (tr4 - ta4) / EMISSIVITY

        kta_scale = math.pow(2, self.kta_scale)
        kv_scale = math.pow(2, self.kv_scale)
        alpha_scale = math.pow(2, self.alpha_scale)
        ks_to, ct = self.ks_to, self.ct

        alpha_corr_r = [1 / (1 + ks_to[0] * 40), 1, 1 + ks_to[1] * ct[2], 0]
        alpha_corr_r[3] = alpha_corr_r[2] * (1 + ks_to[2] * (ct[3] - ct[2]))

        gain = self.gain_ee / signed(frame[778], 32767, 65536)

        mode = (frame[832] & 0x1000) >> 5
        ir_cp = [signed(frame[776], 32767, 65536) * gain,
                 signed(frame[808], 32767, 65536) * gain]
        cp_factor = (1 + self.cp_kta * (ta - 25)) * (1 + self.cp_kv * (vdd - 3.3))
        ir_cp[0] -= self.cp_offset[0] * cp_factor
        if mode == self.calibration_mode_ee:
            ir_cp[1] -= self.cp_offset[1] * cp_factor
        else:
            ir_cp[1] -= (self.cp_offset[1] + self.il_chess_c[0]) * cp_factor

        ks_ta_factor = 1 + self.ks_ta * (ta - 25)
        self.fresh = [False] * PIXELS # Pixels updated by this subpage

        for p in range(PIXELS):
            pattern = self.il_pattern[p] if mode == 0 else self.chess_pattern[p]
            if pattern != sub_page or p in self.bad_pixels:
                continue

            ir = signed(frame[p], 32767, 65536) * gain
            kta = self.kta[p] / kta_scale
            kv = self.kv[p] / kv_scale
            ir -= self.offset[p] * (1 + kta * (ta - 25)) * (1 + kv * (vdd - 3.3))
            if mode != self.calibration_mode_ee:
                ir += (self.il_chess_c[2] * (2 * self.il_pattern[p] - 1)
                       - self.il_chess_c[1] * self.conversion_pattern[p])
            ir -= self.tgc * ir_cp[sub_page]
            ir /= EMISSIVITY

            alpha = SCALEALPHA * alpha_scale / self.alpha[p] * ks_ta_factor
            try:
                sx = alpha ** 3 * (ir + alpha * ta_tr)
                sx = math.sqrt(math.sqrt(sx)) * ks_to[1]
                to = math.sqrt(math.sqrt(
                    ir / (alpha * (1 - ks_to[1] * 273.15) + sx) + ta_tr)) - 273.15

                if to < ct[1]:
                    t_range = 0
                elif to < ct[2]:
                    t_range = 1
                elif to < ct[3]:
                    t_range = 2
                else:
                    t_range = 3

                to = math.sqrt(math.sqrt(
                    ir / (alpha * alpha_corr_r[t_range]
                          * (1 + ks_to[t_range] * (to - ct[t_range]))) + ta_tr)) - 273.15
            except (ValueError, ZeroDivisionError):
                continue
            temperatures[p] = to
            self.fresh[p] = True

        self._fill_bad_pixels(temperatures)
        return ta

    def _fill_bad_pixels(self, temperatures):
        # Replace each bad pixel with the average of its good neighbours.
        for p in self.bad_pixels:
            row, column = divmod(p, WIDTH)
            neighbours = []
            for r, c in ((row - 1, column), (row + 1, column),
                         (row, column - 1), (row, column + 1)):
                n = r * WIDTH + c
                if 0 <= r < HEIGHT and 0 <= c < WIDTH and n not in self.bad_pixels:
                    neighbours.append(temperatures[n])
            if neighbours:
                temperatures[p] = sum(neighbours) / len(neighbours)
