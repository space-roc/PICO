# Project 4 (variant): scrolling messages on two two-colour OLEDs
#
# Same layout as main.py, on two displays, each with its own messages.
#   Display 1: SDA -> GP8,  SCL -> GP9   (hardware I2C0)
#   Display 2: SDA -> GP12, SCL -> GP13  (software I2C)
# GP8/9 and GP12/13 are both I2C0 pins, and a bus can only use one pair at a
# time, so the second display uses SoftI2C, which works on any pins.
# Both displays can share the same I2C address (usually 0x3C) because they are
# on separate buses.
#
# Upload ssd1306.py to the Pico as well as this file.

from machine import I2C, Pin, SoftI2C
from time import sleep_ms

from ssd1306 import SSD1306_I2C

# Edit these messages. Yellow text is fixed (up to 16 characters).
YELLOW_1 = "HELLO BUBBLES!"  # fixed; up to 16 characters fit on the screen
BLUE_1   = "I love you xxxx"
YELLOW_2 = "HELLO BUBBLES!"  # fixed; up to 16 characters fit on the screen
BLUE_2   = "I love you xxxx"

WIDTH = 128
HEIGHT = 64
YELLOW_HEIGHT = 16
CHAR_SIZE = 8

SCROLL_STEP = 2
FRAME_MS = 30


def find_display(i2c, name):
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on " + name + ": check its wiring")
    address = 0x3C if 0x3C in devices else devices[0]
    return SSD1306_I2C(WIDTH, HEIGHT, i2c, address)


class Panel:
    def __init__(self, oled, yellow, blue):
        self.oled = oled
        self.yellow = yellow[:WIDTH // CHAR_SIZE]
        self.blue = blue
        self.width = len(blue) * CHAR_SIZE
        self.x = WIDTH

    def step(self):
        oled = self.oled
        oled.fill(0)
        yellow_x = (WIDTH - len(self.yellow) * CHAR_SIZE) // 2
        oled.text(self.yellow, yellow_x, (YELLOW_HEIGHT - CHAR_SIZE) // 2)
        blue_y = YELLOW_HEIGHT + (HEIGHT - YELLOW_HEIGHT - CHAR_SIZE) // 2
        oled.text(self.blue, self.x, blue_y)
        oled.show()

        self.x -= SCROLL_STEP
        if self.x < -self.width:
            self.x = WIDTH


i2c1 = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
i2c2 = SoftI2C(sda=Pin(12), scl=Pin(13), freq=400000)

panels = [
    Panel(find_display(i2c1, "display 1 (GP8/GP9)"), YELLOW_1, BLUE_1),
    Panel(find_display(i2c2, "display 2 (GP12/GP13)"), YELLOW_2, BLUE_2),
]

while True:
    for panel in panels:
        panel.step()
    sleep_ms(FRAME_MS)
