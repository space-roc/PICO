# Project 5: Two independent cats with randomly changing expressions
#
# Display 1: SDA -> GP8,  SCL -> GP9   (hardware I2C0)
# Display 2: SDA -> GP12, SCL -> GP13  (software I2C)
# The displays can use the same I2C address because they are on separate buses.
#
# Upload ssd1306.py to the Pico alongside this file.

import random
from math import cos, pi, sin
from machine import I2C, Pin, SoftI2C
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

from ssd1306 import SSD1306_I2C

WIDTH = 128
HEIGHT = 64
FRAME_MS = 100
MIN_EXPRESSION_MS = 1000
MAX_EXPRESSION_MS = 3000

OPEN_EXPRESSIONS = ("wide-eyed", "angry", "happy")
GAZES = ("left", "center", "right")
GAZE_OFFSETS = {"left": -3, "center": 0, "right": 3}
WHISKER_POSES = ("level", "perk", "droop")
HEAD_TURN_CHANCE = 5
MEOW_CHANCE = 10 # Probability of meowing 1 in this number of frames

# Sleeping eyes are closed, so their visible variations come from whiskers.
VARIATIONS = tuple(
    (expression, gaze, whiskers)
    for expression in OPEN_EXPRESSIONS
    for gaze in GAZES
    for whiskers in WHISKER_POSES
) + tuple(
    ("sleeping", "center", whiskers)
    for whiskers in WHISKER_POSES
)


def find_display(i2c, name):
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on " + name + ": check its wiring")
    address = 0x3C if 0x3C in devices else devices[0]
    print(name, "found I2C device at", hex(address))
    return SSD1306_I2C(WIDTH, HEIGHT, i2c, address)


def draw_polyline(oled, points):
    for index in range(len(points) - 1):
        x1, y1 = points[index]
        x2, y2 = points[index + 1]
        oled.line(x1, y1, x2, y2, 1)


class TurnedFace:
    def __init__(self, oled, direction):
        self.oled = oled
        self.direction = direction

    def _x(self, x):
        if self.direction == "center":
            return x
        if self.direction == "left":
            pivot = 60
            scale = 0.95 if x < 64 else 0.65
        else:
            pivot = 68
            scale = 0.65 if x < 64 else 0.95
        return int(pivot + (x - 64) * scale)

    def line(self, x1, y1, x2, y2, color):
        self.oled.line(self._x(x1), y1, self._x(x2), y2, color)

    def pixel(self, x, y, color):
        self.oled.pixel(self._x(x), y, color)

    def fill_rect(self, x, y, width, height, color):
        left = self._x(x)
        right = self._x(x + width)
        self.oled.fill_rect(min(left, right), y, abs(right - left), height, color)

    def text(self, string, x, y, color=1):
        self.oled.text(string, self._x(x), y, color)


def draw_ellipse(oled, cx, cy, rx, ry):
    for angle in range(0, 360, 5):
        radians = angle * pi / 180
        x = cx + int(rx * cos(radians))
        y = cy + int(ry * sin(radians))
        oled.pixel(x, y, 1)


def draw_whiskers(oled, pose):
    if pose == "perk":
        middle_offset, tip_offset = -3, -6
    elif pose == "droop":
        middle_offset, tip_offset = 3, 6
    else:
        middle_offset, tip_offset = 0, 0

    draw_polyline(oled, (
        (39, 45), (24, 42 + middle_offset), (12, 40 + tip_offset),
    ))
    draw_polyline(oled, (
        (38, 50), (23, 50 + middle_offset), (11, 52 + tip_offset),
    ))
    draw_polyline(oled, (
        (89, 45), (104, 42 + middle_offset), (116, 40 + tip_offset),
    ))
    draw_polyline(oled, (
        (90, 50), (105, 50 + middle_offset), (117, 52 + tip_offset),
    ))


def draw_head(oled):
    draw_polyline(oled, ((35, 29), (37, 8), (55, 23)))
    draw_polyline(oled, ((73, 23), (91, 8), (93, 29)))
    draw_polyline(oled, ((41, 19), (45, 15), (52, 22)))
    draw_polyline(oled, ((76, 22), (83, 15), (87, 19)))
    draw_polyline(oled, (
        (35, 27), (41, 21), (49, 19), (56, 22), (64, 24),
        (72, 22), (79, 19), (87, 21), (93, 27), (94, 38),
        (91, 48), (85, 55), (76, 60), (64, 62), (52, 60),
        (43, 55), (37, 48), (34, 38), (35, 27),
    ))


def draw_wide_eyes(oled, gaze):
    pupil_offset = GAZE_OFFSETS[gaze]
    for x in (50, 78):
        draw_ellipse(oled, x, 36, 7, 9)
        oled.fill_rect(x + pupil_offset - 2, 33, 5, 7, 1)
        oled.pixel(x + pupil_offset - 1, 34, 0)


def draw_sleeping_eyes(oled):
    draw_polyline(oled, ((43, 37), (47, 40), (51, 41), (55, 40), (58, 37)))
    draw_polyline(oled, ((70, 37), (73, 40), (78, 41), (82, 40), (86, 37)))


def draw_angry_eyes(oled, gaze):
    pupil_offset = GAZE_OFFSETS[gaze]
    draw_polyline(oled, ((43, 30), (58, 35), (58, 39), (54, 42), (47, 41), (43, 37), (43, 30)))
    draw_polyline(oled, ((85, 30), (70, 35), (70, 39), (74, 42), (81, 41), (85, 37), (85, 30)))
    oled.fill_rect(49 + pupil_offset, 36, 4, 5, 1)
    oled.fill_rect(75 + pupil_offset, 36, 4, 5, 1)
    draw_polyline(oled, ((42, 27), (57, 32)))
    draw_polyline(oled, ((86, 27), (71, 32)))


def draw_happy_eyes(oled, gaze):
    pupil_offset = GAZE_OFFSETS[gaze]
    for x in (50, 78):
        draw_ellipse(oled, x, 36, 7, 8)
        oled.fill_rect(x + pupil_offset - 2, 34, 5, 6, 1)
        oled.pixel(x + pupil_offset - 1, 35, 0)
    draw_polyline(oled, ((43, 26), (48, 23), (53, 23), (58, 26)))
    draw_polyline(oled, ((70, 26), (75, 23), (80, 23), (85, 26)))


def draw_muzzle(oled, expression):
    draw_polyline(oled, ((61, 44), (64, 47), (67, 44), (61, 44)))
    draw_polyline(oled, ((64, 47), (64, 50), (60, 53)))
    draw_polyline(oled, ((64, 50), (68, 53)))
    if expression == "happy":
        draw_polyline(oled, ((60, 53), (57, 52), (56, 49)))
        draw_polyline(oled, ((68, 53), (71, 52), (72, 49)))
    elif expression == "angry":
        draw_polyline(oled, ((60, 53), (57, 55), (55, 54)))
        draw_polyline(oled, ((68, 53), (71, 55), (73, 54)))
    else:
        draw_polyline(oled, ((60, 53), (57, 54), (56, 53)))
        draw_polyline(oled, ((68, 53), (71, 54), (72, 53)))


def draw_cat(oled, expression, gaze, whisker_pose, head_turn, meow):
    oled.fill(0)
    face = TurnedFace(oled, head_turn)
    draw_head(face)
    if expression == "wide-eyed":
        draw_wide_eyes(face, gaze)
    elif expression == "sleeping":
        draw_sleeping_eyes(face)
        oled.text("z", 2, 8)
        oled.text("z", 10, 0)
        oled.text("z", 18, 8)
    elif expression == "angry":
        draw_angry_eyes(face, gaze)
    else:
        draw_happy_eyes(face, gaze)
    draw_muzzle(face, expression)
    draw_whiskers(face, whisker_pose)
    if meow:
        oled.text("Meooowww!", 48, 0)
    oled.show()


class Cat:
    def __init__(self, oled, name):
        self.oled = oled
        self.name = name
        self.variation = None
        self.next_change = ticks_ms()
        self.update(self.next_change)

    def update(self, now):
        if ticks_diff(now, self.next_change) < 0:
            return
        choices = [variation for variation in VARIATIONS if variation != self.variation]
        self.variation = choices[random.randrange(len(choices))]
        expression, gaze, whisker_pose = self.variation
        if random.randrange(HEAD_TURN_CHANCE) == 0:
            head_turn = ("left", "right")[random.randrange(2)]
        else:
            head_turn = "center"
        meow = random.randrange(MEOW_CHANCE) == 0
        print(self.name, expression, gaze, whisker_pose, head_turn,
              "MEOW" if meow else "")
        draw_cat(self.oled, expression, gaze, whisker_pose, head_turn, meow)
        delay = random.randint(MIN_EXPRESSION_MS, MAX_EXPRESSION_MS)
        self.next_change = ticks_add(now, delay)


i2c1 = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
i2c2 = SoftI2C(sda=Pin(12), scl=Pin(13), freq=400000)

cats = (
    Cat(find_display(i2c1, "display 1 (GP8/GP9)"), "Cat 1"),
    Cat(find_display(i2c2, "display 2 (GP12/GP13)"), "Cat 2"),
)

while True:
    now = ticks_ms()
    for cat in cats:
        cat.update(now)
    sleep_ms(FRAME_MS)
