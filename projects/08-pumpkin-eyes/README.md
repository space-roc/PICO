# 08 - Pumpkin eyes

Two SSD1306 128x64 OLEDs show a pair of animated eyes with eyebrows, for use inside a carved pumpkin. The eyes blink, look left/right/up/down, squint, and switch between expressions at random: happy, angry, evil, sad, surprised, sleepy, suspicious, wink and cross-eyed.

## Wiring (same as project 05)

| Display | SDA | SCL | Bus |
| --- | --- | --- | --- |
| 1 | GP8 | GP9 | hardware I2C0 |
| 2 | GP12 | GP13 | SoftI2C |

Both displays: VCC to 3V3, GND to GND.

## Upload

```powershell
python -m mpremote connect auto fs cp projects\08-pumpkin-eyes\ssd1306.py :ssd1306.py
python -m mpremote connect auto fs cp projects\08-pumpkin-eyes\main.py :main.py + reset
```

## Tuning

Edit the constants at the top of `main.py`:

- `LEFT_EYE_INNER` / `RIGHT_EYE_INNER`: set to `1` or `-1` if an eyebrow slants the wrong way, which depends on how each display is mounted.
- `EYE_*`, `PUPIL_RADIUS`, `BROW_*`: eye and brow size and position.
- `FRAME_MS`, `SMOOTHING`: animation speed and smoothness.
- `EXPRESSIONS`: add or edit expressions.
