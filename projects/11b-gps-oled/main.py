# Project 11b: GPS latitude and longitude on two OLED displays
#
# GPS module (Pico-GPS-L76B, plugged onto the Pico): UART0, GP0/GP1, 9600 baud
# OLED 1 (latitude):  SDA -> GP8,  SCL -> GP9   (hardware I2C0)
# OLED 2 (longitude): SDA -> GP12, SCL -> GP13  (software I2C)
#
# The same status lines are still printed over USB, so the live map from
# projects/11-gps-map/map_server.py works with this program too.
# Upload ssd1306.py to the Pico alongside this file.

from framebuf import FrameBuffer, MONO_HLSB
from machine import I2C, Pin, SoftI2C, UART
from time import sleep_ms, ticks_diff, ticks_ms

from ssd1306 import SSD1306_I2C

UART_ID = 0
TX_PIN = 0
RX_PIN = 1
BAUD_RATE = 9600
PRINT_EVERY_MS = 2000
NO_DATA_WARNING_MS = 5000

WIDTH = 128
HEIGHT = 64
BIG_SCALE = 2
BIG_MAX_CHARS = WIDTH // (8 * BIG_SCALE)


def to_degrees(value, hemisphere):
    # NMEA gives ddmm.mmmm (latitude) or dddmm.mmmm (longitude).
    if not value or not hemisphere:
        return None
    dot = value.index(".")
    degrees = int(value[:dot - 2])
    minutes = float(value[dot - 2:])
    result = degrees + minutes / 60
    return -result if hemisphere in ("S", "W") else result


def checksum_ok(line):
    if not line.startswith("$") or "*" not in line:
        return False
    body, _, given = line[1:].partition("*")
    calculated = 0
    for character in body:
        calculated ^= ord(character)
    return given[:2].upper() == "{:02X}".format(calculated)


def parse_gga(line):
    # $GNGGA,time,lat,N/S,lon,E/W,quality,satellites,hdop,...
    fields = line.split(",")
    if len(fields) < 8 or not fields[6] or int(fields[6]) == 0:
        return None
    latitude = to_degrees(fields[2], fields[3])
    longitude = to_degrees(fields[4], fields[5])
    if latitude is None or longitude is None:
        return None
    hdop = float(fields[8]) if len(fields) > 8 and fields[8] else None
    return latitude, longitude, int(fields[7] or 0), hdop


def find_display(i2c, name):
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on " + name + ": check its wiring")
    address = 0x3C if 0x3C in devices else devices[0]
    print(name, "found I2C device at", hex(address))
    return SSD1306_I2C(WIDTH, HEIGHT, i2c, address)


_glyph = FrameBuffer(bytearray(8), 8, 8, MONO_HLSB)


def draw_big_text(oled, text, x, y, scale):
    # The built-in font is 8x8 pixels, so enlarge each character by drawing
    # every lit pixel as a scale x scale block.
    for index, character in enumerate(text):
        _glyph.fill(0)
        _glyph.text(character, 0, 0, 1)
        for py in range(8):
            for px in range(8):
                if _glyph.pixel(px, py):
                    oled.fill_rect(x + (index * 8 + px) * scale, y + py * scale,
                                   scale, scale, 1)


def big_number(value):
    # Fit the number into the big-text width by trimming decimals; the full
    # six decimals are shown in small text underneath.
    whole = str(int(abs(value)))
    sign = 1 if value < 0 else 0
    decimals = max(0, min(6, BIG_MAX_CHARS - sign - len(whole) - 1))
    return "{:.{}f}".format(value, decimals)


def draw_coordinate(oled, title, value, hemispheres, footer):
    oled.fill(0)
    oled.text(title, 0, 0)
    if value is None:
        oled.text("No fix yet", 0, 20)
    else:
        draw_big_text(oled, big_number(value), 0, 16, BIG_SCALE)
        oled.text("{:.6f} {}".format(value, hemispheres[0 if value >= 0 else 1]),
                  0, 38)
    oled.text(footer, 0, 54)
    oled.show()


def show_position(oled_lat, oled_lon, position, footer):
    latitude = longitude = None
    if position:
        latitude, longitude = position[0], position[1]
    draw_coordinate(oled_lat, "LATITUDE", latitude, "NS", footer)
    draw_coordinate(oled_lon, "LONGITUDE", longitude, "EW", footer)


i2c1 = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
i2c2 = SoftI2C(sda=Pin(12), scl=Pin(13), freq=400000)
oled_lat = find_display(i2c1, "latitude display (GP8/GP9)")
oled_lon = find_display(i2c2, "longitude display (GP12/GP13)")

uart = UART(UART_ID, baudrate=BAUD_RATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
print("Starting. Put the antenna by a window or outdoors.")
show_position(oled_lat, oled_lon, None, "Starting...")

buffer = b""
position = None
satellites_used = None
in_view = {} # Satellites in view, per constellation (GPS, BeiDou, ...)
sentences_seen = 0
last_data = ticks_ms()
last_print = ticks_ms()

while True:
    chunk = uart.read()
    if chunk:
        last_data = ticks_ms()
        buffer += chunk
        # Keep only the unfinished last line in the buffer.
        *lines, buffer = buffer.split(b"\n")
        for raw in lines:
            try:
                line = raw.decode().strip()
            except UnicodeError:
                continue
            if not checksum_ok(line):
                continue
            sentences_seen += 1
            fields = line.partition("*")[0].split(",")
            if line[3:6] == "GGA":
                position = parse_gga(",".join(fields))
                if len(fields) > 7 and fields[7]:
                    satellites_used = int(fields[7])
            elif line[3:6] == "GSV" and len(fields) > 3 and fields[3]:
                in_view[line[1:3]] = int(fields[3])
        if len(buffer) > 200:
            buffer = b""

    now = ticks_ms()
    if ticks_diff(now, last_print) >= PRINT_EVERY_MS:
        last_print = now
        if ticks_diff(now, last_data) > NO_DATA_WARNING_MS:
            message = "No data from the module. Check it is plugged on the right way round."
            footer = "No GPS data"
            print(message)
        elif position:
            latitude, longitude, used, hdop = position
            hdop_text = "n/a" if hdop is None else "{:.1f}".format(hdop)
            print("Position found! Latitude: {:.6f}  Longitude: {:.6f}  "
                  "(using {} satellites, HDOP {})".format(
                      latitude, longitude, used, hdop_text))
            footer = "Sats {} HDOP {}".format(used, hdop_text)
        elif sentences_seen == 0 or satellites_used is None:
            print("Module is talking, waiting for its first status report...")
            footer = "Waiting..."
        elif sum(in_view.values()) == 0:
            print("Searching for satellites... none seen yet. "
                  "Is the antenna facing the sky?")
            footer = "Sats seen: 0"
        else:
            print("Searching for a fix... {} satellites in view, "
                  "{} locked on (need at least 4)".format(
                      sum(in_view.values()), satellites_used))
            footer = "View {} Lock {}".format(sum(in_view.values()), satellites_used)
        show_position(oled_lat, oled_lon, position, footer)
    sleep_ms(50)
