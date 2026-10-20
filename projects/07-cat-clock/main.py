from framebuf import FrameBuffer, RGB565
from machine import Pin, RTC, SPI
from time import sleep, ticks_add, ticks_diff, ticks_ms

# Set the UTC time here before uploading. The Pico has no battery-backed clock.
START_DATETIME_UTC = (2026, 10, 17, 10, 29, 0)

SCREEN_WIDTH = 160
BUFFER_WIDTH = 161
BUFFER_HEIGHT = 130

BLACK = 0x0000


def lcd_color(rgb565):
    # FrameBuffer stores RGB565 little-endian; the LCD expects high byte first.
    return ((rgb565 & 0xFF) << 8) | (rgb565 >> 8)


TIME_COLOR = lcd_color(0xFFE0)
PUMPKIN_OUTLINE = lcd_color(0x2104)
PUMPKIN_ORANGE = lcd_color(0xFD20)
PUMPKIN_STRIPE = lcd_color(0xCB20)
PUMPKIN_SHADE = lcd_color(0xB280)
PUMPKIN_DARK = lcd_color(0x8A40)
PUMPKIN_HIGHLIGHT = lcd_color(0xFFE0)
PUMPKIN_GREEN = lcd_color(0x4D20)
PUMPKIN_GREEN_LIGHT = lcd_color(0x2AE0)
POO_OUTLINE = lcd_color(0x2104)
POO_BROWN = lcd_color(0x8A22)
POO_SHADE = lcd_color(0x6180)
POO_HIGHLIGHT = lcd_color(0xB48A)
POO_EYE = lcd_color(0xFFFF)
PIXEL_SIZE = 5
PUMPKIN_TOP = 26
POO_HALF_WIDTHS = (1, 2, 3, 4, 5, 6, 6, 7, 8, 9, 10, 10, 10, 10, 10, 9, 8)
POO_TIER_ROWS = (2, 5)
EXPRESSION_INTERVAL_MS = 3000
EXPRESSION_COUNT = 6


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
        sleep(0.01)
        self.reset(0)
        sleep(0.02)
        self.reset(1)
        sleep(0.12)

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
        sleep(0.12)
        self._command(0x29)

    def show(self):
        self._command(0x2A, b"\x00\x01\x00\xF1")
        self._command(0x2B, b"\x00\x01\x00\xF1")
        self._command(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)


SEGMENTS = {
    "0": "abcdef",
    "1": "bc",
    "2": "abged",
    "3": "abgcd",
    "4": "fgbc",
    "5": "afgcd",
    "6": "afgecd",
    "7": "abc",
    "8": "abcdefg",
    "9": "abfgcd",
}


def draw_digit(display, digit, x, y, color):
    width = 10
    height = 24
    thickness = 2
    half = height // 2
    segments = {
        "a": (x + thickness, y, width - 2 * thickness, thickness),
        "b": (x + width - thickness, y + thickness, thickness, half - thickness),
        "c": (x + width - thickness, y + half, thickness, half - thickness),
        "d": (x + thickness, y + height - thickness, width - 2 * thickness, thickness),
        "e": (x, y + half, thickness, half - thickness),
        "f": (x, y + thickness, thickness, half - thickness),
        "g": (x + thickness, y + half - thickness // 2, width - 2 * thickness, thickness),
    }
    for segment in SEGMENTS[digit]:
        display.fill_rect(*segments[segment], color)


def draw_time(display, hour, minute, second):
    value = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
    x = 39
    y = 2
    for index, character in enumerate(value):
        if character == ":":
            display.fill_rect(x, y + 7, 3, 3, TIME_COLOR)
            display.fill_rect(x, y + 16, 3, 3, TIME_COLOR)
            x += 3
        else:
            draw_digit(display, character, x, y, TIME_COLOR)
            x += 10
        if index < len(value) - 1:
            x += 2


def draw_expression(display, expression):
    def cell(x, y, color):
        screen_x = SCREEN_WIDTH // 2 - PIXEL_SIZE // 2 + x * PIXEL_SIZE
        screen_y = PUMPKIN_TOP + y * PIXEL_SIZE
        display.fill_rect(screen_x, screen_y, PIXEL_SIZE, PIXEL_SIZE, color)

    def row(y, left, right, color):
        for x in range(left, right + 1):
            cell(x, y, color)

    dark = PUMPKIN_OUTLINE

    if expression == 0:
        for y, half_width in ((7, 1), (8, 2), (9, 3)):
            row(y, -6 - half_width, -6 + half_width, dark)
            row(y, 6 - half_width, 6 + half_width, dark)
        for y, half_width in ((13, 3), (14, 5), (15, 7), (16, 8), (17, 7), (18, 4)):
            row(y, -half_width, half_width, dark)
        row(14, -1, 1, PUMPKIN_ORANGE)
        row(15, -4, -2, PUMPKIN_ORANGE)
        row(15, 3, 5, PUMPKIN_ORANGE)
    elif expression == 1:
        for y in (7, 8, 9):
            row(y, -7, -5, dark)
            row(y, 5, 7, dark)
        row(13, -1, 1, dark)
        row(14, -2, 2, dark)
        row(15, -2, 2, dark)
        row(16, -2, 2, dark)
        row(17, -1, 1, dark)
    elif expression == 2:
        row(8, -8, -5, dark)
        row(9, -7, -5, dark)
        row(8, 5, 8, dark)
        row(9, 5, 7, dark)
        for x in (-4, -3, -2, 2, 3, 4):
            cell(x, 14, dark)
        for x in (-3, -2, 2, 3):
            cell(x, 15, dark)
    elif expression == 3:
        row(7, -8, -6, dark)
        row(8, -7, -6, dark)
        row(9, -6, -5, dark)
        for y in (7, 8, 9):
            row(y, 5, 7, dark)
        for y, half_width in ((14, 2), (15, 4), (16, 5), (17, 4)):
            row(y, -half_width, half_width, dark)
        row(17, 1, 3, PUMPKIN_ORANGE)
        cell(3, 18, PUMPKIN_ORANGE)
    elif expression == 4:
        row(6, -8, -5, dark)
        row(7, -7, -5, dark)
        row(8, -6, -5, dark)
        row(6, 5, 8, dark)
        row(7, 5, 7, dark)
        row(8, 5, 6, dark)
        row(13, -5, 5, dark)
        row(14, -4, 4, dark)
    else:
        row(8, -8, -7, dark)
        row(7, -7, -5, dark)
        row(8, -5, -4, dark)
        row(8, 4, 5, dark)
        row(7, 5, 7, dark)
        row(8, 7, 8, dark)
        for y, half_width in ((14, 4), (15, 6), (16, 7), (17, 6), (18, 3)):
            row(y, -half_width, half_width, dark)
        row(16, -1, 1, PUMPKIN_ORANGE)
        row(17, -1, 1, PUMPKIN_ORANGE)


def draw_pumpkin(display, expression):
    def cell(x, y, color):
        screen_x = SCREEN_WIDTH // 2 - PIXEL_SIZE // 2 + x * PIXEL_SIZE
        screen_y = PUMPKIN_TOP + y * PIXEL_SIZE
        display.fill_rect(screen_x, screen_y, PIXEL_SIZE, PIXEL_SIZE, color)

    def row(y, left, right, color):
        for x in range(left, right + 1):
            cell(x, y, color)

    # Three-tier swirl of poo with a curled tip.
    last_row = len(POO_HALF_WIDTHS) - 1
    for y, half_width in enumerate(POO_HALF_WIDTHS):
        row(y, -half_width, half_width, POO_OUTLINE)
        row(y, -half_width + 1, half_width - 1, POO_BROWN)
        row(y, max(-half_width + 1, half_width - 3), half_width - 1, POO_SHADE)
        if y >= last_row - 1:
            row(y, -half_width + 1, half_width - 1, POO_SHADE)
        if y in POO_TIER_ROWS:
            row(y, -half_width + 1, half_width - 1, POO_SHADE)
    for y in (4, 5):
        cell(-3, y, POO_HIGHLIGHT)
    for y in (9, 10):
        cell(-6, y, POO_HIGHLIGHT)
    cell(1, 0, POO_BROWN)

    # Face: eyes (blinking on one expression) and a smile.
    for eye_x in (-4, 4):
        if expression == 1:
            row(11, eye_x - 1, eye_x + 1, POO_OUTLINE)
        else:
            row(10, eye_x - 1, eye_x + 1, POO_EYE)
            row(11, eye_x - 1, eye_x + 1, POO_EYE)
            cell(eye_x, 11, POO_OUTLINE)
    if expression in (2, 5):
        row(14, -3, 3, POO_OUTLINE)
        row(15, -2, 2, POO_OUTLINE)
    else:
        cell(-4, 14, POO_OUTLINE)
        row(15, -3, 3, POO_OUTLINE)
        cell(4, 14, POO_OUTLINE)


def weekday_monday_zero(year, month, day):
    offsets = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
    adjusted_year = year - (1 if month < 3 else 0)
    sunday_zero = (
        adjusted_year + adjusted_year // 4 - adjusted_year // 100
        + adjusted_year // 400 + offsets[month - 1] + day
    ) % 7
    return (sunday_zero - 1) % 7


def set_start_time(rtc):
    year, month, day, hour, minute, second = START_DATETIME_UTC
    weekday = weekday_monday_zero(year, month, day)
    rtc.datetime((year, month, day, weekday, hour, minute, second, 0))


def draw_clock(display, rtc, expression):
    hour, minute, second = rtc.datetime()[4:7]
    display.fill(BLACK)
    draw_time(display, hour, minute, second)
    draw_pumpkin(display, expression)
    display.show()


def main():
    display = PicoLCD18()
    rtc = RTC()
    set_start_time(rtc)
    next_expression = ticks_ms()
    expression = 0
    while True:
        now = ticks_ms()
        if ticks_diff(now, next_expression) >= 0:
            expression = (expression + 1) % EXPRESSION_COUNT
            next_expression = ticks_add(now, EXPRESSION_INTERVAL_MS)
        draw_clock(display, rtc, expression)
        sleep(1)


if __name__ == "__main__":
    main()
