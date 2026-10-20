from framebuf import FrameBuffer, RGB565
from machine import Pin, RTC, SPI
from time import sleep_ms, sleep

# Set the UTC time here before uploading. The Pico has no battery-backed clock.
START_DATETIME_UTC = (2026, 10, 16, 18, 52, 0)

SCREEN_WIDTH = 160
BUFFER_WIDTH = 161
BUFFER_HEIGHT = 130

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


def draw_digit(display, digit, x, y):
    width = 18
    height = 36
    thickness = 4
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
        display.fill_rect(*segments[segment], WHITE)


def draw_time(display, hour, minute, second):
    value = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
    x = (SCREEN_WIDTH - (6 * 18 + 2 * 4 + 7 * 3)) // 2
    y = 43
    for index, character in enumerate(value):
        if character == ":":
            display.fill_rect(x, y + 10, 4, 4, WHITE)
            display.fill_rect(x, y + 23, 4, 4, WHITE)
            x += 4
        else:
            draw_digit(display, character, x, y)
            x += 18
        if index < len(value) - 1:
            x += 3


def weekday_monday_zero(year, month, day):
    offsets = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
    adjusted_year = year - (1 if month < 3 else 0)
    sunday_zero = (
        adjusted_year
        + adjusted_year // 4
        - adjusted_year // 100
        + adjusted_year // 400
        + offsets[month - 1]
        + day
    ) % 7
    return (sunday_zero - 1) % 7


def set_start_time(rtc):
    year, month, day, hour, minute, second = START_DATETIME_UTC
    weekday = weekday_monday_zero(year, month, day)
    rtc.datetime((year, month, day, weekday, hour, minute, second, 0))


def draw_clock(display, rtc):
    year, month, day, weekday, hour, minute, second, _ = rtc.datetime()
    display.fill(BLACK)
    display.text("UTC CLOCK", 44, 13, WHITE)
    display.hline(16, 30, SCREEN_WIDTH - 32, WHITE)
    draw_time(display, hour, minute, second)

    weekdays = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
    months = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
    date_text = "{} {:02d} {} {}".format(
        weekdays[weekday], day, months[month - 1], year
    )
    display.text(date_text, (SCREEN_WIDTH - len(date_text) * 8) // 2, 94, WHITE)
    display.show()


def main():
    display = PicoLCD18()
    rtc = RTC()
    set_start_time(rtc)
    while True:
        draw_clock(display, rtc)
        sleep(1)


if __name__ == "__main__":
    main()
