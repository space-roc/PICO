# Project 12: MLX90640 thermal camera

Show a live thermal image from a
[Pimoroni MLX90640 thermal camera breakout](https://shop.pimoroni.com/products/mlx90640-thermal-camera-breakout?variant=12549161746515)
in a small window on your PC. The sensor has 32x24 pixels and measures
temperatures from -40 to 300 °C.

- `main.py` runs on the **Pico**. It reads the sensor over I2C and sends the raw
  data over USB.
- `viewer.py` runs on the **PC**. It calculates the temperatures and shows the
  picture, using `mlx90640.py` for the calculation.

The calculation is done on the PC because the sensor's calibration maths is
heavy for the Pico. `mlx90640.py` is a port of the
[Adafruit CircuitPython MLX90640 driver](https://github.com/adafruit/Adafruit_CircuitPython_MLX90640)
(MIT licence), with the I2C code removed.

## Hardware

- A Raspberry Pi Pico
- A Pimoroni MLX90640 breakout (the 110° or 55° version both work)

| Breakout pin | Qw/ST cable wire | Connects to |
|--------------|------------------|-------------|
| 3-5V | Red | 3.3 V (physical pin 36) |
| GND | Black | GND (for example physical pin 38) |
| SDA | Blue | **GP8** (physical pin 11) |
| SCL | Yellow | **GP9** (physical pin 12) |
| INT | | not used |

These are the same I2C pins as projects 3 and 4 (hardware I2C0). The sensor's
I2C address is `0x33`.

### Breadboard setup

With the Pico unplugged from USB, place it across the breadboard's centre
trench. Wire the four connections in the table above, then check them before
plugging in USB. Either use a Qw/ST cable in the breakout's Qw/ST socket, with
its bare wires going to the Pico pins (check the wire colours match the table),
or connect the breakout's own pins with jumper wires. Use one or the other, not
both. The sensor sits on the front of the breakout, so point that side at what
you want to see.

## Set up

1. Install the PC requirements. `pyserial` comes with `mpremote`; `tkinter`
   comes with the standard Windows Python.

   ```powershell
   python -m pip install pyserial
   ```

2. Upload `main.py` to the Pico so it runs on its own:

   ```powershell
   python -m mpremote connect auto fs cp projects\12-thermal-camera\main.py :main.py + reset
   ```

3. Close anything else using the Pico's serial port (Thonny, `mpremote`, the
   VS Code Pico tasks). Only one program can use it at a time.
4. Start the viewer from the repository root:

   ```powershell
   python projects\12-thermal-camera\viewer.py
   ```

   The picture should appear within a second or two. If the Pico's program has
   been stopped (for example after `mpremote run`), the viewer restarts it
   after about 4 seconds.

To see the window without a Pico or camera, add `--demo`.

## Using the viewer

The colours run from cold to hot over a fixed range, 15 to 40 °C by default, so
the same colour always means the same temperature. Anything outside the range
shows as the coldest or hottest colour. The colour bar to the right of the
picture is labelled every 5 °C, and the box under it shows the current minimum
and maximum temperatures in view, even when they are outside the range. The
crosshair shows the temperature at the centre of the picture.

| Key | Action |
|-----|--------|
| Space | Freeze or unfreeze the picture |
| M | Flip the picture left to right (it starts flipped) |
| C | Switch to the next colour palette |
| Esc or Q | Quit |

### Colour palettes

Press **C** to cycle through these, or choose the starting one with
`--palette`. The colour bar changes to match, and the current palette is shown
under the picture.

| Palette | Colours (cold to hot) | Good for |
|---------|-----------------------|----------|
| `inferno` (default) | black, purple, red, orange, pale yellow | all-round contrast |
| `iron` | black, purple, red, orange, yellow, white | the classic thermal-camera look |
| `rainbow` | blue, cyan, green, yellow, red | easy to read at a glance |
| `viridis` | purple, blue, green, yellow | colour-blind friendly |
| `coolwarm` | blue, white, red | above or below room temperature |
| `whitehot` | black to white | white is hot |
| `blackhot` | white to black | black is hot |

Options:

```powershell
python projects\12-thermal-camera\viewer.py --port COM4        # choose the port
python projects\12-thermal-camera\viewer.py --min 20 --max 35  # colour range in °C (default 15 to 40)
python projects\12-thermal-camera\viewer.py --palette iron     # starting palette
python projects\12-thermal-camera\viewer.py --scale 8          # smaller window
python projects\12-thermal-camera\viewer.py --no-mirror        # start unmirrored
python projects\12-thermal-camera\viewer.py --demo             # fake image, no Pico
```

## How it works

- The sensor reads each frame as two interleaved halves ("subpages"). `main.py`
  waits for each half, reads its 832 raw words over I2C and prints them as a hex
  text line (`FR:...`). The sensor's calibration EEPROM is sent as an `EE:...`
  line at start-up, whenever the viewer connects (it sends a byte to ask for
  it), and every 40 messages as a backup. The viewer can't show anything until
  it has this calibration data.
- The sensor runs at 4 Hz (8 messages a second). Change `REFRESH_RATE` in
  `main.py` for a different rate; faster rates may need a higher `I2C_FREQ` and
  are less reliable.
- `viewer.py` turns each half into temperatures, takes the surrounding sensor
  temperature into account, replaces any faulty pixels with the average of their
  neighbours, and smooths the 32x24 grid up to the window size.
- The sensor updates half its pixels (in a chessboard pattern) with each half
  frame, so moving objects can leave a checkerboard pattern. The viewer pulls
  each out-of-date pixel towards the average of its up-to-date neighbours, more
  strongly the more they disagree (`MOTION_FULL_C` in `viewer.py`, 1.5 °C by
  default). Still scenes keep their full detail. Raise it for more detail
  and more checkerboarding, or lower it for a smoother picture.
- Temperatures assume an emissivity of 0.95, which suits skin, wood, paper and
  most painted surfaces. Shiny metal and glass reflect heat from elsewhere and
  read wrongly.

## Troubleshooting

- **`MLX90640 not found at 0x33`:** check SDA/SCL (not swapped), 3.3 V and GND.
- **"No Pico found" or "Serial problem":** replug the Pico and close other
  programs using it.
- **"Waiting for the camera..." for more than a few seconds:** make sure this
  project's `main.py` is on the Pico. Unplug and replug it, or run the upload
  command again. To see any error from the Pico, run
  `python -m mpremote connect auto run projects\12-thermal-camera\main.py`
  with the viewer closed.
- **Checkerboard pattern on moving objects:** see `MOTION_FULL_C` above.
- **Everything is one colour:** the scene is outside the 15 to 40 °C range, so
  set `--min` and `--max` to suit it.
- **"Sensor error" messages:** usually a loose wire, or `I2C_FREQ` too high for
  your wiring. Try `100000`.
- **Picture is the wrong way round:** press M, or use `--no-mirror`.
- **Temperatures a few degrees out:** the sensor warms up when it first powers
  on; give it a minute or two.
