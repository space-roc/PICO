# Minimal SSD1306 OLED driver (I2C only) for MicroPython.
#
# Upload this file to the Pico alongside main.py. It draws into a framebuffer
# in memory (text, lines, rectangles...) and show() sends it to the screen.

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
            # 0x80 means "one command byte follows".
            self.i2c.writeto(self.addr, bytes((0x80, c)))

    def _init_display(self):
        self._cmd(
            0xAE,                # display off
            0x20, 0x00,          # horizontal addressing mode
            0x40,                # start line 0
            0xA1,                # column 127 maps to SEG0 (not mirrored)
            0xA8, self.height - 1,
            0xC8,                # scan COM output from the bottom (not flipped)
            0xD3, 0x00,          # no display offset
            0xDA, 0x02 if self.width > 2 * self.height else 0x12,
            0xD5, 0x80,          # clock divide / oscillator
            0xD9, 0xF1,          # pre-charge
            0xDB, 0x30,          # VCOM deselect level
            0x81, 0xFF,          # maximum contrast
            0xA4,                # follow RAM contents
            0xA6,                # normal (not inverted)
            0x8D, 0x14,          # enable the internal charge pump
            0xAF,                # display on
        )
        self.fill(0)
        self.show()

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # 64-pixel-wide panels are centred in the 128-column memory.
            x0 += 32
            x1 += 32
        self._cmd(0x21, x0, x1, 0x22, 0, self.pages - 1)
        # 0x40 means "display data follows".
        self.i2c.writevto(self.addr, (b"\x40", self.buffer))

    def poweroff(self):
        self._cmd(0xAE)

    def poweron(self):
        self._cmd(0xAF)

    def contrast(self, value):
        self._cmd(0x81, value)

    def invert(self, on):
        self._cmd(0xA7 if on else 0xA6)
