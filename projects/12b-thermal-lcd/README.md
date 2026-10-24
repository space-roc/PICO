# Project 13b: Stand-alone thermal camera on the Pico-LCD-1.8

A live thermal image from the
[Pimoroni MLX90640 breakout](https://shop.pimoroni.com/products/mlx90640-thermal-camera-breakout?variant=12549161746515)
on the [Waveshare Pico-LCD-1.8](https://www.waveshare.com/wiki/Pico-LCD-1.8),
all on **one Pico**. There is no PC involved once the files are uploaded, so
you can run it from a power bank.

This combines [project 12](../12-thermal-camera/README.md) (the camera, whose
calibration maths used to run on the PC) with [project 6](../06-utc-clock/README.md)
(the display). The Pico now does the sensor calculation itself.

## Hardware

- A Raspberry Pi Pico (a Pico 2 is faster, but not needed)
- Waveshare Pico-LCD-1.8, fitted in the direction shown by the USB markings
- Pimoroni MLX90640 breakout (the 110° or 55° version both work)

The LCD uses SPI1 and the pins below, which are the same as projects 6 and 7:

| LCD signal | Pico pin |
|------------|----------|
| VCC | VSYS |
| GND | GND |
| DIN | GP11 |
| CLK | GP10 |
| CS | GP9 |
| DC | GP8 |
| RST | GP12 |
| BL | GP13 |

The camera uses I2C0 on **GP4 and GP5**, not GP8 and GP9 as in project 12,
because the LCD uses GP8 and GP9.

| Breakout pin | Qw/ST cable wire | Connects to |
|--------------|------------------|-------------|
| 3-5V | Red | 3.3 V (physical pin 36) |
| GND | Black | GND (for example physical pin 38) |
| SDA | Blue | **GP4** (physical pin 6) |
| SCL | Yellow | **GP5** (physical pin 7) |
| INT | | not used |

The sensor's I2C address is `0x33`. Use either a Qw/ST cable or the
breakout's own pins, not both. The sensor is on the front of the breakout, so
point that side at what you want to see.

If you plug the LCD straight onto the Pico, the Pico's own pins are underneath
it. In that case wire the LCD to the Pico with jumper wires instead (the
Waveshare page also shows an expansion-board option), so GP4 and GP5 stay
reachable. Any other free I2C0 pair works too (GP0/GP1, GP16/GP17 or
GP20/GP21): change `SDA_PIN` and `SCL_PIN` at the top of `main.py`.

## Battery power

Once the files are uploaded, the Pico doesn't need a computer. The easiest
supply is a **USB power bank** in the Pico's micro-USB port. To use a bare
battery instead, connect it to **VSYS** (physical pin 39) and **GND** (for
example physical pin 38). VSYS accepts 1.8 to 5.5 V. The LCD's VCC is already
on VSYS, and the camera runs from the Pico's 3V3 output, so both are powered.

| Battery | Notes |
|---------|-------|
| 3 x AA or AAA (4.5 V) | Good choice. If you might also plug in USB, put a Schottky diode (for example 1N5817) in series on the + wire so the two supplies don't fight. |
| 2 x AA or AAA (3 V) | Works, but the picture may dim and the Pico may reset as the cells run down. |
| Single LiPo or Li-ion cell (3.7 V) | Use a charger and protection board (for example Pimoroni's Pico LiPo SHIM or an Adafruit PowerBoost) between the cell and VSYS. Don't wire a bare cell straight in. |

- Never go above 5.5 V on VSYS. Four AAs (6 V) are too many.
- Never connect a battery to 3V3 (OUT) or VBUS (physical pin 40).
- Check polarity first. VSYS has no reverse-polarity protection.
- Expect roughly 100 to 150 mA in total, so three AAs of about 2000 mAh should
  last around 10 hours. These figures are estimates, not measurements.

## Upload

Both files are needed on the Pico. From the repository root:

```powershell
python -m mpremote connect auto fs cp projects\13b-thermal-lcd\mlx_calc.py :mlx_calc.py
python -m mpremote connect auto fs cp projects\13b-thermal-lcd\main.py :main.py + reset
```

To try it first without saving, upload `mlx_calc.py` as above, then run
`python -m mpremote connect auto run projects\13b-thermal-lcd\main.py`. That
also prints any error and the time taken per picture. Close Thonny and other
programs using the Pico's serial port first.

## What you see

The picture is 160x120 on the 160x128 screen: each sensor pixel (the sensor is
32x24) is smoothed up to 5x5 screen pixels, as in project 12's viewer. A white
crosshair marks the centre. The line underneath shows the temperature at the
centre, then the hottest and coldest pixels in view:

```
C24.3 H31.2 L20.1
```

Colours run from cold to hot over a fixed range, 15 to 40 °C by default, so the
same colour always means the same temperature. Press **BOOTSEL** on the Pico to
switch to the next colour palette.

## Settings

Edit these at the top of `main.py` and upload again:

| Setting | Default | Meaning |
|---------|---------|---------|
| `MIN_C`, `MAX_C` | 15, 40 | Temperatures at the cold and hot ends of the colours |
| `AUTO_RANGE` | `False` | `True` stretches the colours over the coldest to hottest pixel in view (at least `AUTO_MIN_SPAN_C` = 10 °C wide). The colours then no longer mean fixed temperatures |
| `PALETTE` | `"inferno"` | Starting palette: `inferno`, `iron`, `rainbow`, `viridis`, `whitehot`, `blackhot` |
| `MIRROR` | `True` | Flip the picture left to right, like a mirror (as in project 12) |
| `REFRESH_RATE` | `2` | Sensor rate: 0 = 0.5 Hz, 1 = 1 Hz, 2 = 2 Hz, 3 = 4 Hz, 4 = 8 Hz |
| `SDA_PIN`, `SCL_PIN` | 4, 5 | The camera's I2C pins |

## How it works

- `mlx_calc.py` is project 12's calculation (a port of the Adafruit
  CircuitPython MLX90640 driver, MIT licence), reorganised to be quicker on the
  Pico. Everything that doesn't change between frames is worked out once at
  start-up, and the per-pixel numbers are stored as compact float arrays.
  Each message from the sensor is one half ("subpage") of a frame, so each
  picture updates half the pixels.
- The sensor updates its pixels in a chessboard pattern, so moving objects can
  leave a checkerboard. As in project 12, out-of-date pixels are pulled towards
  their up-to-date neighbours when they disagree strongly.
- The smoothing from 32x24 to 160x120 is done by two small `@micropython.viper`
  functions (integer maths on the buffer), because doing it in ordinary
  MicroPython would be far too slow. The temperatures are converted to a colour
  with a 256-entry palette and written straight into the LCD's frame buffer.
- Temperatures assume an emissivity of 0.95, which suits skin, wood, paper and
  most painted surfaces. Shiny metal and glass reflect heat from elsewhere and
  read wrongly.

## Speed

The Pico runs the calibration maths in MicroPython, so a picture takes a
fraction of a second rather than the 125 ms the sensor needs per half frame.
The program prints `NNN ms per picture` for each picture when run from a
computer. If the picture feels laggy or half of it looks out of date, set
`REFRESH_RATE` to `1` so the sensor doesn't send halves faster than the Pico
can use them. A Pico 2 is noticeably quicker.

## Troubleshooting

- **"MLX90640 not found" on the screen:** check SDA (GP4) and SCL (GP5) aren't
  swapped, and the 3.3 V and GND wires. The Pico retries every second.
- **"Sensor error" on the screen:** usually a loose wire, or `I2C_FREQ` too
  high for your wiring. Try `100000`.
- **`ImportError: no module named 'mlx_calc'`:** upload `mlx_calc.py` as well
  as `main.py`.
- **Screen stays dark:** make sure the LCD is the right way round and seated
  firmly, as in project 6.
- **The picture is a strip short at the top or bottom, or the text line is cut
  off:** this panel needs address offsets that the code copies from projects 6
  and 7. If your screen differs, adjust `IMAGE_HEIGHT`/`TEXT_Y` or the offsets
  in `PicoLCD18.show()`.
- **Picture is the wrong way round:** set `MIRROR` to `False`.
- **Everything is one colour:** the scene is outside the 15 to 40 °C range, so
  change `MIN_C` and `MAX_C`, or set `AUTO_RANGE = True`.
- **Temperatures a few degrees out:** the sensor warms up when it first powers
  on; give it a minute or two.
