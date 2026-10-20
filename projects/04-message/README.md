# Project 4: Scrolling message

Show a scrolling message on the blue part of a two-colour OLED and a separate
fixed message on the yellow part.

## What you'll learn

- How two-colour SSD1306 displays split into a yellow strip and a blue area
- Animating text by redrawing it at a shifting x position

## Hardware

- A two-colour (yellow/blue) SSD1306 I2C OLED, 128x64
- OLED VCC to 3.3 V, GND to GND, **SDA to GP8**, **SCL to GP9**

## Run it

1. Upload [ssd1306.py](ssd1306.py) to the Pico, for example
   `python -m mpremote connect auto fs cp ssd1306.py :ssd1306.py`.
2. Edit `YELLOW_MESSAGE` and `BLUE_MESSAGE` at the top of [main.py](main.py).
3. Use **Run current file on Pico (no save)**, or **Upload current file to Pico
   as main.py** to run at power-up.

## How it works

- The yellow strip is the top 16 pixel rows; the blue area is the rest. The
  colours are fixed by the panel, so the code just draws in the right rows.
- Each frame clears the screen, draws the yellow text centred, draws the blue
  text at `x`, then reduces `x` by `SCROLL_STEP`. When the text has fully left
  the screen, `x` resets to the right edge.

## Try it yourself

- Change `SCROLL_STEP` and `FRAME_MS` to alter the speed.
- Make the message scroll left to right instead.
- Cycle through a list of yellow messages.

## Troubleshooting

- **Yellow text is cut off:** the yellow message is limited to 16 characters.
- **Text appears in the wrong colour:** your panel's yellow strip may be a
  different height; change `YELLOW_HEIGHT`.
- **"No I2C device found":** check SDA/SCL are on GP8/GP9 and power is connected.
