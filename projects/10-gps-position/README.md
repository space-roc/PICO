# Project 10: Simple GPS latitude and longitude

Print latitude and longitude from the
[Waveshare Pico-GPS-L76B](https://www.waveshare.com/wiki/Pico-GPS-L76B) module
plugged onto the Pico. This is a shorter version of
[project 1](../01-gps-l76b/README.md), which also reports time, speed and
altitude.

## Hardware

- A Pico with the Pico-GPS-L76B plugged on, USB logos facing the same way
- The module's antenna side facing the sky, outdoors or by a window
- The module's default connection: **UART0, GP0 (Pico TX) and GP1 (Pico RX) at
  9600 baud**

## Run it

From the repository root in PowerShell:

```powershell
python -m mpremote connect auto run projects\10-gps-position\main.py
```

Or upload it so it runs at power-up:

```powershell
python -m mpremote connect auto fs cp projects\10-gps-position\main.py :main.py + reset
```

Until the module has a fix you'll see `No position fix yet...`. A cold start
can take 30 seconds or more, and indoors it usually won't get a fix. After
that, every 2 seconds:

```
Latitude: 22.541137  Longitude: 114.077913  Satellites: 12
```

Positive latitude is north and positive longitude is east. Paste
`latitude,longitude` into Google Maps to see the position.

## How it works

- The module sends NMEA text lines such as `$GNGGA,...*hh` once a second.
- Lines are checked against their checksum so corrupted ones are ignored.
- Only the **GGA** sentence is used. It holds the position (as degrees and
  minutes), the fix quality and the number of satellites.
- `to_degrees()` converts `2232.4682,N` (22 degrees 32.4682 minutes) into
  decimal degrees, negative for south and west.

## Troubleshooting

- **No data from the module:** check the module is plugged on the right way
  round. If you've re-soldered the module for UART1, change `UART_ID`,
  `TX_PIN` and `RX_PIN` (GP4/GP5).
- **Always "No position fix yet":** go outdoors with a clear view of the sky.
