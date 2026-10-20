# Project 5: Two random cat faces

Show a cat on each of two SSD1306 OLEDs. Each cat independently changes
expression, gaze, whisker pose, and head direction at a random interval.
Occasionally, "MEOW" appears in the yellow top band; sleeping cats show
floating Zs there.

## Hardware

- Two SSD1306 I2C OLED displays, 128x64
- Both OLEDs: VCC to 3.3 V and GND to GND
- Display 1: SDA to **GP8**, SCL to **GP9** (hardware I2C0)
- Display 2: SDA to **GP12**, SCL to **GP13** (software I2C)

The displays may have the same I2C address (usually `0x3C`) because they are
connected to separate buses. This project uses a software I2C bus for the
second display, as GP8/GP9 and GP12/GP13 are both I2C0 pin pairs.

## Upload and run

From the repository root in PowerShell, upload the driver and then the program:

```powershell
python -m mpremote connect auto fs cp projects\05-cat-faces\ssd1306.py :ssd1306.py
python -m mpremote connect auto fs cp projects\05-cat-faces\main.py :main.py
python -m mpremote connect auto reset
```

The Pico will start the cats program after resetting, and again when powered
on. Alternatively, open this project's `main.py` in VS Code and use
**Run current file on Pico (no save)** or **Upload current file to Pico as
main.py**.

## How it works

- Each display gets its own `Cat` object and independently selected face.
- The 30 variations combine wide-eyed, angry, or happy expressions with a
  left, center, or right gaze and level, perked, or drooping whiskers (27
  combinations), plus three sleeping faces with different whisker poses.
- The head can face left, center, or right. Turns use a horizontally
  asymmetric face projection to suggest the cat looking to one side.
- "MEOW" is independently selected with a one-in-five chance on each face
  update. It appears at the top of the display, in the yellow band on
  two-colour OLEDs. Sleeping faces show three Zs in that band.
- The cats pick a different expression/gaze/whisker variation every 1 to 3
  seconds.
- The graphics are drawn directly into the SSD1306 framebuffer; no image files
  or extra libraries are required.

## Troubleshooting

- **No I2C device found:** check the SDA/SCL pins for both displays and ensure
  that each has 3.3 V and GND.
- **The first cat works but the second doesn't:** check the GP12/GP13 wiring.
- **`ImportError: no module named ssd1306`:** upload `ssd1306.py` using the
  first command above.
