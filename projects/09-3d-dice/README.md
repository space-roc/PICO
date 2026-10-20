# Project 9: Two 3D twelve-sided dice

Show a 3D twelve-sided die (a dodecahedron) on each of two SSD1306 OLEDs. Press
the button and both dice tumble in 3D, slow down, and land on a random value
(1 to 12). The rolled value is shown as `=N` in the top-left corner of each
display, and numbers are drawn on the faces turned towards you.

## Hardware

- Two SSD1306 I2C OLED displays, 128x64
- Both OLEDs: VCC to 3.3 V and GND to GND
- Display 1: SDA to **GP8**, SCL to **GP9** (hardware I2C0)
- Display 2: SDA to **GP12**, SCL to **GP13** (software I2C)
- Push button: one leg to **GP15**, the other to **GND** (no resistor needed;
  the internal pull-up is used)

## Upload and run

From the repository root in PowerShell:

```powershell
python -m mpremote connect auto fs cp projects\09-3d-dice\ssd1306.py :ssd1306.py
python -m mpremote connect auto fs cp projects\09-3d-dice\main.py :main.py
python -m mpremote connect auto reset
```

## How it works

- The die's 20 corners and 12 pentagon faces are built at start-up. Each face
  is found from the corners nearest its direction, and opposite faces add up to
  13.
- Orientations are 3x3 rotation matrices, projected onto the screen with simple
  perspective. Faces turned away from the viewer are skipped, and the numbers
  are drawn at the centre of faces that point towards you.
- A roll blends the die from its old orientation to the chosen face while two
  extra spins around random axes unwind to nothing. Whole turns are used, so
  the die always lands exactly on its chosen face.
- The second die settles a little after the first. Presses during a roll are
  ignored.

## Troubleshooting

- **No I2C device found:** check the SDA/SCL pins for both displays and ensure
  that each has 3.3 V and GND.
- **Nothing happens when pressing the button:** check the GP15 and GND
  connections, or change `BUTTON_PIN`.
- **The animation looks choppy:** the second display uses software I2C, which
  is slower than hardware I2C, and a 12-sided die has more lines to draw.
