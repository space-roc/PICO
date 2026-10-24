# Projects

Standalone projects using extra hardware. Most are MicroPython projects for
the Pico; project 13 targets the Waveshare ESP32-S3.

| # | Project |
|---|---------|
| 1 | [Waveshare Pico-GPS-L76B GPS module](01-gps-l76b/README.md) |
| 2 | [Random dice](02-dice/README.md) |
| 3 | [OLED temperature display](03-oled-temperature/README.md) |
| 4 | [Scrolling message](04-message/README.md) |
| 5 | [Two random cat faces](05-cat-faces/README.md) |
| 5b | [Cat faces with a cats/poos button](05b-cat-faces/README.md) |
| 6 | [UTC clock on the Waveshare Pico-LCD-1.8](06-utc-clock/README.md) |
| 7 | [Pumpkin clock on the Waveshare Pico-LCD-1.8](07-cat-clock/README.md) |
| 8 | [Pumpkin eyes on two OLED displays](08-pumpkin-eyes/README.md) |
| 9 | [Two 3D dice](09-3d-dice/README.md) |
| 10 | [Simple GPS latitude and longitude](10-gps-position/README.md) |
| 11 | [Live GPS map in the browser](11-gps-map/README.md) |
| 11b | [GPS latitude and longitude on two OLEDs](11b-gps-oled/README.md) |
| 12 | [MLX90640 thermal camera viewer](12-thermal-camera/README.md) |
| 13 | [Clock on the Waveshare ESP32-S3 round display](13-esp32-s3-access/README.md) |
| 13b | [Stand-alone thermal camera on the Waveshare Pico-LCD-1.8](13b-thermal-lcd/README.md) |
| 14 | [Pumpkin eyes on round LCDs (Pico 2 W)](14-pumpkin-eyes-lcd/README.md) |
| 14b | [Pumpkin eyes that jiggle when shaken (accelerometer)](14b-pumpkin-eyes-shake/README.md) |

For a MicroPython project, open its `main.py` and use the VS Code tasks **Run
current file on Pico (no save)** or **Upload current file to Pico as main.py**.
Setup is in the [main README](../README.md). Project 13 uses Arduino on the
ESP32-S3; its README has separate build and upload instructions.
