# Project 3: OLED temperature display

Show the Pico's built-in temperature sensor reading on an I2C OLED display.
Based on the [How2Electronics tutorial](https://how2electronics.com/read-temperature-sensor-value-from-raspberry-pi-pico/).

## What you'll learn

- Reading the internal temperature sensor with `ADC(4)`
- Converting a 16-bit reading to volts and then to degrees
- Talking to an I2C device and drawing text on an SSD1306 OLED

## Hardware

- An SSD1306 I2C OLED display (128x64 assumed)
- OLED VCC to 3.3 V, GND to GND, **SDA to GP8**, **SCL to GP9**

**Check before running:** if your screen is 128x32, change `HEIGHT` at the top
of `main.py`.

## Run it

1. Upload [ssd1306.py](ssd1306.py) to the Pico (`main.py` imports it). For
   example, run `python -m mpremote connect auto fs cp ssd1306.py :ssd1306.py`
   from this folder.
2. Open [main.py](main.py) and use **Run current file on Pico (no save)**, or
   **Upload current file to Pico as main.py** to run at power-up.
3. The OLED shows the temperature in C and F, updated every second, and the
   terminal prints the Celsius value.

## How it works

- At 27 C the sensor outputs 0.706 V, falling 1.721 mV per degree, so
  `27 - (volts - 0.706) / 0.001721` gives Celsius.
- `i2c.scan()` finds the display (normally address `0x3C`) and reports a clear
  error if nothing answers.
- `ssd1306.py` draws into a memory buffer; `oled.show()` sends it to the screen.

## Try it yourself

- Show the minimum and maximum temperature seen so far.
- Average several readings to smooth out the noise.
- Add a graph of the last 30 readings with `oled.line()`.

## Troubleshooting

- **"No I2C device found":** check SDA/SCL are on GP8/GP9 (not swapped) and the
  display has 3.3 V and GND.
- **Blank screen but the scan works:** the display may be 128x32; set `HEIGHT`.
- **`ImportError: no module named ssd1306`:** upload `ssd1306.py` to the Pico.
- **Reading is warmer than the room:** it is the chip's temperature, which
  rises with use. It is not an accurate air thermometer.
