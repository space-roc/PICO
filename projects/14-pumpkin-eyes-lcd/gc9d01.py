# Driver for the Waveshare 0.71" Dual Eye LCD module (two round 160x160 GC9D01
# screens on one SPI bus), for MicroPython on the Pico.
#
# Both screens share the clock, data and DC lines. Each has its own chip
# select (CS), reset (RST) and backlight (BL). The start-up commands are the
# ones in Waveshare's TFT_eSPI demo for this module.

from machine import PWM, Pin, SPI
from time import sleep_ms

SIZE = 160

# MADCTL (command 0x36) values for the four rotations, from the demo's driver.
ROTATIONS = (0x00, 0xF0, 0x50, 0x30)
BGR = 0x08 # Add this to a MADCTL value if red and blue are swapped

_SETUP = (
    (0xFE, b""),
    (0xEF, b""),
) + tuple((command, b"\xFF") for command in range(0x80, 0x90)) + (
    (0x3A, b"\x05"), # 16 bits per pixel (RGB565)
    (0xEC, b"\x01"),
    (0x74, b"\x02\x0E\x00\x00\x00\x00\x00"),
    (0x98, b"\x3E"),
    (0x99, b"\x3E"),
    (0xB5, b"\x0D\x0D"),
    (0x60, b"\x38\x0F\x79\x67"),
    (0x61, b"\x38\x11\x79\x67"),
    (0x64, b"\x38\x17\x71\x5F\x79\x67"),
    (0x65, b"\x38\x13\x71\x5B\x79\x67"),
    (0x6A, b"\x00\x00"),
    (0x6C, b"\x22\x02\x22\x02\x22\x22\x50"),
    (0x6E, b"\x03\x03\x01\x01\x00\x00\x0F\x0F\x0D\x0D\x0B\x0B\x09\x09\x00\x00"
           b"\x00\x00\x0A\x0A\x0C\x0C\x0E\x0E\x10\x10\x00\x00\x02\x02\x04\x04"),
    (0xBF, b"\x01"),
    (0xF9, b"\x40"),
    (0x9B, b"\x3B"),
    (0x93, b"\x33\x7F\x00"),
    (0x7E, b"\x30"),
    (0x70, b"\x0D\x02\x08\x0D\x02\x08"),
    (0x71, b"\x0D\x02\x08"),
    (0x91, b"\x0E\x09"),
    (0xC3, b"\x19"),
    (0xC4, b"\x19"),
    (0xC9, b"\x3C"),
    (0xF0, b"\x53\x15\x0A\x04\x00\x3E"),
    (0xF2, b"\x53\x15\x0A\x04\x00\x3A"),
    (0xF1, b"\x56\xA8\x7F\x33\x34\x5F"),
    (0xF3, b"\x52\xA4\x7F\x33\x34\xDF"),
    (0x36, b"\x00"),
)

_WINDOW = b"\x00\x00\x00" + bytes((SIZE - 1,))


class DualEye:
    def __init__(self, sck, mosi, dc, cs, rst, bl, madctl, baudrate=40_000_000,
                 brightness=1.0):
        """`cs`, `rst`, `bl` and `madctl` are lists with one entry per screen."""
        self.spi = SPI(0, baudrate=baudrate, polarity=0, phase=0,
                       sck=Pin(sck), mosi=Pin(mosi))
        self.dc = Pin(dc, Pin.OUT, value=1)
        self.cs = [Pin(pin, Pin.OUT, value=1) for pin in cs]
        self.rst = [Pin(pin, Pin.OUT, value=1) for pin in rst]
        self.backlights = [PWM(Pin(pin), freq=1000, duty_u16=0) for pin in bl]
        self.madctl = madctl
        self._initialize()
        self.set_brightness(brightness)

    def set_brightness(self, brightness):
        for backlight in self.backlights:
            backlight.duty_u16(int(max(0.0, min(1.0, brightness)) * 65535))

    def _command(self, command, data=b"", screens=None):
        # `screens` is a list of screen numbers, or None for both.
        selected = [self.cs[i] for i in (range(len(self.cs)) if screens is None else screens)]
        for cs in selected:
            cs(0)
        self.dc(0)
        self.spi.write(bytes((command,)))
        if data:
            self.dc(1)
            self.spi.write(data)
        for cs in selected:
            cs(1)

    def _initialize(self):
        for rst in self.rst:
            rst(1)
        sleep_ms(5)
        for rst in self.rst:
            rst(0)
        sleep_ms(20)
        for rst in self.rst:
            rst(1)
        sleep_ms(120)

        for command, data in _SETUP:
            self._command(command, data)
        self._command(0x11)
        sleep_ms(200)
        self._command(0x29)
        self._command(0x20) # Inversion off
        for screen, madctl in enumerate(self.madctl):
            self._command(0x36, bytes((madctl,)), (screen,))

    def show(self, screen, buffer):
        """Send a 160x160 RGB565 image (51200 bytes, high byte first) to one screen."""
        cs = self.cs[screen]
        self._command(0x2A, _WINDOW, (screen,))
        self._command(0x2B, _WINDOW, (screen,))
        cs(0)
        self.dc(0)
        self.spi.write(b"\x2C")
        self.dc(1)
        self.spi.write(buffer)
        cs(1)
