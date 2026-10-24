# Project 14: Pumpkin Eyes on Round LCDs

A pair of cute, animated pumpkin eyes on the Waveshare 0.71" Dual Eye round LCD, driven by a Pico 2 W. They blink, look around and pull faces (angry, happy, sad, wink, cross-eyed and more). It's the colour, round-screen version of project 8.

This was written without the hardware to hand, so check the first start-up as described below.

## Hardware

- Raspberry Pi Pico 2 W (a Pico or Pico 2 also works, but only the W has Wi-Fi for the clock)
- [Waveshare 0.71" Dual Eye LCD module](https://www.waveshare.com/wiki/0.71inch_DualEye_LCD_Module) (two round 160x160 GC9D01 screens, sold by The Pi Hut)

## Wiring

Both screens share the clock, data and DC lines. Each has its own CS, RST and backlight pin. Match the labels printed on the module, as the order on the connector may differ from this table.

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

## Upload

```powershell
python -m mpremote connect auto fs cp projects\14-pumpkin-eyes-lcd\gc9d01.py :gc9d01.py
python -m mpremote connect auto fs cp projects\14-pumpkin-eyes-lcd\wifi_time.py :wifi_time.py
python -m mpremote connect auto fs cp projects\14-pumpkin-eyes-lcd\wifi_config.py :wifi_config.py
python -m mpremote connect auto fs cp projects\14-pumpkin-eyes-lcd\main.py :main.py + reset
```

The Wi-Fi files are only needed for the clock (see below). Without `wifi_config.py` the eyes run on their own.

## Clock (Wi-Fi)

When it starts, both screens show "WI-FI ..." while the Pico joins the network and sets its clock from the internet (NTP). Then they show "WI-FI OK" for two seconds (or "NO WI-FI" if it failed), followed by the time (left screen) and date (right screen) for three seconds, and the eyes begin. After that, every 30 seconds the eyes blink shut and the time and date show for three seconds before the eyes open again.

1. Make sure the Pico runs the **Pico 2 W** MicroPython firmware (from the [MicroPython downloads page](https://micropython.org/download/RPI_PICO2_W/)). The plain Pico 2 build has no Wi-Fi. If `import network` works in the REPL, you're fine.
2. Copy `wifi_config_example.py` to `wifi_config.py` and put your Wi-Fi name and password in it. Git ignores that file, so the password isn't committed. The Pico only joins 2.4 GHz networks.
3. Upload as above.

The Pico switches Wi-Fi off after setting the clock, and re-syncs every 6 hours (every 10 minutes until the first success). The pop-ups only start once the time has been set. If Wi-Fi fails, the eyes carry on as normal and it tries again later.

The time is UTC plus `UTC_OFFSET_HOURS`. `UK_DAYLIGHT_SAVING = True` adds the extra hour from the last Sunday of March to the last Sunday of October. Outside the UK, set it to `False` and use `UTC_OFFSET_HOURS`.

## First start-up

For three seconds each screen shows a test picture: a white border, red, green and blue bars, "SCREEN 1" or "SCREEN 2", and an arrow with "TOP" above it. Check that:

- the arrow points up on both screens;
- the bars are red, green, blue from left to right.

Then the eyes start. Fix anything wrong in the settings at the top of `main.py`.

## Settings

| Setting | Meaning |
|---------|---------|
| `ROTATION` | Rotation (0 to 3) for each screen. Change a screen's number if its picture is upside down or sideways |
| `RED_BLUE_SWAPPED` | Set to `True` if red and blue are the wrong way round |
| `INNER` | Which side of each screen faces the nose. Swap the two values if the eyes look cross-eyed or the angry brows slope outwards |
| `BRIGHTNESS` | Backlight level, 0 to 1 |
| `SPI_BAUDRATE` | Lower to `20_000_000` if the picture has glitches |
| `STARTUP_TEST_MS` | Test screen time; `0` skips it |
| `MIN/MAX_EXPRESSION_MS`, `MIN/MAX_BLINK_MS` | How often the face changes and blinks |
| `EXPRESSIONS` | Add or edit expressions |
| `SLEEP_CHANCE` | Chance (0 to 1) that the next expression is a sleep; `0` turns sleeping off |
| `SLEEP_MS` | How long a sleep lasts (default 30000, i.e. 30 seconds) |
| `Z_CYCLE_MS` | How long each Z takes to float up the screen |
| `SHOW_CLOCK` | Turn the time/date pop-ups on or off |
| `CLOCK_INTERVAL_S` | Seconds of eyes between time/date pop-ups (default 30) |
| `CLOCK_SHOW_MS` | How long the time and date stay up (default 3000) |
| `WIFI_MESSAGE_MS` | How long "WI-FI OK" shows at start-up |
| `UTC_OFFSET_HOURS`, `UK_DAYLIGHT_SAVING` | Your time zone |
| `SYNC_INTERVAL_MIN`, `SYNC_RETRY_MIN` | How often to re-check the time over Wi-Fi |

## How it works

- `gc9d01.py` is a small driver. It sends Waveshare's start-up commands to both screens, then writes whole 160x160 pictures over SPI.
- `main.py` draws each eye into one shared RGB565 buffer, column by column: the yellow eye shape, then the orange iris and pupil clipped to the eyelids, then the sparkles and eyebrow. The buffer is sent to one screen and then redrawn for the other.
- Expressions are sets of targets (look direction, eyelid slant, eyebrow position, pupil size and so on). Each eye eases towards its targets, and a random expression and blink are chosen on timers.

## Troubleshooting

- **Blank screens:** check VCC, GND and the BL wires. The backlight only turns on if BL1 and BL2 are wired to GP9 and GP10.
- **One screen blank:** check that screen's CS, RST and BL wires.
- **White or garbled picture:** check DIN and CLK, and try a lower `SPI_BAUDRATE`.
- **Orange looks blue:** set `RED_BLUE_SWAPPED = True`.
- **Picture is rotated or mirrored:** change `ROTATION` for that screen.
- **No clock appears:** run `python -m mpremote run projects\14-pumpkin-eyes-lcd\main.py` to see messages. "Could not connect" means a wrong name or password, or a 5 GHz-only network. `ImportError: no module named network` means the firmware isn't the Pico W build. The clock only appears after the time has been set.
- **Clock is an hour out:** check `UK_DAYLIGHT_SAVING` and `UTC_OFFSET_HOURS`.
