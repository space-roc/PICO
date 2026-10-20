# Project 4: Scrolling message on a two-colour OLED
#
# Two-colour SSD1306 OLEDs have a yellow strip across the top 16 pixel rows and
# a blue area below it. This script shows a fixed message in the yellow strip
# and a scrolling message in the blue area.
#
# Wiring: OLED VCC -> 3.3 V, GND -> GND, SDA -> GP8, SCL -> GP9
# Upload ssd1306.py to the Pico as well as this file.

from machine import I2C, Pin
from time import sleep_ms

from ssd1306 import SSD1306_I2C

# Edit these two messages.
YELLOW_MESSAGE = "HELLO BUBBLES!"  # fixed; up to 16 characters fit on the screen
BLUE_MESSAGE = "I love you xxxx"

I2C_ID = 0
SDA_PIN = 8
SCL_PIN = 9

WIDTH = 128
HEIGHT = 64

# The yellow strip is the top 16 rows; the blue area is the rest.
YELLOW_HEIGHT = 16
CHAR_SIZE = 8

# Scroll speed: pixels moved per frame and delay between frames.
SCROLL_STEP = 2
FRAME_MS = 30


def setup_display():
    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found: check the OLED wiring (SDA=GP8, SCL=GP9)")
    address = 0x3C if 0x3C in devices else devices[0]
    return SSD1306_I2C(WIDTH, HEIGHT, i2c, address)


def draw(oled, x):
    oled.fill(0)

    # Yellow strip: centred, vertically in the middle of the top 16 rows.
    text = YELLOW_MESSAGE[:WIDTH // CHAR_SIZE]
    yellow_x = (WIDTH - len(text) * CHAR_SIZE) // 2
    oled.text(text, yellow_x, (YELLOW_HEIGHT - CHAR_SIZE) // 2)

    # Blue area: scrolling text, vertically centred below the strip.
    blue_y = YELLOW_HEIGHT + (HEIGHT - YELLOW_HEIGHT - CHAR_SIZE) // 2
    oled.text(BLUE_MESSAGE, x, blue_y)
    oled.show()


oled = setup_display()

message_width = len(BLUE_MESSAGE) * CHAR_SIZE
x = WIDTH  # start just off the right edge

while True:
    draw(oled, x)
    x -= SCROLL_STEP
    if x < -message_width:
        x = WIDTH
    sleep_ms(FRAME_MS)
