# Project 13: Clock on the ESP32-S3 round display

Run a simple digital clock on the Waveshare ESP32-S3 Touch LCD 1.46
(412 × 412). This board is an ESP32-S3, not a Raspberry Pi Pico. The sketch
uses the board's QSPI LCD driver and synchronises time over Wi-Fi/NTP when
credentials are configured.

Uploading this sketch replaces the factory music/menu demo. You can restore
Waveshare's test firmware later from the
[official firmware repository](https://github.com/waveshareteam/ESP32-S3-Touch-LCD-1.46/tree/main/Firmware)
by flashing its `.bin` at address `0x00`.

## Configure Wi-Fi

Copy `wifi_secrets.example.h` to `wifi_secrets.h` in this folder and enter
your network's SSID and password in that local file. Do not share or commit
`wifi_secrets.h`; it is excluded by this folder's `.gitignore`.

The clock uses the UK timezone with automatic daylight-saving changes by
default. Change `CLOCK_TIMEZONE` in your private file if needed. If Wi-Fi is
not configured or NTP cannot be reached, the sketch starts from its firmware
build time, which is only an approximate fallback and resets to that time on
each restart.

## Build and upload

The build helper uses the official Waveshare display driver sources, Arduino
CLI, and Espressif's ESP32 Arduino core 3.1.1. It downloads the board driver
sources into a temporary build folder and leaves the repository free of
vendored driver code.

1. Connect the board by USB and find its COM port in Device Manager.
2. Close any serial monitor using the ESP32 port.
3. Configure Wi-Fi as described above.
4. From PowerShell in this folder, compile and upload (replace `COM5` if
   needed):

   ```powershell
   .\build.ps1 -Port COM5 -Upload
   ```

The board has 16 MB flash and 8 MB octal PSRAM. The helper selects those
settings for the ESP32-S3 and uploads only to the explicit port you provide.
After upload, the round display shows a 24-hour `HH:MM` clock. Serial status
messages are available at 115200 baud.

If you only want to check that the sketch compiles without writing to the
board, omit `-Upload`:

```powershell
.\build.ps1
```

## Hardware notes

- LCD: 412 × 412 QSPI panel, controller SPD2010.
- Touchscreen: capacitive I2C controller. Touch is not needed by this clock.
- The sketch initialises the board's I2C expander and backlight before starting
  the LCD.
- The framebuffer uses the board's octal PSRAM.
