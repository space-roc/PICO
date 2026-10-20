# Raspberry Pi Pico workspace

A VS Code workspace for learning and developing on the Raspberry Pi Pico. It
contains four independent parts:

- `src/` is a C/C++ starter project using the Raspberry Pi Pico SDK.
- `micropython/tutorials/` has two beginner MicroPython tutorials.
- `experiments/` has ten MicroPython experiments modelled on the topics of the
  Kitronik Inventor's Kit for Pico.
- `projects/` has standalone projects for extra hardware, starting with the
  [Waveshare Pico-GPS-L76B GPS module](projects/01-gps-l76b/README.md).

## Getting started

1. Install the [prerequisites](#prerequisites) and flash MicroPython onto the
   Pico (once).
2. Work through the [tutorials](micropython/README.md). They need no extra
   hardware.
3. Build the circuits and try the [experiments](experiments/README.md).
4. Explore the C/C++ project when you want to try the Pico SDK.

Every `main.py` is heavily commented to explain what each line does.

```
PICO/
+-- CMakeLists.txt, CMakePresets.json   C/C++ build configuration
+-- src/                                C/C++ source
+-- micropython/
|   +-- README.md                       Tutorial index
|   +-- tutorials/
|       +-- 01-blink-led/               README.md + main.py
|       +-- 02-temperature-sensor/      README.md + main.py
+-- experiments/
|   +-- README.md                       Experiment index
|   +-- 01-... to 10-.../               README.md + main.py each
+-- projects/
|   +-- README.md                       Project index
|   +-- 01-gps-l76b/                    README.md + main.py
|   +-- 02-dice/                        README.md + main.py
+-- .vscode/                            Recommended extensions and tasks
```

The C project defaults to a Raspberry Pi Pico. It also includes CMake presets
for the Pico 2. Change the board preset if you are using a W or another board.

## Prerequisites

- Visual Studio Code and Git for Windows (Thonny is not required)
- For C/C++: CMake 3.21 or newer, Ninja, the Arm GNU Toolchain, and the
  Raspberry Pi Pico SDK
- For MicroPython: Python 3 and `mpremote`

Install the C/C++ tools and SDK using the
[official Pico VS Code setup guide](https://www.raspberrypi.com/news/raspberry-pi-pico-vscode-extension/).
Alternatively, install the tools separately, clone the
[Pico SDK](https://github.com/raspberrypi/pico-sdk) (including its submodules),
and set `PICO_SDK_PATH` to the SDK directory in your Windows user environment.
Restart VS Code after installing tools or changing environment variables.

Install the MicroPython upload tool:

```powershell
python -m pip install mpremote
```

Run it as `python -m mpremote ...` (the VS Code tasks do this). The bare
`mpremote` command only works if Python's `Scripts` folder is on your PATH,
which is often not the case with the Microsoft Store version of Python.

For MicroPython, download the UF2 firmware for your board from the
[MicroPython Raspberry Pi Pico downloads](https://micropython.org/download/).
Hold **BOOTSEL** while connecting the Pico over USB, then copy the downloaded
UF2 file to the `RPI-RP2` drive. The board will reboot with MicroPython.

## C/C++ with the Pico SDK

Open this folder in VS Code. Choose **CMake: Select Configure Preset** and
select `pico` (or `pico2`), then configure and build with the CMake Tools
extension. The presets use Ninja and place generated files under `build/`.

The initial program prints a message once per second over USB serial. Connect
to the Pico's USB serial port with a terminal at 115200 baud to see it.

To build from PowerShell instead of VS Code:

```powershell
cmake --preset pico
cmake --build --preset pico
```

For a Pico 2, use `pico2` in both commands. For other boards, select an
appropriate board in `CMakePresets.json`.

## MicroPython

### Tutorials

Follow the tutorials in [micropython/](micropython/README.md):

1. [Blink the onboard LED](micropython/tutorials/01-blink-led/README.md)
2. [Read the onboard temperature sensor](micropython/tutorials/02-temperature-sensor/README.md)

### Experiments
(see https://kitronik.co.uk/blogs/resources/pico-inventors-kit-experiment-1-digital-inputs-outputs)

The [experiments](experiments/README.md) need the kit's components:

1. [Digital inputs and outputs](experiments/01-digital-inputs-outputs/README.md)
2. [Light sensor and analog inputs](experiments/02-light-sensor-analog-inputs/README.md)
3. [Dimming an LED with a potentiometer](experiments/03-dimming-led-potentiometer/README.md)
4. [Using a transistor to drive a motor](experiments/04-transistor-motor/README.md)
5. [Controlling a servo with a potentiometer](experiments/05-servo-potentiometer/README.md)
6. [Setting the tone with a piezo buzzer](experiments/06-piezo-buzzer-tones/README.md)
7. [Using a seven segment display](experiments/07-seven-segment-display/README.md)
8. [Exploring wind power](experiments/08-exploring-wind-power/README.md)
9. [Capacitor charge circuit](experiments/09-capacitor-charge-circuit/README.md)
10. [Controlling ZIP LEDs](experiments/10-controlling-zip-leds/README.md)

The experiment code is original and was written without access to Kitronik's
guides, so the **pin numbers are assumptions**. Check the pin constants at the
top of each `main.py` against your kit's guide before running.

### Projects

The [projects](projects/README.md) use extra hardware modules:

1. [Waveshare Pico-GPS-L76B GPS module](projects/01-gps-l76b/README.md)
2. [Random dice](projects/02-dice/README.md)
3. [OLED temperature display](projects/03-oled-temperature/README.md)
4. [Scrolling message](projects/04-message/README.md)
5. [Two random cat faces](projects/05-cat-faces/README.md)
6. [UTC clock on the Waveshare Pico-LCD-1.8](projects/06-utc-clock/README.md)

### Running a program

Open a tutorial's, experiment's or project's `main.py`, connect a Pico running MicroPython,
and run **Tasks: Run Task → Run current file on Pico (no save)** to test, or
**Upload current file to Pico as main.py** to save it on the board. If a task
can't connect, close anything else using the Pico's serial port.

For an interactive REPL, run `python -m mpremote connect auto repl` in the VS Code
terminal (`Ctrl+]` to exit).

## VS Code

Install the recommended extensions when prompted. Everything can be done in
VS Code without Thonny:

- **Raspberry Pi Pico** installs the C/C++ toolchain and SDK, and provides
  build, run, and debug. If you use it, it can replace the CMake presets and
  the `PICO_SDK_PATH` requirement.
- **MicroPico** provides a MicroPython REPL, file sync, and run-file buttons
  for the Pico.
- **CMake Tools**, **C/C++**, **Python**, and **Pylance** provide editing and
  build support. Select the Python interpreter that has `mpremote` installed.
