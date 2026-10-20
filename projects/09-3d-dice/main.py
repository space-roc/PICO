# Project 9: Two 3D twelve-sided dice that tumble when a button is pressed
#
# Display 1: SDA -> GP8,  SCL -> GP9   (hardware I2C0)
# Display 2: SDA -> GP12, SCL -> GP13  (software I2C)
# Button: GP15 -> push button -> GND
#
# Upload ssd1306.py to the Pico alongside this file.

import random
from math import atan2, cos, pi, sin, sqrt
from machine import I2C, Pin, SoftI2C
from time import sleep_ms, ticks_diff, ticks_ms

from ssd1306 import SSD1306_I2C

WIDTH = 128
HEIGHT = 64
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2
BUTTON_PIN = 15
POLL_MS = 10
ROLL_MS = 1800
ROLL_STAGGER_MS = 350 # The second die takes slightly longer to settle

DIE_SCALE = 15 # Pixels per unit; the dodecahedron's corners are 1.73 units out
CAMERA_DISTANCE = 6.0 # Larger is flatter, smaller is more perspective
NUMBER_MIN_FACING = 0.3 # Faces turned further away than this show no number
TWO_PI = 2 * pi
PHI = (1 + sqrt(5)) / 2

# Corners of a regular dodecahedron: a cube plus three groups of four pairs.
VERTICES = [
    (sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)
]
for s1 in (-1, 1):
    for s2 in (-1, 1):
        VERTICES.append((0, s1 / PHI, s2 * PHI))
        VERTICES.append((s1 / PHI, s2 * PHI, 0))
        VERTICES.append((s2 * PHI, 0, s1 / PHI))

# Face directions; each has an opposite face, numbered 13 - value.
HALF_NORMALS = (
    (0, PHI, 1), (0, PHI, -1), (PHI, 1, 0), (PHI, -1, 0), (1, 0, PHI), (-1, 0, PHI),
)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize(a):
    length = sqrt(dot(a, a))
    return (a[0] / length, a[1] / length, a[2] / length)


def build_face(direction):
    normal = normalize(direction)
    best = max(dot(vertex, normal) for vertex in VERTICES)
    corners = [v for v in VERTICES if dot(v, normal) > best - 0.01]
    # The first corner defines "up" on the face; sort the corners around it.
    first = corners[0]
    along = dot(first, normal)
    up = normalize((first[0] - normal[0] * along, first[1] - normal[1] * along,
                    first[2] - normal[2] * along))
    right = cross(up, normal)
    corners.sort(key=lambda v: atan2(dot(v, up), dot(v, right)))
    centre = (normal[0] * best, normal[1] * best, normal[2] * best)
    # Rows of this matrix turn the face towards the viewer with `up` upwards.
    return normal, corners, centre, (right, up, normal)


# value: (normal, corners, centre, matrix that brings the face to the front)
FACES = {}
for index, direction in enumerate(HALF_NORMALS):
    FACES[index + 1] = build_face(direction)
    FACES[12 - index] = build_face((-direction[0], -direction[1], -direction[2]))


def mat_mul(a, b):
    return tuple(
        tuple(sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3))
        for r in range(3)
    )


def transform(m, p):
    return (
        m[0][0] * p[0] + m[0][1] * p[1] + m[0][2] * p[2],
        m[1][0] * p[0] + m[1][1] * p[1] + m[1][2] * p[2],
        m[2][0] * p[0] + m[2][1] * p[1] + m[2][2] * p[2],
    )


def axis_rotation(axis, angle):
    x, y, z = axis
    c, s = cos(angle), sin(angle)
    t = 1 - c
    return (
        (t * x * x + c, t * x * y - s * z, t * x * z + s * y),
        (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
        (t * x * z - s * y, t * y * z + s * x, t * z * z + c),
    )


def matrix_to_quaternion(m):
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0:
        s = sqrt(trace + 1) * 2
        return (s / 4, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s,
                (m[1][0] - m[0][1]) / s)
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = sqrt(1 + m[0][0] - m[1][1] - m[2][2]) * 2
        return ((m[2][1] - m[1][2]) / s, s / 4, (m[0][1] + m[1][0]) / s,
                (m[0][2] + m[2][0]) / s)
    if m[1][1] > m[2][2]:
        s = sqrt(1 + m[1][1] - m[0][0] - m[2][2]) * 2
        return ((m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, s / 4,
                (m[1][2] + m[2][1]) / s)
    s = sqrt(1 + m[2][2] - m[0][0] - m[1][1]) * 2
    return ((m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
            (m[1][2] + m[2][1]) / s, s / 4)


def quaternion_to_matrix(q):
    w, x, y, z = q
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
        (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
        (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)),
    )


def blend(m1, m2, amount):
    # Normalised linear blend of orientations along the shortest path.
    q1 = matrix_to_quaternion(m1)
    q2 = matrix_to_quaternion(m2)
    if sum(a * b for a, b in zip(q1, q2)) < 0:
        q2 = tuple(-v for v in q2)
    q = tuple(a + (b - a) * amount for a, b in zip(q1, q2))
    length = sqrt(sum(v * v for v in q))
    return quaternion_to_matrix(tuple(v / length for v in q))


def random_axis():
    while True:
        axis = (random.random() - 0.5, random.random() - 0.5, random.random() - 0.5)
        if dot(axis, axis) > 0.01:
            return normalize(axis)


# Fixed tilt so neighbouring faces stay visible when the die is at rest.
VIEW_TILT = mat_mul(axis_rotation((1, 0, 0), 0.35), axis_rotation((0, 1, 0), -0.3))


def project(p):
    scale = DIE_SCALE * CAMERA_DISTANCE / (CAMERA_DISTANCE - p[2])
    return CENTER_X + int(p[0] * scale), CENTER_Y - int(p[1] * scale)


def draw_die(oled, matrix, value=None):
    oled.fill(0)
    for face_value, (normal, corners, centre, _) in FACES.items():
        facing = transform(matrix, normal)[2]
        # Back-face culling: a convex solid hides faces turned away from us.
        if facing <= 0:
            continue

        points = [project(transform(matrix, corner)) for corner in corners]
        for index in range(len(points)):
            x1, y1 = points[index]
            x2, y2 = points[(index + 1) % len(points)]
            oled.line(x1, y1, x2, y2, 1)

        if facing > NUMBER_MIN_FACING:
            label = str(face_value)
            x, y = project(transform(matrix, centre))
            oled.text(label, x - 4 * len(label), y - 4, 1)

    if value is not None:
        oled.text("" + str(value), 0, 0)
    oled.show()


class Die:
    def __init__(self, oled, name):
        self.oled = oled
        self.name = name
        self.value = random.randrange(12) + 1
        self.rolling = False
        self.start = 0
        self.duration = ROLL_MS
        self.from_matrix = FACES[self.value][3]
        self.spin_axes = ((1, 0, 0), (0, 1, 0))
        self.spin_turns = (1, 1)
        self.draw_rest()

    def draw_rest(self):
        draw_die(self.oled, mat_mul(VIEW_TILT, FACES[self.value][3]), self.value)

    def roll(self, now, extra_ms):
        self.from_matrix = FACES[self.value][3]
        self.value = random.randrange(12) + 1
        self.duration = ROLL_MS + extra_ms
        self.start = now
        self.spin_axes = (random_axis(), random_axis())
        # Whole turns, so the spin finishes exactly on the chosen face.
        self.spin_turns = (random.randrange(2) + 1, random.randrange(2) + 2)
        self.rolling = True
        print(self.name, "rolling to", self.value)

    def update(self, now):
        if not self.rolling:
            return
        t = ticks_diff(now, self.start) / self.duration
        if t >= 1:
            self.rolling = False
            self.draw_rest()
            return
        # Everything eases out: the base orientation moves to the target while
        # extra spins around two random axes unwind to nothing.
        remaining = (1 - t) ** 3
        matrix = blend(self.from_matrix, FACES[self.value][3], 1 - remaining)
        for axis, turns in zip(self.spin_axes, self.spin_turns):
            matrix = mat_mul(axis_rotation(axis, TWO_PI * turns * remaining), matrix)
        draw_die(self.oled, mat_mul(VIEW_TILT, matrix))


def find_display(i2c, name):
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on " + name + ": check its wiring")
    address = 0x3C if 0x3C in devices else devices[0]
    print(name, "found I2C device at", hex(address))
    return SSD1306_I2C(WIDTH, HEIGHT, i2c, address)


i2c1 = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
i2c2 = SoftI2C(sda=Pin(12), scl=Pin(13), freq=400000)

dice = (
    Die(find_display(i2c1, "display 1 (GP8/GP9)"), "Die 1"),
    Die(find_display(i2c2, "display 2 (GP12/GP13)"), "Die 2"),
)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
button_was_pressed = False

while True:
    now = ticks_ms()
    # Pull-up input: 0 means pressed. Roll once per press, and not mid-roll.
    button_pressed = button.value() == 0
    if button_pressed and not button_was_pressed:
        if not any(die.rolling for die in dice):
            for index, die in enumerate(dice):
                die.roll(now, index * ROLL_STAGGER_MS)
    button_was_pressed = button_pressed
    for die in dice:
        die.update(now)
    sleep_ms(POLL_MS)
