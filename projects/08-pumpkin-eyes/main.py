# Project 8: Pumpkin eyes on two OLED displays
#
# Display 1 (left eye):  SDA -> GP8,  SCL -> GP9   (hardware I2C0)
# Display 2 (right eye): SDA -> GP12, SCL -> GP13  (software I2C)
#
# Upload ssd1306.py to the Pico alongside this file.

import random
from math import sqrt
from machine import I2C, Pin, SoftI2C
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

from ssd1306 import SSD1306_I2C

WIDTH = 128
HEIGHT = 64
FRAME_MS = 30
MIN_EXPRESSION_MS = 1500
MAX_EXPRESSION_MS = 4000
MIN_BLINK_MS = 1500
MAX_BLINK_MS = 5000

# If the eyes look cross-eyed or angry brows slope the wrong way, swap these:
# +1 means the inner (nose) side of this display's eye is its right edge.
LEFT_EYE_INNER = 1
RIGHT_EYE_INNER = -1

EYE_X = 64
EYE_Y = 41
EYE_RX = 40
EYE_RY = 21
PUPIL_RADIUS = 9
BROW_Y = 11
BROW_HALF_LENGTH = 34
BROW_THICKNESS = 4
SMOOTHING = 0.45

# Eye openness multipliers applied over successive frames during a blink.
BLINK_FRAMES = (0.55, 0.0, 0.0, 0.5)

DEFAULTS = {
    "look_x": 0.0,   # -1 looks left, +1 looks right
    "look_y": 0.0,   # -1 looks up, +1 looks down
    "open": 1.0,     # 1 fully open, 0 closed
    "slant": 0.0,    # + lowers the inner upper lid (angry), - lowers the outer (sad)
    "lower": 0.0,    # raises the lower lid into an arch (happy/squint)
    "brow_y": 0.0,   # pixels; negative raises the eyebrow
    "tilt": 0.0,     # pixels; + drops the inner end of the eyebrow
    "pupil": 1.0,    # pupil size multiplier
    "cross": 0.0,    # + moves the pupil towards the nose
}

# (name, settings for both eyes, {eye index: settings that override one eye})
EXPRESSIONS = (
    ("neutral", {}, {}),
    ("look left", {"look_x": -1}, {}),
    ("look right", {"look_x": 1}, {}),
    ("look up", {"look_y": -1, "brow_y": -3}, {}),
    ("look down", {"look_y": 1, "brow_y": 2}, {}),
    ("look up left", {"look_x": -1, "look_y": -1, "brow_y": -3}, {}),
    ("look down right", {"look_x": 1, "look_y": 1, "brow_y": 2}, {}),
    ("squint", {"open": 0.6, "lower": 0.2, "brow_y": 3}, {}),
    ("happy", {"lower": 0.85, "open": 0.95, "brow_y": -3}, {}),
    ("angry", {"slant": 0.9, "tilt": 6, "brow_y": 1, "open": 0.9, "pupil": 0.8}, {}),
    ("evil", {"slant": 1.0, "tilt": 7, "brow_y": 2, "open": 0.6, "pupil": 0.4}, {}),
    ("sad", {"slant": -0.8, "tilt": -6, "brow_y": -1, "look_y": 0.6, "open": 0.85}, {}),
    ("surprised", {"brow_y": -7, "pupil": 0.5}, {}),
    ("sleepy", {"open": 0.3, "brow_y": 2, "look_y": 0.5}, {}),
    ("suspicious", {"open": 0.55, "slant": 0.4, "tilt": 3, "look_x": 1},
     {1: {"open": 0.85, "slant": 0.0, "tilt": -3, "brow_y": -5}}),
    ("wink", {"lower": 0.5, "brow_y": -2},
     {1: {"open": 0.0, "lower": 0.0, "brow_y": 2}}),
    ("cross-eyed", {"cross": 1.0, "brow_y": -2}, {}),
)

# Per-column ellipse geometry, worked out once: (dx, half height, 1 - t * t).
COLUMNS = []
for _dx in range(-EYE_RX, EYE_RX + 1):
    _t = _dx / EYE_RX
    _w = 1 - _t * _t
    COLUMNS.append((_dx, EYE_RY * sqrt(_w), _w))


def find_display(i2c, name):
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on " + name + ": check its wiring")
    address = 0x3C if 0x3C in devices else devices[0]
    print(name, "found I2C device at", hex(address))
    return SSD1306_I2C(WIDTH, HEIGHT, i2c, address)


class Eye:
    def __init__(self, oled, inner):
        self.oled = oled
        self.inner = inner
        self.values = dict(DEFAULTS)
        self.targets = dict(DEFAULTS)

    def set_target(self, settings):
        self.targets = dict(DEFAULTS)
        self.targets.update(settings)

    def step(self):
        values = self.values
        for key, target in self.targets.items():
            value = values[key]
            if abs(target - value) < 0.02:
                values[key] = target
            else:
                values[key] = value + (target - value) * SMOOTHING

    def draw(self, blink):
        oled = self.oled
        v = self.values
        inner = self.inner
        oled.fill(0)

        openness = max(0.0, min(1.0, v["open"] * blink))
        closing = 1 - openness
        top_limit = EYE_Y - EYE_RY + closing * EYE_RY * 1.1
        bottom_limit = EYE_Y + EYE_RY - closing * EYE_RY * 0.9
        slant = v["slant"] * EYE_RY * 0.9
        lower = v["lower"] * EYE_RY * 1.5

        radius = max(2, int(PUPIL_RADIUS * v["pupil"]))
        pupil_x = int(
            EYE_X + v["look_x"] * (EYE_RX - PUPIL_RADIUS - 3)
            + v["cross"] * inner * 14
        )
        pupil_y = int(EYE_Y + v["look_y"] * 9)

        for dx, half_height, weight in COLUMNS:
            top = max(EYE_Y - half_height, top_limit + slant * inner * dx / EYE_RX)
            bottom = min(EYE_Y + half_height, bottom_limit - lower * weight)
            top = int(top)
            bottom = int(bottom)
            if bottom <= top:
                continue
            x = EYE_X + dx
            oled.fill_rect(x, top, 1, bottom - top + 1, 1)

            offset = x - pupil_x
            if -radius <= offset <= radius:
                reach = int(sqrt(radius * radius - offset * offset))
                y0 = max(pupil_y - reach, top)
                y1 = min(pupil_y + reach, bottom)
                if y1 >= y0:
                    oled.fill_rect(x, y0, 1, y1 - y0 + 1, 0)

        if openness < 0.1:
            # A fully closed eye is drawn as a thick line.
            oled.fill_rect(EYE_X - EYE_RX + 4, EYE_Y - 1, 2 * EYE_RX - 8, 3, 1)

        self._draw_brow(v, inner)
        oled.show()

    def _draw_brow(self, v, inner):
        base = BROW_Y + v["brow_y"]
        inner_x = EYE_X + inner * BROW_HALF_LENGTH
        outer_x = EYE_X - inner * BROW_HALF_LENGTH
        inner_y = int(base + v["tilt"])
        outer_y = int(base - v["tilt"] * 0.5)
        for thickness in range(BROW_THICKNESS):
            self.oled.line(outer_x, outer_y + thickness,
                           inner_x, inner_y + thickness, 1)


def choose_expression(previous):
    choices = [item for item in EXPRESSIONS if item[0] != previous]
    return choices[random.randrange(len(choices))]


def apply_expression(eyes, expression):
    name, shared, overrides = expression
    # Asymmetric expressions such as a wink randomly use either eye.
    flip = random.randrange(2)
    for index, eye in enumerate(eyes):
        settings = dict(shared)
        settings.update(overrides.get(index ^ flip, {}))
        eye.set_target(settings)
    print(name)


def main():
    i2c1 = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
    i2c2 = SoftI2C(sda=Pin(12), scl=Pin(13), freq=400000)
    eyes = (
        Eye(find_display(i2c1, "left eye (GP8/GP9)"), LEFT_EYE_INNER),
        Eye(find_display(i2c2, "right eye (GP12/GP13)"), RIGHT_EYE_INNER),
    )

    name = None
    now = ticks_ms()
    next_expression = now
    next_blink = ticks_add(now, random.randint(MIN_BLINK_MS, MAX_BLINK_MS))
    blink_frame = len(BLINK_FRAMES)

    while True:
        now = ticks_ms()
        if ticks_diff(now, next_expression) >= 0:
            expression = choose_expression(name)
            name = expression[0]
            apply_expression(eyes, expression)
            next_expression = ticks_add(
                now, random.randint(MIN_EXPRESSION_MS, MAX_EXPRESSION_MS)
            )
        if blink_frame >= len(BLINK_FRAMES) and ticks_diff(now, next_blink) >= 0:
            blink_frame = 0
            next_blink = ticks_add(now, random.randint(MIN_BLINK_MS, MAX_BLINK_MS))

        blink = 1.0
        if blink_frame < len(BLINK_FRAMES):
            blink = BLINK_FRAMES[blink_frame]
            blink_frame += 1

        for eye in eyes:
            eye.step()
            eye.draw(blink)
        sleep_ms(FRAME_MS)


if __name__ == "__main__":
    main()
