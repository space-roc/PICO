# Tutorial 2: Read the onboard temperature sensor
#
# The Pico's chip has a temperature sensor built in. We read it every two
# seconds, convert the reading to degrees Celsius, and print it.

# ADC = Analog to Digital Converter. It turns a voltage into a number.
from machine import ADC
from time import sleep

# ADC channel 4 is connected to the chip's internal temperature sensor.
# (Channels 0-3 are the external pins GP26-GP29 on the Pico.)
sensor = ADC(4)

# read_u16() returns a number from 0 to 65535, which represents 0 V to 3.3 V.
# Multiplying by this value converts that number into volts.
CONVERSION = 3.3 / 65535

while True:
    # Read the raw sensor value (0-65535) and convert it to volts.
    voltage = sensor.read_u16() * CONVERSION

    # The chip datasheet says the sensor outputs 0.706 V at 27 degrees C and
    # the voltage falls by 0.001721 V for every extra degree. Rearranging
    # that gives the temperature from the voltage.
    celsius = 27 - (voltage - 0.706) / 0.001721

    # "{:.1f}" means: show the number with 1 decimal place.
    print("Temperature: {:.1f} C".format(celsius))

    # Wait 2 seconds before the next reading.
    sleep(2)
