# Project 10: Simple latitude and longitude from the Pico-GPS-L76B
#
# The module is plugged onto the Pico and talks over UART0:
# GP0 (Pico TX) and GP1 (Pico RX) at 9600 baud.

from machine import UART, Pin
from time import sleep_ms, ticks_diff, ticks_ms

UART_ID = 0
TX_PIN = 0
RX_PIN = 1
BAUD_RATE = 9600
PRINT_EVERY_MS = 2000
NO_DATA_WARNING_MS = 5000


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
    # $GNGGA,time,lat,N/S,lon,E/W,quality,satellites,...
    fields = line.split(",")
    if len(fields) < 8 or not fields[6] or int(fields[6]) == 0:
        return None
    latitude = to_degrees(fields[2], fields[3])
    longitude = to_degrees(fields[4], fields[5])
    if latitude is None or longitude is None:
        return None
    return latitude, longitude, int(fields[7] or 0)


uart = UART(UART_ID, baudrate=BAUD_RATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
print("Starting. Put the antenna by a window or outdoors.")

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
            print("No data from the module. Check it is plugged on the right way round.")
        elif position:
            print("Position found! Latitude: {:.6f}  Longitude: {:.6f}  "
                  "(using {} satellites)".format(*position))
        elif sentences_seen == 0 or satellites_used is None:
            print("Module is talking, waiting for its first status report...")
        elif sum(in_view.values()) == 0:
            print("Searching for satellites... none seen yet. "
                  "Is the antenna facing the sky?")
        else:
            print("Searching for a fix... {} satellites in view, "
                  "{} locked on (need at least 4)".format(
                      sum(in_view.values()), satellites_used))
    sleep_ms(50)
