# Project 1: Waveshare Pico-GPS-L76B

Read position, time, speed and satellite data from the
[Waveshare Pico-GPS-L76B](https://www.waveshare.com/wiki/Pico-GPS-L76B) GNSS
module (GPS, BeiDou and QZSS) and print it in the VS Code terminal.

## What you'll learn

- Serial communication with `UART`
- NMEA 0183 text sentences and their checksums
- Converting degrees-and-minutes coordinates into decimal degrees

## Hardware

- A Raspberry Pi Pico (or Pico W / Pico 2) with headers fitted
- The Pico-GPS-L76B module, plugged onto the Pico

Fitting it:

1. Plug the Pico into the module with the **USB logo on the module matching
   the direction of the Pico's USB connector**.
2. Put the antenna side (the side without a label) facing the sky and do not
   cover it.
3. For the first test, go outdoors or put the module by a window. Indoors it
   usually will not get a fix.

By default the module talks to the Pico on **UART0: GP0 (Pico TX) and GP1
(Pico RX) at 9600 baud**. These are the values in `main.py`. To use UART1
(GP4/GP5) the module's H1 and H2 pads must be re-soldered (see the
[schematic](https://files.waveshare.com/upload/7/75/Pico-GPS-L76B.pdf)); then
change `UART_ID`, `TX_PIN` and `RX_PIN` in `main.py`.

## Run it

1. Open [main.py](main.py) in VS Code.
2. Run **Tasks: Run Task → Run current file on Pico (no save)**.
3. Wait. A cold start usually takes 30 seconds or so in good conditions. While
   waiting you'll see "Waiting for a position fix".
4. Once there is a fix, each second prints something like:

   ```
   UTC: 23/08/2022 01:05:56
   Fix: GPS fix | Satellites in use: 12
   Latitude: 22.541137  Longitude: 114.077913
   Google Maps: 22.541137,114.077913
   Altitude: 45.3 m  HDOP: 0.9
   Speed: 1.9 km/h  Course: 125.29
   ```

5. Paste the "Google Maps" coordinates into the Google Maps search box to see
   your position.

To keep the program on the Pico so it runs at power-up, use **Upload current
file to Pico as main.py**.

## How the code works

- The module sends lines like `$GNRMC,010555.000,A,2232.4682,N,...*71`. This
  is the NMEA 0183 format.
- `checksum_ok()` verifies the two hex digits after `*` so corrupted lines are
  ignored.
- `handle_sentence()` reads two sentence types: **RMC** (time, date, position,
  speed, course) and **GGA** (fix quality, satellites, HDOP, altitude).
- `to_degrees()` converts `2232.4682,N` (22 degrees 32.4682 minutes) into
  decimal degrees.

The code is original and does not need Waveshare's `micropyGPS` library, so it
differs from their sample program. The parser was tested on a PC using the
sample sentence from the Waveshare wiki; it has not been run on the real module.

## Troubleshooting

- **"No data from the GPS module":** check the module is plugged in the right
  way round and that the UART pins match.
- **Stuck on "Waiting for a position fix":** move outdoors with a clear view of
  the sky and wait a few minutes. The battery holder (ML1220) keeps satellite
  data for faster hot starts if fitted.
- **Garbled output:** make sure the baud rate is 9600 (the module's default).
- **Connection error when uploading:** close anything else using the Pico's
  serial port.

## Try it yourself

- Print the position only when it changes by more than a few metres.
- Save readings to a file on the Pico to log a walk.
- Light an LED (Experiment 1) when there is a fix.
- Change the update rate to 10 Hz (see the PMTK commands in the module's
  documentation).
