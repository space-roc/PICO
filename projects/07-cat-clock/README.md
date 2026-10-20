# Project 7: Pumpkin clock on the Waveshare Pico-LCD-1.8

Show a pixel-art jack-o'-lantern on the Waveshare Pico-LCD-1.8, with the UTC
time above it. The pumpkin is drawn directly into the display framebuffer in
orange, gold, and green, with a dark orange centre stripe and shading for a 3D
look. Its six carved expressions change every few seconds.

## Hardware

- Raspberry Pi Pico or Pico H running MicroPython
- Waveshare Pico-LCD-1.8, fitted in the direction shown by the USB markings

The LCD uses the Pico's built-in connections:

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
   `(year, month, day, hour, minute, second)` in 24-hour UTC.
2. Connect the Pico over USB and use **Run current file on Pico (no save)**
   to try the clock.
3. Use **Upload current file to Pico as main.py** to make it start whenever
   the Pico powers on. From the repository root, the equivalent PowerShell
   command is:

   ```powershell
   python -m mpremote connect auto fs cp projects\07-cat-clock\main.py :main.py + reset
   ```

The time is yellow. A standard Pico has no battery-backed clock, so update `START_DATETIME_UTC` and upload again after the Pico has been
disconnected from power.

## Troubleshooting

- Make sure the board is fitted the right way round: the USB markings on the
  Pico and LCD should be at the same end.
- If the screen stays dark, check that the display is seated firmly and that
  the Pico is running MicroPython.
