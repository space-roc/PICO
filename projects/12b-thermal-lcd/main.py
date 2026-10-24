# Project 13b: MLX90640 thermal camera on the Waveshare Pico-LCD-1.8
#
# Everything runs on the Pico, with no PC. The Pico reads the sensor over I2C,
# calculates the temperatures (mlx_calc.py) and draws them on the LCD.
#
#   LCD   (fits straight onto the Pico, or wire it to the same pins):
#         DIN GP11, CLK GP10, CS GP9, DC GP8, RST GP12, BL GP13, VCC VSYS, GND GND
#   MLX90640 breakout:
#         SDA GP4, SCL GP5, 3-5V -> 3V3 (OUT), GND -> GND
#
# Upload both main.py and mlx_calc.py to the Pico.

import gc
import struct
import micropython
from array import array
from framebuf import FrameBuffer, RGB565
from machine import I2C, Pin, SPI
from micropython import const
from time import sleep_ms, ticks_diff, ticks_ms

from mlx_calc import EEPROM_WORDS, HEIGHT, PIXELS, WIDTH, Calibration, smooth_stale

try:
    from rp2 import bootsel_button
except ImportError:
    bootsel_button = None

SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400000
ADDRESS = 0x33

# 0 = 0.5 Hz, 1 = 1 Hz, 2 = 2 Hz, 3 = 4 Hz, 4 = 8 Hz. Each frame is two
# subpages, so 2 Hz means 4 pictures a second. If the Pico can't keep up, the
# picture updates more slowly but still works; lower this to match.
REFRESH_RATE = 2
READY_TIMEOUT_MS = 2000

MIN_C = 15.0 # Bottom of the colour range
MAX_C = 40.0 # Top of the colour range
AUTO_RANGE = False # True: use the coldest and hottest pixels in view instead
AUTO_MIN_SPAN_C = 10.0 # Smallest range used by AUTO_RANGE, so noise isn't stretched
MIRROR = True # Flip the picture left to right, as project 12's viewer does
PALETTE = "inferno" # Press BOOTSEL on the Pico to switch to the next one

STATUS_REG = 0x8000
CONTROL_REG = 0x800D
EEPROM_START = 0x2400
RAM_START = 0x0400
DATA_READY = 0x0008

# The LCD in landscape: 160x128 visible. The 32x24 sensor image is drawn five
# times as big (160x120), with a line of text underneath.
SCREEN_WIDTH = 160
BUFFER_WIDTH = const(161)
BUFFER_HEIGHT = 130
IMAGE_WIDTH = const(160)
IMAGE_HEIGHT = const(120)
TEXT_Y = 120

GRID_WIDTH = const(32)
GRID_HEIGHT = const(24)
GRID_MAX = 65280 # Temperatures are scaled to 0..GRID_MAX, which is 255 << 8

PALETTES = { # Colour stops from cold (0) to hot (1)
    "inferno": [(0.00, (0, 0, 4)), (0.15, (40, 11, 84)), (0.30, (101, 21, 110)),
                (0.45, (159, 42, 99)), (0.60, (212, 72, 66)), (0.75, (245, 125, 21)),
                (0.90, (250, 193, 39)), (1.00, (252, 255, 164))],
    "iron": [(0.00, (0, 0, 0)), (0.20, (32, 0, 110)), (0.40, (150, 0, 120)),
             (0.60, (230, 60, 20)), (0.80, (255, 190, 20)), (1.00, (255, 255, 255))],
    "rainbow": [(0.00, (0, 0, 160)), (0.25, (0, 140, 255)), (0.50, (0, 220, 60)),
                (0.75, (255, 230, 0)), (1.00, (230, 0, 0))],
    "viridis": [(0.00, (68, 1, 84)), (0.25, (59, 82, 139)), (0.50, (33, 144, 140)),
                (0.75, (93, 201, 99)), (1.00, (253, 231, 37))],
    "whitehot": [(0.00, (0, 0, 0)), (1.00, (255, 255, 255))],
    "blackhot": [(0.00, (255, 255, 255)), (1.00, (0, 0, 0))],
}


def lcd_color(rgb565):
    # FrameBuffer stores RGB565 little-endian; the LCD expects high byte first.
    return ((rgb565 & 0xFF) << 8) | (rgb565 >> 8)


BLACK = 0x0000
WHITE = 0xFFFF


class PicoLCD18(FrameBuffer):
    def __init__(self):
        self.spi = SPI(
            1,
            baudrate=10_000_000,
            polarity=0,
            phase=0,
            sck=Pin(10),
            mosi=Pin(11),
        )
        self.cs = Pin(9, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.reset = Pin(12, Pin.OUT, value=1)
        self.backlight = Pin(13, Pin.OUT, value=1)
        self.buffer = bytearray(BUFFER_WIDTH * BUFFER_HEIGHT * 2)
        super().__init__(self.buffer, BUFFER_WIDTH, BUFFER_HEIGHT, RGB565)
        self._initialize()

    def _command(self, command, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytes((command,)))
        if data:
            self.dc(1)
            self.spi.write(data)
        self.cs(1)

    def _initialize(self):
        self.reset(1)
        sleep_ms(10)
        self.reset(0)
        sleep_ms(20)
        self.reset(1)
        sleep_ms(120)

        # ST7735S setup values for Waveshare's Pico-LCD-1.8.
        setup = (
            (0x36, b"\x70"),
            (0x3A, b"\x05"),
            (0xB1, b"\x01\x2C\x2D"),
            (0xB2, b"\x01\x2C\x2D"),
            (0xB3, b"\x01\x2C\x2D\x01\x2C\x2D"),
            (0xB4, b"\x07"),
            (0xC0, b"\xA2\x02\x84"),
            (0xC1, b"\xC5"),
            (0xC2, b"\x0A\x00"),
            (0xC3, b"\x8A\x2A"),
            (0xC4, b"\x8A\xEE"),
            (0xC5, b"\x0E"),
            (0xE0, b"\x0F\x1A\x0F\x18\x2F\x28\x20\x22\x1F\x1B\x23\x37\x00\x07\x02\x10"),
            (0xE1, b"\x0F\x1B\x0F\x17\x33\x2C\x29\x2E\x30\x30\x39\x3F\x00\x07\x03\x10"),
            (0xF0, b"\x01"),
            (0xF6, b"\x00"),
        )
        for command, data in setup:
            self._command(command, data)
        self._command(0x11)
        sleep_ms(120)
        self._command(0x29)

    def show(self):
        # The vendor demo uses this address range for this panel.
        self._command(0x2A, b"\x00\x01\x00\xF1")
        self._command(0x2B, b"\x00\x01\x00\xF1")
        self._command(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)

    def message(self, *lines):
        self.fill(BLACK)
        for number, line in enumerate(lines):
            self.text(line, 0, 4 + number * 10, WHITE)
        self.show()


def build_palette(name):
    # 256 colours from cold to hot, as RGB565 in the LCD's byte order.
    stops = PALETTES[name]
    palette = array("H")
    for index in range(256):
        position = index / 255
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if position <= p1:
                f = (position - p0) / (p1 - p0)
                red, green, blue = (round(low + (high - low) * f)
                                    for low, high in zip(c0, c1))
                palette.append(lcd_color((red & 0xF8) << 8 | (green & 0xFC) << 3 | blue >> 3))
                break
    return palette


def axis_map(size, out_size, mirror):
    # For each output pixel: the two source pixels to blend, and how much (0-255)
    # of the second one to use.
    mapping = array("H")
    for out in range(out_size):
        position = (out + 0.5) * size / out_size - 0.5
        if mirror:
            position = size - 1 - position
        position = min(max(position, 0), size - 1)
        low = int(position)
        mapping.append(low)
        mapping.append(min(low + 1, size - 1))
        mapping.append(int((position - low) * 256))
    return mapping


@micropython.viper
def blend_rows(grid: ptr16, xmap: ptr16, rows: ptr16):
    # Stretch each of the 24 sensor rows from 32 to 160 pixels.
    for row in range(GRID_HEIGHT):
        source = row * GRID_WIDTH
        target = row * IMAGE_WIDTH
        for x in range(IMAGE_WIDTH):
            m = x * 3
            a = int(grid[source + int(xmap[m])])
            b = int(grid[source + int(xmap[m + 1])])
            f = int(xmap[m + 2])
            rows[target + x] = (a * (256 - f) + b * f) >> 8


@micropython.viper
def blend_columns(rows: ptr16, ymap: ptr16, palette: ptr16, out: ptr16):
    # Blend between those rows to get all 120, and colour each pixel.
    for y in range(IMAGE_HEIGHT):
        m = y * 3
        top = int(ymap[m]) * IMAGE_WIDTH
        bottom = int(ymap[m + 1]) * IMAGE_WIDTH
        f = int(ymap[m + 2])
        g = 256 - f
        target = y * BUFFER_WIDTH
        for x in range(IMAGE_WIDTH):
            v = (int(rows[top + x]) * g + int(rows[bottom + x]) * f + 32768) >> 16
            out[target + x] = palette[v]


class Camera:
    def __init__(self, i2c):
        self.i2c = i2c
        self.words = bytearray(832 * 2)

    def read_bytes(self, register, words):
        return self.i2c.readfrom_mem(ADDRESS, register, words * 2, addrsize=16)

    def read_word(self, register):
        data = self.read_bytes(register, 1)
        return data[0] << 8 | data[1]

    def write_word(self, register, value):
        self.i2c.writeto_mem(ADDRESS, register, bytes((value >> 8, value & 0xFF)), addrsize=16)

    def start(self):
        control = self.read_word(CONTROL_REG)
        self.write_word(CONTROL_REG, (control & 0xFC7F) | (REFRESH_RATE << 7))
        return struct.unpack(">832H", self.read_bytes(EEPROM_START, 832))

    def read_subpage(self):
        # Wait for a subpage, then read it. If a new one arrives while reading,
        # read again so the data isn't a mixture of two. Returns the subpage
        # number, the control register and the 832 signed words.
        start = ticks_ms()
        while not self.read_word(STATUS_REG) & DATA_READY:
            if ticks_diff(ticks_ms(), start) > READY_TIMEOUT_MS:
                raise RuntimeError("Sensor not ready")
            sleep_ms(2)

        for _ in range(5):
            self.write_word(STATUS_REG, 0x0030)
            self.i2c.readfrom_mem_into(ADDRESS, RAM_START, self.words, addrsize=16)
            status = self.read_word(STATUS_REG)
            if not status & DATA_READY:
                return (status & 0x0001, self.read_word(CONTROL_REG),
                        struct.unpack(">832h", self.words))
        raise RuntimeError("Too many retries")


class Picture:
    def __init__(self, display):
        self.display = display
        self.names = list(PALETTES)
        self.palette_name = PALETTE
        self.palette = build_palette(PALETTE)
        self.xmap = axis_map(GRID_WIDTH, IMAGE_WIDTH, MIRROR)
        self.ymap = axis_map(GRID_HEIGHT, IMAGE_HEIGHT, False)
        self.grid = array("H", [0] * PIXELS)
        self.rows = array("H", [0] * (GRID_HEIGHT * IMAGE_WIDTH))
        self.centre = (GRID_HEIGHT // 2) * GRID_WIDTH + (GRID_WIDTH // 2 - (1 if MIRROR else 0))

    def next_palette(self):
        index = (self.names.index(self.palette_name) + 1) % len(self.names)
        self.palette_name = self.names[index]
        self.palette = build_palette(self.palette_name)

    def draw(self, temps):
        low, high = MIN_C, MAX_C
        coldest, hottest = min(temps), max(temps)
        if AUTO_RANGE:
            low = coldest
            high = max(hottest, low + AUTO_MIN_SPAN_C)

        grid = self.grid
        factor = GRID_MAX / (high - low)
        for p in range(PIXELS):
            value = int((temps[p] - low) * factor + 0.5)
            grid[p] = 0 if value < 0 else GRID_MAX if value > GRID_MAX else value

        blend_rows(grid, self.xmap, self.rows)
        blend_columns(self.rows, self.ymap, self.palette, self.display.buffer)

        # Crosshair at the centre of the picture, and the temperatures.
        display = self.display
        cx, cy = IMAGE_WIDTH // 2, IMAGE_HEIGHT // 2
        display.hline(cx - 6, cy, 13, WHITE)
        display.vline(cx, cy - 6, 13, WHITE)
        display.fill_rect(0, TEXT_Y, SCREEN_WIDTH, 8, BLACK)
        display.text("C{:.1f} H{:.1f} L{:.1f}".format(temps[self.centre], hottest, coldest),
                     0, TEXT_Y, WHITE)
        display.show()


def start_camera(display):
    i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
    while ADDRESS not in i2c.scan():
        print("MLX90640 not found at 0x33")
        display.message("MLX90640 not found", "SDA GP{} SCL GP{}".format(SDA_PIN, SCL_PIN),
                        "Check wiring, 3V3, GND")
        sleep_ms(1000)
    camera = Camera(i2c)
    display.message("Thermal camera", "Reading calibration...")
    return camera, Calibration(camera.start())


def main():
    display = PicoLCD18()
    display.message("Thermal camera", "Starting...")
    camera, calibration = start_camera(display)
    gc.collect()

    picture = Picture(display)
    temps = array("f", [20.0] * PIXELS)
    shown = array("f", temps)
    was_pressed = False

    print("MLX90640 found. Showing frames...")
    while True:
        started = ticks_ms()
        try:
            sub_page, control, frame = camera.read_subpage()
            calibration.update(frame, control, sub_page, temps)
        except (RuntimeError, OSError) as error:
            print("Sensor error:", error)
            display.message("Sensor error", str(error)[:20], "Check wiring")
            sleep_ms(500)
            continue
        except (ValueError, ZeroDivisionError):
            continue # Corrupt data: wait for the next subpage

        smooth_stale(temps, calibration.fresh, shown)
        picture.draw(shown)

        pressed = bootsel_button is not None and bootsel_button()
        if pressed and not was_pressed:
            picture.next_palette()
        was_pressed = pressed

        gc.collect()
        print("{} ms per picture".format(ticks_diff(ticks_ms(), started)))


if __name__ == "__main__":
    main()
