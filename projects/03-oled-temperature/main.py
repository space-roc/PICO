# Project 3: OLED temperature display
#
# Reads the Pico's built-in temperature sensor (ADC channel 4) and shows the
# result in Celsius and Fahrenheit on an SSD1306 I2C OLED display.
#
# Wiring (as in the How2Electronics tutorial):
#   OLED VCC -> 3.3 V, OLED GND -> GND, OLED SDA -> GP8, OLED SCL -> GP9
#
# Upload ssd1306.py to the Pico as well as this file.
# NOTE: the sensor measures the chip's own temperature, which is usually a few
# degrees warmer than the air around it.

from machine import ADC, I2C, Pin
from time import sleep_ms

from ssd1306 import SSD1306_I2C

# GP8 and GP9 are the SDA and SCL pins of the Pico's I2C bus 0.
I2C_ID = 0
SDA_PIN = 8
SCL_PIN = 9

# Screen size in pixels; most small OLEDs are 128x64 (some are 128x32).
WIDTH = 128
HEIGHT = 64

# How often the reading is refreshed.
UPDATE_MS = 1000

# Channel 4 of the ADC is the internal temperature sensor.
sensor = ADC(4)
VOLTS_PER_COUNT = 3.3 / 65535


def read_celsius():
    # read_u16() returns 0-65535, which we convert to a voltage. The datasheet
    # says the sensor gives 0.706 V at 27 C and drops 1.721 mV per degree.
    volts = sensor.read_u16() * VOLTS_PER_COUNT
    return 27 - (volts - 0.706) / 0.001721


def setup_display():
    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found: check the OLED wiring (SDA=GP8, SCL=GP9)")
    print("I2C devices found:", [hex(d) for d in devices])
    # The display is normally at 0x3C, but some boards use 0x3D.
    address = 0x3C if 0x3C in devices else devices[0]
    return SSD1306_I2C(WIDTH, HEIGHT, i2c, address)


def show(oled, celsius):
    fahrenheit = celsius * 9 / 5 + 32
    oled.fill(0)
    oled.text("Pico temperature", 0, 0)
    oled.hline(0, 12, WIDTH, 1)
    oled.text("{:.1f} C".format(celsius), 0, 24)
    oled.text("{:.1f} F".format(fahrenheit), 0, 40)
    oled.show()


oled = setup_display()

while True:
    temperature = read_celsius()
    print("{:.1f} C".format(temperature))
    show(oled, temperature)
    sleep_ms(UPDATE_MS)
