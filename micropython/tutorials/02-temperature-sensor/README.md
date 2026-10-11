# Tutorial 2: Read the onboard temperature sensor

Read the temperature sensor built into the Pico's chip and print it every two
seconds. No extra hardware is needed.

## What you'll learn

- Reading analog values with `ADC`
- Converting a raw reading into a voltage, then a temperature
- Formatting output with `str.format`

## Before you start

Complete [Tutorial 1](../01-blink-led/README.md) so MicroPython and `mpremote`
are working.

## The code

[main.py](main.py):

```python
from machine import ADC
from time import sleep

# Channel 4 is the RP2040/RP2350 internal temperature sensor.
sensor = ADC(4)
CONVERSION = 3.3 / 65535

while True:
    voltage = sensor.read_u16() * CONVERSION
    celsius = 27 - (voltage - 0.706) / 0.001721
    print("Temperature: {:.1f} C".format(celsius))
    sleep(2)
```

- `ADC(4)` selects the internal sensor. `read_u16()` returns 0-65535, which
  maps to 0-3.3 V.
- The formula comes from the RP2040 datasheet: 0.706 V at 27 °C, dropping
  about 1.721 mV per degree.
- The value reflects the chip's own temperature, so it reads a little higher
  than the room.

## Run it

1. Open `main.py` in VS Code.
2. Run **Tasks: Run Task → Run current file on Pico (no save)**. Temperatures
   print in the terminal. Stop with `Ctrl+C`.
3. To keep it on the board, run **Tasks: Run Task → Upload current file to Pico
   as main.py**.

## Try it yourself

- Convert to Fahrenheit: `celsius * 9 / 5 + 32`.
- Blink the LED (Tutorial 1) when the temperature exceeds a threshold.
- Warm the chip by pinching it gently and watch the value rise.

## Troubleshooting

- Values wildly off: the formula is calibrated for the RP2040. Pico 2
  (RP2350) readings can differ by a few degrees.
- Connection error: close any other program using the Pico's serial port.
