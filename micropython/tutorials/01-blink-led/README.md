# Tutorial 1: Blink the onboard LED

Your first MicroPython program: blink the Pico's onboard LED and print a counter.
No extra hardware is needed.

## What you'll learn

- Importing modules (`machine`, `time`)
- Controlling a pin with `Pin`
- Looping forever and printing to the REPL

## Before you start

MicroPython must be flashed on the Pico and `mpremote` installed. See the
[main README](../../../README.md#prerequisites).

## The code

[main.py](main.py):

```python
from machine import Pin
from time import sleep

led = Pin("LED", Pin.OUT)
count = 0

while True:
    led.toggle()
    count += 1
    print("blink", count)
    sleep(0.5)
```

- `Pin("LED", Pin.OUT)` creates an output on the onboard LED. On an older
  MicroPython build with a plain Pico, use `Pin(25, Pin.OUT)`.
- `led.toggle()` flips the LED between on and off.
- `sleep(0.5)` waits half a second between toggles.

## Run it

1. Open `main.py` in VS Code.
2. Run **Tasks: Run Task → Run current file on Pico (no save)** to try it. Stop
   it with `Ctrl+C` in the terminal.
3. When happy, run **Tasks: Run Task → Upload current file to Pico as main.py**.
   The Pico runs it automatically on every power-up.
4. View output with `mpremote connect auto repl` (`Ctrl+]` to exit).

## Try it yourself

- Change the `sleep` value to blink faster or slower.
- Make a double-blink pattern.
- Stop after 20 blinks using `for` instead of `while True`.

## Troubleshooting

If you get a connection error, close anything else using the Pico's serial port
(including an open REPL) and try again.
