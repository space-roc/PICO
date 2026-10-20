# Project 11b: GPS latitude and longitude on two OLEDs

A variant of [project 11](../11-gps-map/README.md). The Pico reads the
Pico-GPS-L76B module and shows the **latitude on one OLED and the longitude on
the other**, using the same two SSD1306 displays as
[project 5](../05-cat-faces/README.md). It still prints the same lines over USB,
so the live map from project 11 works with it too.

## Hardware

- A Raspberry Pi Pico with the Pico-GPS-L76B plugged on
- Two SSD1306 I2C OLED displays, 128x64 (the same ones as project 5)

### Breadboard setup

With the Pico unplugged from USB, plug the GPS module onto the Pico, matching
the USB logos. Place the Pico across the breadboard's centre trench so its pins
are accessible, then place the two OLEDs in separate rows. Use jumper wires to
connect each OLED to the Pico using the table below. Both displays share power
and ground; connect them to the Pico's 3.3 V output and GND, either directly or
through the breadboard power rails. Check whether the rails are split before
using them, and bridge the halves if needed.

| Part | Pin on the part | Connects to |
|------|-----------------|-------------|
| Both OLEDs | VCC | 3.3 V (physical pin 36) |
| Both OLEDs | GND | GND (for example physical pin 13 or 18) |
| OLED 1 (latitude) | SDA | **GP8** (physical pin 11) |
| OLED 1 (latitude) | SCL | **GP9** (physical pin 12) |
| OLED 2 (longitude) | SDA | **GP12** (physical pin 16) |
| OLED 2 (longitude) | SCL | **GP13** (physical pin 17) |

These are the same pins as project 5. The GPS module itself uses **GP0 and GP1**
(UART0) by default, so GP8/GP9 and GP12/GP13 don't clash with it.

Pins to avoid:

- **GP0, GP1:** the GPS module's serial connection.
- **GP4, GP5:** the GPS module's alternative serial port, if you ever re-solder
  its H1/H2 pads.
- **GP14:** the GPS module's power control, if you ever move its R3 resistor.

OLED 1 uses hardware I2C0 and OLED 2 uses software I2C, because GP8/GP9 and
GP12/GP13 are both I2C0 pin pairs. The displays may share the I2C address
(usually `0x3C`) since they're on separate buses.

## Upload and run

From the repository root in PowerShell:

```powershell
python -m mpremote connect auto fs cp projects\11b-gps-oled\ssd1306.py :ssd1306.py
python -m mpremote connect auto fs cp projects\11b-gps-oled\main.py :main.py
python -m mpremote connect auto reset
```

The program starts after the reset and again at power-up.

For the live map, run project 11's server on the PC, with nothing else using the
Pico's serial port:

```powershell
python projects\11-gps-map\map_server.py
```

## What the displays show

Each display has a title (`LATITUDE` or `LONGITUDE`), the value in large text,
the full six-decimal value with its hemisphere (N/S or E/W) underneath, and a
status line at the bottom:

- `Starting...` or `Waiting...` while the module starts up
- `Sats seen: 0` when it can't see any satellites (is the antenna facing the sky?)
- `View 8 Lock 2` while searching: satellites in view and satellites locked on
- `Sats 7 HDOP 1.2` once there's a fix
- `No GPS data` if the module isn't sending anything

The large number is trimmed to fit the screen, for example `51.48342`; the
small text always shows six decimals. Until there's a fix, the coordinate area
says `No fix yet`. The first fix can take 30 seconds or more, and needs the
antenna outdoors or by a window.

## Troubleshooting

- **`No I2C device found on ...`:** check that display's SDA/SCL pins, 3.3 V and
  GND.
- **`ImportError: no module named ssd1306`:** upload `ssd1306.py` using the
  first command above.
- **Both displays work but say `No GPS data`:** check the GPS module is plugged
  on the right way round (USB logos matching).
