# Project 6: UTC clock on the Waveshare Pico-LCD-1.8

Show the UTC time and date on the 1.8-inch colour LCD that plugs onto the
Raspberry Pi Pico. The clock uses the Pico's built-in RTC and does not need an
extra display driver file. Its pin mapping and panel setup follow the
[Waveshare Pico-LCD-1.8 documentation](https://www.waveshare.com/wiki/Pico-LCD-1.8).

## Hardware

- Raspberry Pi Pico or Pico H running MicroPython
- Waveshare Pico-LCD-1.8, fitted in the direction shown by the USB markings

The LCD uses SPI and the board's built-in connections:

| LCD signal | Pico pin |
|---|---|
| VCC | VSYS |
| GND | GND |
| DIN | GP11 |
| CLK | GP10 |
| CS | GP9 |
| DC | GP8 |
| RST | GP12 |
| BL | GP13 |

## Set the time and run

1. Open [main.py](main.py) and edit `START_DATETIME_UTC` near the top. Use
   `(year, month, day, hour, minute, second)` in 24-hour UTC, for example
   `(2026, 10, 16, 16, 10, 0)`.
2. Connect the Pico over USB and use **Run current file on Pico (no save)** to
   try the clock.
3. Use **Upload current file to Pico as main.py** to make it start whenever
   the Pico powers on.

The time in `START_DATETIME_UTC` is applied each time the program starts. A
standard Pico has no battery-backed clock, so update this value and upload
again after the Pico has been disconnected from power. The clock runs in UTC
and does not apply daylight-saving changes.

## Troubleshooting

- Make sure the board is fitted the right way round: the USB markings on the
  Pico and LCD should be at the same end.
- If the screen stays dark, check that the display is seated firmly and that
  the Pico is running MicroPython.
