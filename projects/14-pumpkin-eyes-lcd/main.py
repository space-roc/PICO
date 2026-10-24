# Project 14: Cute pumpkin eyes on the Waveshare 0.71" Dual Eye round LCD
#
# Pico 2 W (a plain Pico or Pico 2 works too) driving two round 160x160 screens
# that blink, look around and pull faces.
#
#   LCD pin  Pico pin            LCD pin  Pico pin
#   VCC      3V3 (OUT)           RST1     GP7
#   GND      GND                 RST2     GP8
#   DIN      GP3                 BL1      GP9
#   CLK      GP2                 BL2      GP10
#   CS1      GP4                 DC       GP6
#   CS2      GP5
#
# Upload gc9d01.py, wifi_time.py, wifi_config.py and main.py to the Pico.

import random
from math import sqrt
from framebuf import FrameBuffer, MONO_HLSB, RGB565
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

from gc9d01 import BGR, ROTATIONS, SIZE, DualEye

try:
    import wifi_config
    import wifi_time
    print("Wi-Fi config loaded")
except ImportError:
    print("Wi-Fi config not found")
    wifi_config = None # No Wi-Fi details, so the eyes run without the clock

SCK_PIN = 2
MOSI_PIN = 3 # The LCD's DIN
DC_PIN = 6
CS_PINS = (4, 5) # CS1, CS2
RST_PINS = (7, 8) # RST1, RST2
BL_PINS = (9, 10) # BL1, BL2

SPI_BAUDRATE = 40_000_000 # Try 20_000_000 if the picture has glitches
BRIGHTNESS = 1.0 # 0 to 1

# Which of the four rotations (0 to 3) each screen needs. Waveshare's demo turns
# the two screens 180 degrees from each other, because of how they are mounted.
# If an eye is upside down or sideways, change its number.
ROTATION = (3, 1)
RED_BLUE_SWAPPED = False # Set to True if the orange eyes come out blue

# +1 means the inner (nose) side of this screen's eye is its right edge. If the
# eyes look cross-eyed or the angry brows slope the wrong way, swap these.
INNER = (1, -1)

STARTUP_TEST_MS = 3000 # Show a test screen for this long first (0 to skip)
FRAME_MS = 15
MIN_EXPRESSION_MS = 1500
MAX_EXPRESSION_MS = 4000
SLEEP_CHANCE = 0.08 # Chance that the next expression is a sleep (0 to turn off)
SLEEP_MS = 30000 # How long a sleep lasts
Z_CYCLE_MS = 3000 # Each Z takes this long to float up the screen
MIN_BLINK_MS = 1500
MAX_BLINK_MS = 5000

# The clock: the time (screen 1) and date (screen 2) pop up now and then
SHOW_CLOCK = True
CLOCK_INTERVAL_S = 60 # Seconds of eyes between each pop-up
CLOCK_SHOW_MS = 3000
WIFI_MESSAGE_MS = 2000 # How long "WI-FI OK" is shown at start-up
UTC_OFFSET_HOURS = 0 # Hours ahead of UTC (for example 1 for central Europe)
UK_DAYLIGHT_SAVING = True # Adds an hour in the UK summer; set False elsewhere
SYNC_INTERVAL_MIN = 360 # Re-check the time from the internet this often
SYNC_RETRY_MIN = 10 # Try again this soon if Wi-Fi failed


def rgb(red, green, blue):
    # FrameBuffer stores RGB565 little-endian; the LCD expects high byte first.
    value = (red & 0xF8) << 8 | (green & 0xFC) << 3 | blue >> 3
    return ((value & 0xFF) << 8) | (value >> 8)


BLACK = 0
WHITE = rgb(255, 255, 255)
EYE_WHITE = rgb(255, 236, 140) # Candle-glow yellow
IRIS = rgb(255, 150, 0)
IRIS_RING = rgb(200, 70, 0)
PUPIL = rgb(25, 0, 0)
BROW = rgb(255, 120, 0)

EYE_X = 80
EYE_Y = 88
EYE_RX = 58
EYE_RY = 50
IRIS_RADIUS = 34
RING_WIDTH = 3
PUPIL_RADIUS = 17
LOOK_X = EYE_RX - IRIS_RADIUS - 6
LOOK_Y = 10
BROW_Y = 26
BROW_HALF_LENGTH = 34
BROW_THICKNESS = 5
SMOOTHING = 0.4

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
    "cross": 0.0,    # + moves the iris towards the nose
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
    ("cute", {"pupil": 1.35, "brow_y": -4, "tilt": -2}, {}),
    ("angry", {"slant": 0.9, "tilt": 6, "brow_y": 1, "open": 0.9, "pupil": 0.8}, {}),
    ("evil", {"slant": 1.0, "tilt": 7, "brow_y": 2, "open": 0.6, "pupil": 0.4}, {}),
    ("sad", {"slant": -0.8, "tilt": -6, "brow_y": -1, "look_y": 0.6, "open": 0.85}, {}),
    ("surprised", {"brow_y": -7, "pupil": 0.5}, {}),
    ("sleepy", {"open": 0.3, "brow_y": 2, "look_y": 0.5}, {}),
    ("sleeping", {"open": 0.0, "brow_y": 4, "tilt": -2}, {}),
    ("suspicious", {"open": 0.55, "slant": 0.4, "tilt": 3, "look_x": 1},
     {1: {"open": 0.85, "slant": 0.0, "tilt": -3, "brow_y": -5}}),
    ("wink", {"lower": 0.5, "brow_y": -2},
     {1: {"open": 0.0, "lower": 0.0, "brow_y": 2}}),
    ("cross-eyed", {"cross": 1.0, "brow_y": -2}, {}),
    ("super cross-eyed", {"cross": 2.0, "pupil": 0.8, "brow_y": -3}, {}),
    ("wall-eyed", {"cross": -1.5, "brow_y": -2}, {}),
    ("shocked", {"pupil": 0.25, "brow_y": -10, "look_y": -0.3}, {}),
    ("huge pupils", {"pupil": 2.0, "brow_y": -5, "lower": 0.1}, {}),
    ("tiny pupils", {"pupil": 0.3, "brow_y": 1}, {}),
    ("furious", {"slant": 1.0, "tilt": 10, "brow_y": 4, "open": 0.75, "pupil": 0.3}, {}),
    ("devious", {"slant": 0.8, "lower": 0.6, "tilt": 6, "brow_y": 0, "open": 0.8,
                 "look_x": -1, "pupil": 0.6}, {}),
    ("heartbroken", {"slant": -1.0, "tilt": -9, "brow_y": -3, "look_y": 1,
                     "pupil": 1.7, "open": 0.9}, {}),
    ("bliss", {"lower": 0.75, "open": 0.9, "brow_y": -5, "tilt": -3, "pupil": 1.4}, {}),
    ("laughing", {"lower": 0.85, "open": 0.6, "brow_y": -6, "look_y": -0.3}, {}),
    ("dizzy", {"look_x": 1.6, "look_y": -1, "pupil": 0.5, "cross": 0.6},
     {1: {"look_x": -1.6, "look_y": 1, "cross": -0.6}}),
    ("glaring left", {"look_x": -1.6, "slant": 0.7, "tilt": 5, "open": 0.7, "pupil": 0.5}, {}),
    ("glaring right", {"look_x": 1.6, "slant": 0.7, "tilt": 5, "open": 0.7, "pupil": 0.5}, {}),
    ("peeking up", {"look_y": -1.8, "brow_y": -6, "open": 0.8}, {}),
    ("peeking down", {"look_y": 1.8, "brow_y": 3, "open": 0.7}, {}),
    ("bug-eyed", {"pupil": 0.6, "brow_y": -12, "open": 1.0, "look_y": -0.2},
     {1: {"pupil": 0.35, "brow_y": -8}}),
    ("one raised brow", {"brow_y": 0, "open": 0.8},
     {0: {"brow_y": -10, "tilt": -4, "open": 1.0}, 1: {"slant": 0.7, "tilt": 6, "open": 0.6}}),
    ("half asleep", {"open": 0.15, "brow_y": 4, "look_y": 1, "lower": 0.1}, {}),
    ("mischievous wink", {"slant": 0.5, "tilt": 4, "look_x": 1, "lower": 0.4},
     {1: {"open": 0.0, "lower": 0.0, "slant": 0.0, "tilt": 0, "brow_y": 3}}),
    ("manic", {"pupil": 0.25, "brow_y": -10, "slant": 0.4, "tilt": 3, "look_y": 0.4,
               "cross": 0.5}, {}),
)

buffer = bytearray(SIZE * SIZE * 2)
frame = FrameBuffer(buffer, SIZE, SIZE, RGB565)

# Per-column ellipse geometry, worked out once: (dx, half height, 1 - t * t).
COLUMNS = []
for _dx in range(-EYE_RX, EYE_RX + 1):
    _t = _dx / EYE_RX
    _w = 1 - _t * _t
    COLUMNS.append((_dx, EYE_RY * sqrt(_w), _w))


def fill_disc(spans, cx, cy, radius, colour):
    # A filled circle, clipped to the visible part of the eye.
    for x in range(cx - radius, cx + radius + 1):
        index = x - (EYE_X - EYE_RX)
        if 0 <= index < len(spans) and spans[index]:
            top, bottom = spans[index]
            offset = x - cx
            reach = int(sqrt(radius * radius - offset * offset))
            y0 = max(cy - reach, top)
            y1 = min(cy + reach, bottom)
            if y1 >= y0:
                frame.fill_rect(x, y0, 1, y1 - y0 + 1, colour)


class Eye:
    def __init__(self, index, inner):
        self.index = index
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
        v = self.values
        inner = self.inner
        frame.fill(BLACK)

        openness = max(0.0, min(1.0, v["open"] * blink))
        closing = 1 - openness
        top_limit = EYE_Y - EYE_RY + closing * EYE_RY * 1.1
        bottom_limit = EYE_Y + EYE_RY - closing * EYE_RY * 0.9
        slant = v["slant"] * EYE_RY * 0.9
        lower = v["lower"] * EYE_RY * 1.5

        iris_x = int(EYE_X + v["look_x"] * LOOK_X + v["cross"] * inner * 14)
        iris_y = int(EYE_Y + v["look_y"] * LOOK_Y)
        pupil_radius = max(4, int(PUPIL_RADIUS * v["pupil"]))
        layers = ((IRIS_RADIUS + RING_WIDTH, IRIS_RING), (IRIS_RADIUS, IRIS),
                  (pupil_radius, PUPIL))

        spans = []
        for dx, half_height, weight in COLUMNS:
            top = max(EYE_Y - half_height, top_limit + slant * inner * dx / EYE_RX)
            bottom = min(EYE_Y + half_height, bottom_limit - lower * weight)
            top = int(top)
            bottom = int(bottom)
            if bottom <= top:
                spans.append(None)
                continue
            spans.append((top, bottom))
            x = EYE_X + dx
            frame.fill_rect(x, top, 1, bottom - top + 1, EYE_WHITE)

            offset = x - iris_x
            for radius, colour in layers:
                if -radius <= offset <= radius:
                    reach = int(sqrt(radius * radius - offset * offset))
                    y0 = max(iris_y - reach, top)
                    y1 = min(iris_y + reach, bottom)
                    if y1 >= y0:
                        frame.fill_rect(x, y0, 1, y1 - y0 + 1, colour)

        # Sparkles that make the eyes look wet and cute.
        fill_disc(spans, iris_x - 13, iris_y - 13, 8, WHITE)
        fill_disc(spans, iris_x + 12, iris_y + 12, 4, WHITE)

        if openness < 0.1:
            # A fully closed eye is drawn as a thick line.
            frame.fill_rect(EYE_X - EYE_RX + 8, EYE_Y - 2, 2 * EYE_RX - 16, 5, BROW)

        self._draw_brow(v, inner)

    def _draw_brow(self, v, inner):
        base = BROW_Y + v["brow_y"]
        inner_x = EYE_X + inner * BROW_HALF_LENGTH
        outer_x = EYE_X - inner * BROW_HALF_LENGTH
        inner_y = int(base + v["tilt"])
        outer_y = int(base - v["tilt"] * 0.5)
        for thickness in range(BROW_THICKNESS):
            frame.line(outer_x, outer_y + thickness, inner_x, inner_y + thickness, BROW)


def show_test_screen(lcd, index):
    # Colour bars, the screen number and an arrow at the top, to check the
    # wiring, colours and which way up each screen is.
    frame.fill(BLACK)
    frame.rect(0, 0, SIZE, SIZE, WHITE)
    for position, colour in enumerate((rgb(255, 0, 0), rgb(0, 255, 0), rgb(0, 0, 255))):
        frame.fill_rect(40 + position * 27, 70, 27, 30, colour)
    frame.text("SCREEN {}".format(index + 1), 44, 108, WHITE)
    frame.text("R  G  B", 52, 56, WHITE)
    frame.text("TOP", 68, 8, WHITE)
    for row in range(10):
        frame.hline(80 - row, 20 + row, 2 * row + 1, WHITE)
    lcd.show(index, buffer)


DAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

glyph_bits = bytearray(8)
glyph = FrameBuffer(glyph_bits, 8, 8, MONO_HLSB)


def draw_text(text, y, scale, colour=BROW, x=None):
    # The built-in 8x8 font, enlarged; centred on the screen unless x is given
    if x is None:
        x = (SIZE - len(text) * 8 * scale) // 2
    for character in text:
        glyph.fill(0)
        glyph.text(character, 0, 0, 1)
        for row in range(8):
            bits = glyph_bits[row]
            for column in range(8):
                if bits & (0x80 >> column):
                    frame.fill_rect(x + column * scale, y + row * scale, scale, scale, colour)
        x += 8 * scale


def show_message(lcd, *lines):
    for index in range(2):
        frame.fill(BLACK)
        top = 80 - len(lines) * 16
        for number, text in enumerate(lines):
            draw_text(text, top + number * 32, 3)
        lcd.show(index, buffer)


def show_clock(lcd, local):
    month, day, hour, minute, weekday = local[1], local[2], local[3], local[4], local[6]
    frame.fill(BLACK)
    draw_text("{:02d}".format(hour), 26, 6)
    draw_text("{:02d}".format(minute), 86, 6)
    lcd.show(0, buffer)
    frame.fill(BLACK)
    draw_text(DAYS[weekday], 22, 3)
    draw_text("{:02d}".format(day), 56, 6)
    draw_text(MONTHS[month - 1], 110, 3)
    lcd.show(1, buffer)


def draw_z(x, y, size, thickness):
    frame.fill_rect(x, y, size, thickness, WHITE)
    frame.fill_rect(x, y + size - thickness, size, thickness, WHITE)
    for offset in range(thickness):
        frame.line(x + size - 1 - offset, y, x - offset + 1, y + size - 1, WHITE)


def draw_zs(now):
    # Three Zs float up and to the right, growing as they go, staggered in time
    for number in range(3):
        progress = ((now + number * Z_CYCLE_MS // 3) % Z_CYCLE_MS) / Z_CYCLE_MS
        size = 8 + int(progress * 20)
        x = 84 + int(progress * 30) + (number % 2) * 6
        y = 80 - int(progress * 66)
        draw_z(x, y, size, 2 + size // 10)


def render_eyes(lcd, eyes, blink, now=0, sleeping=False):
    for eye in eyes:
        eye.step()
        eye.draw(blink)
        if sleeping:
            draw_zs(now)
        lcd.show(eye.index, buffer)


def sync_time():
    return wifi_time.sync(wifi_config.SSID, wifi_config.PASSWORD)


def choose_expression(previous):
    if previous != "sleeping" and random.random() < SLEEP_CHANCE:
        return next(item for item in EXPRESSIONS if item[0] == "sleeping")
    choices = [item for item in EXPRESSIONS if item[0] not in (previous, "sleeping")]
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
    bgr = BGR if RED_BLUE_SWAPPED else 0
    lcd = DualEye(SCK_PIN, MOSI_PIN, DC_PIN, CS_PINS, RST_PINS, BL_PINS,
                  [ROTATIONS[rotation] | bgr for rotation in ROTATION],
                  SPI_BAUDRATE, BRIGHTNESS)
    eyes = [Eye(0, INNER[0]), Eye(1, INNER[1])]

    if STARTUP_TEST_MS:
        for index in range(2):
            show_test_screen(lcd, index)
        sleep_ms(STARTUP_TEST_MS)

    name = None
    if SHOW_CLOCK and wifi_config is None:
        show_message(lcd, "NO", "WI-FI", "CONFIG")
        sleep_ms(WIFI_MESSAGE_MS)
    clock_enabled = SHOW_CLOCK and wifi_config is not None
    time_set = False
    if clock_enabled:
        show_message(lcd, "WI-FI", "...")
        time_set = sync_time()
        if time_set:
            show_message(lcd, "WI-FI", "OK")
            sleep_ms(WIFI_MESSAGE_MS)
            show_clock(lcd, wifi_time.local_time(UTC_OFFSET_HOURS, UK_DAYLIGHT_SAVING))
            sleep_ms(CLOCK_SHOW_MS)
        else:
            show_message(lcd, "NO", "WI-FI")
            sleep_ms(WIFI_MESSAGE_MS)
    now = ticks_ms()
    next_sync = ticks_add(now, (SYNC_INTERVAL_MIN if time_set else SYNC_RETRY_MIN) * 60000)
    next_clock = ticks_add(now, CLOCK_INTERVAL_S * 1000)
    next_expression = now
    next_blink = ticks_add(now, random.randint(MIN_BLINK_MS, MAX_BLINK_MS))
    blink_frame = len(BLINK_FRAMES)

    while True:
        now = ticks_ms()
        if clock_enabled and ticks_diff(now, next_sync) >= 0:
            time_set = sync_time() or time_set
            now = ticks_ms()
            next_sync = ticks_add(now, (SYNC_INTERVAL_MIN if time_set else SYNC_RETRY_MIN) * 60000)
        if time_set and ticks_diff(now, next_clock) >= 0:
            for blink in BLINK_FRAMES[:2]:
                render_eyes(lcd, eyes, blink)
                sleep_ms(FRAME_MS)
            show_clock(lcd, wifi_time.local_time(UTC_OFFSET_HOURS, UK_DAYLIGHT_SAVING))
            sleep_ms(CLOCK_SHOW_MS)
            now = ticks_ms()
            next_clock = ticks_add(now, CLOCK_INTERVAL_S * 1000)
            blink_frame = 0 # Open the eyes again
        if ticks_diff(now, next_expression) >= 0:
            expression = choose_expression(name)
            name = expression[0]
            apply_expression(eyes, expression)
            next_expression = ticks_add(
                now, SLEEP_MS if name == "sleeping"
                else random.randint(MIN_EXPRESSION_MS, MAX_EXPRESSION_MS)
            )
        if blink_frame >= len(BLINK_FRAMES) and ticks_diff(now, next_blink) >= 0:
            blink_frame = 0
            next_blink = ticks_add(now, random.randint(MIN_BLINK_MS, MAX_BLINK_MS))

        blink = 1.0
        if blink_frame < len(BLINK_FRAMES):
            blink = BLINK_FRAMES[blink_frame]
            blink_frame += 1

        render_eyes(lcd, eyes, blink, now, name == "sleeping")
        sleep_ms(FRAME_MS)


if __name__ == "__main__":
    main()
