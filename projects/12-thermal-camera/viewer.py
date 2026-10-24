# Project 12: MLX90640 thermal camera viewer
#
# Runs on the PC (not the Pico). Reads the raw sensor data that main.py (running
# on the Pico) sends over USB serial and shows a live thermal image in a window.
#
#   python projects\12-thermal-camera\viewer.py
#   python projects\12-thermal-camera\viewer.py --port COM4
#   python projects\12-thermal-camera\viewer.py --demo     (fake image, no Pico)
#
# Keys: Space freezes/unfreezes the picture, M mirrors it, C changes the colour
# palette, Esc or Q quits.

import argparse
import math
import random
import struct
import threading
import time
import tkinter as tk

import serial
from serial.tools import list_ports

from mlx90640 import EEPROM_WORDS, HEIGHT, PIXELS, WIDTH, MLX90640Calibration

PICO_VENDOR_ID = 0x2E8A
DEFAULT_MIN_C = 15.0
DEFAULT_MAX_C = 40.0
BAR_TICK_STEP_C = 5
REDRAW_MS = 50
# A stale pixel that differs from its fresh neighbours by this much or more is
# replaced by their average; smaller differences are blended in proportion.
MOTION_FULL_C = 1.5
BAR_PANEL_WIDTH = 150 # Black strip to the right of the picture holding the colour bar
BAR_MARGIN = 12
BAR_WIDTH = 20
BAR_VERTICAL_MARGIN = 14
BOX_HEIGHT = 56 # Box under the colour bar showing the current min and max
FONT_PIXELS = -15 # Negative sizes are pixels, so the layout doesn't depend on display scaling
RESTART_AFTER_S = 4 # Restart the Pico's program if it sends no camera data for this long
SUPER_RESOLUTION = 2
PALETTES = { # Colour stops from cold (0) to hot (1)
    "inferno": [(0.00, (0, 0, 4)), (0.15, (40, 11, 84)), (0.30, (101, 21, 110)),
                (0.45, (159, 42, 99)), (0.60, (212, 72, 66)), (0.75, (245, 125, 21)),
                (0.90, (250, 193, 39)), (1.00, (252, 255, 164))],
    "iron": [(0.00, (0, 0, 0)), (0.20, (32, 0, 110)), (0.40, (150, 0, 120)),
             (0.60, (230, 60, 20)), (0.80, (255, 190, 20)), (1.00, (255, 255, 255))],
    "rainbow": [(0.00, (0, 0, 160)), (0.25, (0, 140, 255)), (0.50, (0, 220, 60)),
                (0.75, (255, 230, 0)), (1.00, (230, 0, 0))],
    "viridis": [(0.00, (68, 1, 84)), (0.25, (59, 82, 139)), (0.50, (33, 144, 140)),
                (0.75, (93, 201, 99)), (1.00, (253, 231, 37))],
    "coolwarm": [(0.00, (40, 70, 200)), (0.50, (235, 235, 235)), (1.00, (200, 40, 40))],
    "whitehot": [(0.00, (0, 0, 0)), (1.00, (255, 255, 255))],
    "blackhot": [(0.00, (255, 255, 255)), (1.00, (0, 0, 0))],
}
DEFAULT_PALETTE = "inferno"

state = {"temps": [20.0] * PIXELS, "ambient": None, "status": "Starting...",
         "frame": 0, "port": None}
lock = threading.Lock()


def build_palette(stops):
    palette = []
    for index in range(256):
        position = index / 255
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if position <= p1:
                f = (position - p0) / (p1 - p0)
                palette.append(bytes(round(a + (b - a) * f) for a, b in zip(c0, c1)))
                break
    return palette


PALETTE_TABLES = {name: build_palette(stops) for name, stops in PALETTES.items()}


def set_status(text):
    with lock:
        state["status"] = text


def publish(temps, ambient):
    with lock:
        state["temps"] = list(temps)
        state["ambient"] = ambient
        state["frame"] += 1


def find_pico_port():
    for port in list_ports.comports():
        if port.vid == PICO_VENDOR_ID:
            return port.device
    return None


def decode_words(text, count):
    data = bytes.fromhex(text)
    if len(data) != count * 2:
        raise ValueError("wrong length")
    return list(struct.unpack(">" + "H" * count, data))


def reduce_checkerboard(temps, fresh):
    """The sensor updates half the pixels (in a chessboard pattern) at a time, so
    when something moves the other half is out of date and shows as a
    checkerboard. Pull each stale pixel towards the average of its fresh
    neighbours, more strongly the more they disagree."""
    result = list(temps)
    for p in range(PIXELS):
        if fresh[p]:
            continue
        row, column = divmod(p, WIDTH)
        neighbours = [temps[r * WIDTH + c]
                      for r, c in ((row - 1, column), (row + 1, column),
                                   (row, column - 1), (row, column + 1))
                      if 0 <= r < HEIGHT and 0 <= c < WIDTH and fresh[r * WIDTH + c]]
        if neighbours:
            average = sum(neighbours) / len(neighbours)
            weight = min(1.0, abs(average - temps[p]) / MOTION_FULL_C)
            result[p] = temps[p] + (average - temps[p]) * weight
    return result


def serial_reader(port_name):
    calibration = None
    temps = [20.0] * PIXELS
    while True:
        name = port_name or find_pico_port()
        if name is None:
            set_status("No Pico found. Plug it in and close other programs using it.")
            time.sleep(1)
            continue
        try:
            with serial.Serial(name, 115200, timeout=1) as link:
                with lock:
                    state["port"] = name
                set_status("Connected to " + name + ". Waiting for the camera...")
                link.write(b"E") # Ask the Pico to send its calibration now
                last_data = time.time()
                last_restart = 0
                while True:
                    line = link.readline().decode(errors="replace").strip()
                    if line.startswith(("EE:", "FR:")):
                        last_data = time.time()
                    elif time.time() - last_data > RESTART_AFTER_S > 0 \
                            and time.time() - last_restart > RESTART_AFTER_S:
                        # Nothing useful received: the Pico is probably stopped at its
                        # prompt. Ctrl+C then Ctrl+D restarts main.py.
                        link.write(b"\x03\x03\x04")
                        last_restart = time.time()
                        set_status("No data from the Pico. Restarting its program...")
                    if not line:
                        continue
                    try:
                        if line.startswith("EE:"):
                            if calibration is None:
                                calibration = MLX90640Calibration(
                                    decode_words(line[3:], EEPROM_WORDS))
                        elif line.startswith("FR:"):
                            if calibration is None:
                                continue # Wait for the next EEPROM line
                            _, sub_page, control, data = line.split(":", 3)
                            frame = decode_words(data, 832) + [int(control, 16), int(sub_page)]
                            ambient = calibration.update(frame, temps)
                            publish(reduce_checkerboard(temps, calibration.fresh), ambient)
                            set_status("")
                        elif line != "E" and not line.startswith(">>>"):
                            set_status(line)
                    except (ValueError, ZeroDivisionError):
                        continue # Corrupt line, wait for the next one
        except (serial.SerialException, OSError):
            with lock:
                state["port"] = None
            set_status("Serial problem. Replug the Pico and close other programs using it.")
            time.sleep(1)


def demo_reader():
    # A warm room with a warm spot and a hand-sized hot blob moving around.
    start = time.time()
    while True:
        t = time.time() - start
        cx = 16 + 10 * math.sin(t * 0.8)
        cy = 12 + 6 * math.cos(t * 0.6)
        temps = []
        for row in range(HEIGHT):
            for column in range(WIDTH):
                hand = 14 * math.exp(-((column - cx) ** 2 + (row - cy) ** 2) / 12)
                spot = 6 * math.exp(-((column - 6) ** 2 + (row - 18) ** 2) / 5)
                temps.append(22 + hand + spot + random.gauss(0, 0.15))
        publish(temps, 23.0)
        set_status("Demo: fake data")
        time.sleep(0.125)


class Viewer:
    def __init__(self, root, scale, mirror, low, high, palette=DEFAULT_PALETTE):
        self.root = root
        self.scale = scale
        self.output_scale = scale * SUPER_RESOLUTION
        self.mirror = mirror
        self.palette_names = list(PALETTES)
        self.palette_name = palette
        self.palette = PALETTE_TABLES[palette]
        self.last_args = None
        self.low = low
        self.high = high
        self.frozen = False
        self.last_frame = -1
        self.shown_status = None
        self.image = None

        # For each output pixel: the two source pixels to blend and by how much.
        self.x_map = self.axis_map(WIDTH)
        self.y_map = self.axis_map(HEIGHT)

        width, height = WIDTH * self.output_scale, HEIGHT * self.output_scale
        self.canvas = tk.Canvas(root, width=width + BAR_PANEL_WIDTH, height=height,
                                highlightthickness=0, bg="black")
        self.canvas.pack()
        self.picture = self.canvas.create_image(0, 0, anchor="nw")
        self.cross = [self.canvas.create_line(0, 0, 0, 0, fill="white") for _ in range(2)]
        self.centre_text = self.canvas.create_text(0, 0, fill="white", anchor="nw",
                                                   font=("Segoe UI", FONT_PIXELS - 1, "bold"))
        self.build_bar(width, height)
        self.label = tk.Label(root, anchor="w", font=("Segoe UI", 9), justify="left")
        self.label.pack(fill="x", padx=4)

        root.bind("<space>", self.toggle_freeze)
        root.bind("m", self.toggle_mirror)
        root.bind("c", self.next_palette)
        root.bind("<Escape>", lambda event: root.destroy())
        root.bind("q", lambda event: root.destroy())
        self.tick()

    def build_bar(self, image_width, height):
        # Fixed colour bar in the black strip to the right of the picture: hot
        # at the top, cold at the bottom, labelled every BAR_TICK_STEP_C degrees.
        # Below it is a box showing the current minimum and maximum.
        left = image_width + BAR_MARGIN
        top = BAR_VERTICAL_MARGIN
        bottom = height - BAR_VERTICAL_MARGIN - BOX_HEIGHT - 20
        bar_height = bottom - top
        self.bar_height = bar_height
        self.bar_picture = self.canvas.create_image(left, top, anchor="nw",
                                                    image=self.make_bar_image())
        self.canvas.create_rectangle(left - 1, top - 1, left + BAR_WIDTH, bottom,
                                     outline="white")

        tick = math.ceil(self.low / BAR_TICK_STEP_C) * BAR_TICK_STEP_C
        while tick <= self.high:
            y = bottom - (tick - self.low) / (self.high - self.low) * bar_height
            self.canvas.create_line(left + BAR_WIDTH, y, left + BAR_WIDTH + 4, y, fill="white")
            self.canvas.create_text(left + BAR_WIDTH + 7, y, fill="white", anchor="w",
                                    text="{:g} °C".format(tick), font=("Segoe UI", FONT_PIXELS))
            tick += BAR_TICK_STEP_C

        box_top = height - BAR_VERTICAL_MARGIN - BOX_HEIGHT
        box_right = image_width + BAR_PANEL_WIDTH - BAR_MARGIN
        self.canvas.create_rectangle(left - 1, box_top, box_right, box_top + BOX_HEIGHT,
                                     outline="white")
        self.box_text = self.canvas.create_text(
            left + 6, box_top + BOX_HEIGHT // 2, fill="white", anchor="w",
            font=("Segoe UI", FONT_PIXELS, "bold"), text="")

    def make_bar_image(self):
        rows = b"".join(self.palette[255 - min(255, i * 256 // self.bar_height)] * BAR_WIDTH
                        for i in range(self.bar_height))
        header = "P6 {} {} 255\n".format(BAR_WIDTH, self.bar_height).encode()
        self.bar_image = tk.PhotoImage(data=header + rows, format="PPM")
        return self.bar_image

    def axis_map(self, size):
        mapping = []
        for out in range(size * self.output_scale):
            source = min(max((out + 0.5) / self.output_scale - 0.5, 0), size - 1)
            low = int(source)
            mapping.append((low, min(low + 1, size - 1), source - low))
        return mapping

    def toggle_freeze(self, _event=None):
        self.frozen = not self.frozen

    def toggle_mirror(self, _event=None):
        self.mirror = not self.mirror
        self.refresh()

    def next_palette(self, _event=None):
        self.set_palette(self.palette_names[
            (self.palette_names.index(self.palette_name) + 1) % len(self.palette_names)])

    def set_palette(self, name):
        self.palette_name = name
        self.palette = PALETTE_TABLES[name]
        self.canvas.itemconfig(self.bar_picture, image=self.make_bar_image())
        self.refresh()

    def refresh(self):
        # Redraw the latest picture now, also while it is frozen.
        if self.last_args:
            self.draw(*self.last_args)

    def tick(self):
        with lock:
            frame = state["frame"]
            temps = state["temps"]
            ambient = state["ambient"]
            status = state["status"]
        if frame != self.last_frame and not self.frozen:
            self.last_frame = frame
            self.last_args = (temps, ambient, status)
            self.draw(temps, ambient, status)
        elif status != self.shown_status:
            self.shown_status = status
            self.label.config(text=status)
        self.root.after(REDRAW_MS, self.tick)

    def draw(self, temps, ambient, status):
        if self.mirror:
            temps = [temps[row * WIDTH + WIDTH - 1 - column]
                     for row in range(HEIGHT) for column in range(WIDTH)]

        low, factor = self.low, 255 / (self.high - self.low)
        self.canvas.itemconfig(self.box_text, text="Max {:.1f} °C\nMin {:.1f} °C".format(
            max(temps), min(temps)))

        # Render at twice the previous resolution, interpolating temperatures
        # along each row first, then between rows.
        blended_rows = []
        for row in range(HEIGHT):
            values = temps[row * WIDTH:(row + 1) * WIDTH]
            blended_rows.append([values[a] + (values[b] - values[a]) * f
                                 for a, b, f in self.x_map])

        scanlines = []
        for a, b, f in self.y_map:
            top, bottom = blended_rows[a], blended_rows[b]
            scanlines.append(b"".join(
                self.palette[min(255, max(0, int((x + (y - x) * f - low) * factor)))]
                for x, y in zip(top, bottom)))
        width, height = WIDTH * self.output_scale, HEIGHT * self.output_scale
        header = "P6 {} {} 255\n".format(width, height).encode()
        self.image = tk.PhotoImage(data=header + b"".join(scanlines), format="PPM")
        self.canvas.itemconfig(self.picture, image=self.image)

        # Crosshair and temperature at the centre of the picture.
        cx, cy = width // 2, height // 2
        centre = temps[(HEIGHT // 2) * WIDTH + WIDTH // 2]
        cross_size = 8 * SUPER_RESOLUTION
        self.canvas.coords(self.cross[0], cx - cross_size, cy, cx + cross_size, cy)
        self.canvas.coords(self.cross[1], cx, cy - cross_size, cx, cy + cross_size)
        self.canvas.coords(self.centre_text, cx + 10 * SUPER_RESOLUTION,
                           cy + 6 * SUPER_RESOLUTION)
        self.canvas.itemconfig(self.centre_text, text="{:.1f} °C".format(centre))

        text = "Centre {:.1f} °C   Palette {}".format(centre, self.palette_name)
        if ambient is not None:
            text += "   Sensor {:.1f} °C".format(ambient)
        if self.frozen:
            text += "   [frozen]"
        if status:
            text += "\n" + status
        self.shown_status = status
        self.label.config(text=text)


def main():
    parser = argparse.ArgumentParser(description="Live MLX90640 thermal camera viewer")
    parser.add_argument("--port", help="serial port of the Pico, for example COM4")
    parser.add_argument("--scale", type=int, default=12,
                        help="window pixels per upsampled pixel (default 12)")
    parser.add_argument("--no-mirror", action="store_true",
                        help="don't flip the picture left to right (flipped by default)")
    parser.add_argument("--min", type=float, default=DEFAULT_MIN_C, dest="min_c",
                        help="bottom of the colour range in °C (default 15)")
    parser.add_argument("--max", type=float, default=DEFAULT_MAX_C, dest="max_c",
                        help="top of the colour range in °C (default 40)")
    parser.add_argument("--palette", choices=list(PALETTES), default=DEFAULT_PALETTE,
                        help="colour palette to start with (default {}); press C to "
                             "change it while running".format(DEFAULT_PALETTE))
    parser.add_argument("--demo", action="store_true", help="fake data, no Pico needed")
    args = parser.parse_args()
    if args.max_c <= args.min_c:
        parser.error("--max must be greater than --min")

    if args.demo:
        target, target_args = demo_reader, ()
    else:
        target, target_args = serial_reader, (args.port,)
    threading.Thread(target=target, args=target_args, daemon=True).start()

    root = tk.Tk()
    root.title("MLX90640 thermal camera")
    root.resizable(False, False)
    Viewer(root, max(1, args.scale), not args.no_mirror, args.min_c, args.max_c, args.palette)
    root.mainloop()


if __name__ == "__main__":
    main()
