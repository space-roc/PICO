# Project 5b: Two cat faces, with a button to swap cats and poos

Show a cat on each of two SSD1306 OLEDs. Each cat independently changes
expression, gaze, whisker pose, and head direction at a random interval.
Occasionally, "Meooowww!" appears in the yellow top band; sleeping cats show
floating Zs there. A push button switches both displays between cats and
poos.

## Hardware

- A Raspberry Pi Pico
- Two SSD1306 I2C OLED displays, 128x64
- One push button

| Part | Pin on the part | Connects to |
|------|-----------------|-------------|
| Both OLEDs | VCC | 3.3 V |
| Both OLEDs | GND | GND |
| OLED 1 | SDA | **GP8** (physical pin 11) |
| OLED 1 | SCL | **GP9** (physical pin 12) |
| OLED 2 | SDA | **GP12** (physical pin 16) |
| OLED 2 | SCL | **GP13** (physical pin 17) |
| Push button | one leg | **GP15** (physical pin 20) |
| Push button | other leg | GND (for example physical pin 18) |

- OLED 1 uses hardware I2C0 and OLED 2 uses software I2C. The displays may have
  the same I2C address (usually `0x3C`) because they are on separate buses.
  GP8/GP9 and GP12/GP13 are both I2C0 pin pairs, so the second display can't
  also use hardware I2C0.
- The button needs no resistor. The code turns on the Pico's internal pull-up
  (`Pin(15, Pin.IN, Pin.PULL_UP)`), so the pin reads 0 while it's pressed.
- To use a different button pin, change `BUTTON_PIN` in `main.py`. Avoid GP8,
  GP9, GP12 and GP13.

## Upload and run

From the repository root in PowerShell, upload the driver and then the program:

```powershell
python -m mpremote connect auto fs cp projects\05b-cat-faces\ssd1306.py :ssd1306.py
python -m mpremote connect auto fs cp projects\05b-cat-faces\main.py :main.py
python -m mpremote connect auto reset
```

The Pico will start the program after resetting, and again when powered on.
Alternatively, open this project's `main.py` in VS Code and use **Run current
file on Pico (no save)** or **Upload current file to Pico as main.py**.

## How it works

- Each display gets its own `Cat` object and independently selected face.
- The 30 variations combine wide-eyed, angry, or happy expressions with a
  left, center, or right gaze and level, perked, or drooping whiskers (27
  combinations), plus three sleeping faces with different whisker poses.
- The head can face left, center, or right. Turns use a horizontally
  asymmetric face projection to suggest the cat looking to one side.
- "Meooowww!" is independently selected with a one-in-ten chance on each face
  update. It appears at the top of the display, in the yellow band on
  two-colour OLEDs. Sleeping faces show three Zs in that band.
- The cats pick a different expression/gaze/whisker variation every 1 to 3
  seconds.
- Each button press toggles between cats and poos on both displays and redraws
  them straight away. The poo has a swirled outline, stink lines instead of
  whiskers, and the label reads "Shit!". The program starts with cats.
- The graphics are drawn directly into the SSD1306 framebuffer; no image files
  or extra libraries are required.

## Troubleshooting

- **No I2C device found:** check the SDA/SCL pins for both displays and ensure
  that each has 3.3 V and GND.
- **The first cat works but the second doesn't:** check the GP12/GP13 wiring.
- **The button does nothing:** check the GP15 and GND connections, or change
  `BUTTON_PIN`.
- **`ImportError: no module named ssd1306`:** upload `ssd1306.py` using the
  first command above.
