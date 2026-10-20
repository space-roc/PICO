# Minimal SSD1306 OLED driver (I2C only) for MicroPython.
# This is the same small framebuffer driver used by Projects 4 and 5.

import framebuf


class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self._init_display()

    def _cmd(self, *cmds):
        for c in cmds:
            self.i2c.writeto(self.addr, bytes((0x80, c)))

    def _init_display(self):
        self._cmd(
            0xAE,
            0x20, 0x00,
            0x40,
            0xA1,
            0xA8, self.height - 1,
            0xC8,
            0xD3, 0x00,
            0xDA, 0x02 if self.width > 2 * self.height else 0x12,
            0xD5, 0x80,
            0xD9, 0xF1,
            0xDB, 0x30,
            0x81, 0xFF,
            0xA4,
            0xA6,
            0x8D, 0x14,
            0xAF,
        )
        self.fill(0)
        self.show()

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        self._cmd(0x21, x0, x1, 0x22, 0, self.pages - 1)
        self.i2c.writevto(self.addr, (b"\x40", self.buffer))

    def poweroff(self):
        self._cmd(0xAE)

    def poweron(self):
        self._cmd(0xAF)

    def contrast(self, value):
        self._cmd(0x81, value)

    def invert(self, on):
        self._cmd(0xA7 if on else 0xA6)
