# Project 14b: Pumpkin Eyes That Jiggle When Shaken

[Project 14](../14-pumpkin-eyes-lcd/README.md) plus an accelerometer. Shake the pumpkin harder than a threshold you choose and the eyes jiggle around, each one independently (looking in different directions, pupils, lids and brows all wobbling). When the shaking stops they calm down over about a second and a bit, then carry on with their normal expressions.

This was written without the hardware to hand, so check the first start-up as described below.

## Hardware

- Everything from project 14 (Pico 2 W, Waveshare 0.71" Dual Eye LCD)
- [DFRobot Gravity I2C LIS2DW12 accelerometer](https://thepihut.com/products/gravity-i2c-lis2dw12-triple-axis-accelerometer-sensor-2g-4g-8g-16g) (SEN0409)

## Wiring

The LCD wiring is the same as project 14:

| LCD pin | Pico pin | Physical pin |
|---------|----------|--------------|
| VCC | 3V3 (OUT) | 36 |
| GND | GND | 3 |
| DIN | GP3 | 5 |
| CLK | GP2 | 4 |
| CS1 | GP4 | 6 |
| CS2 | GP5 | 7 |
| DC | GP6 | 9 |
| RST1 | GP7 | 10 |
| RST2 | GP8 | 11 |
| BL1 | GP9 | 12 |
| BL2 | GP10 | 14 |

The accelerometer is new:

| Accelerometer pin | Pico pin | Physical pin |
|-------------------|----------|--------------|
| VCC | 3V3 (OUT) | 36 |
| GND | GND | 38 |
| SDA | GP0 | 1 |
| SCL | GP1 | 2 |

The Pico has only one 3V3 (OUT) pin, so the LCD and the accelerometer must share it (use a breadboard rail, or twist the two wires into the same pin). The accelerometer's INT pins aren't used.

## Upload

```powershell
python -m mpremote connect auto fs cp projects\14b-pumpkin-eyes-shake\gc9d01.py :gc9d01.py
python -m mpremote connect auto fs cp projects\14b-pumpkin-eyes-shake\accel.py :accel.py
python -m mpremote connect auto fs cp projects\14b-pumpkin-eyes-shake\main.py :main.py + reset
```

## First start-up

Follow the checks in project 14 (the test picture on each screen), then shake the board. If the accelerometer isn't found, a message is printed (use `python -m mpremote run projects\14b-pumpkin-eyes-shake\main.py` to see it) and the eyes carry on without shaking.

## Settings

The display settings (`ROTATION`, `INNER`, `RED_BLUE_SWAPPED` and so on) are the same as project 14. New ones at the top of `main.py`:

| Setting | Meaning |
|---------|---------|
| `SHAKE_THRESHOLD_G` | How hard you must shake, in g. Still is about 0, a gentle wave 0.3 to 0.5, a real shake 1 or more. Default `0.8` |
| `SHAKE_HOLD_MS` | Keep jiggling this long after the last strong shake |
| `RECOVER_MS` | How long the jiggle takes to fade away afterwards |
| `JIGGLE` | Overall jiggle strength (try `0.5` to `1.5`) |
| `JIGGLE_AMOUNTS` | How far each setting (look direction, cross-eye, pupil, lid, brow) swings |
| `ACCEL_ADDRESS` | `0x19` by default, or `0x18` if you flip the board's address switch |
| `SDA_PIN`, `SCL_PIN`, `I2C_ID` | I2C pins (GP0 and GP1 are I2C0) |

## How it works

- `accel.py` reads the LIS2DW12 at 100 Hz with a range of +/-8 g.
- Each frame the program compares the reading with a slowly-following estimate of gravity. The difference is the shake strength, so slowly tilting the pumpkin doesn't count, only sharp movement.
- A shake above the threshold sets the shake level to 1. After `SHAKE_HOLD_MS` of calm it falls steadily to 0 over `RECOVER_MS`.
- Each eye gives every setting its own random wobble, scaled by the shake level, so the eyes never move together and the jiggle shrinks smoothly as they recover.

## Troubleshooting

- **"Accelerometer not found":** check SDA, SCL, power and ground, and try `ACCEL_ADDRESS = 0x18`. `python -m mpremote exec "import machine; print(machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1)).scan())"` lists the addresses it can see.
- **Jiggles too easily or not enough:** change `SHAKE_THRESHOLD_G`.
- **Recovers too quickly or slowly:** change `RECOVER_MS`.
- For display problems see project 14.
