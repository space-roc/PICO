# Project 1: Waveshare Pico-GPS-L76B
#
# The GPS module sends text messages ("NMEA sentences") over a serial (UART)
# connection, about once a second. This program reads them, checks they are
# not corrupted, picks out the position, time, speed and satellite
# information, and prints a summary.
#
# This file is self-contained: it does not need Waveshare's sample library.
#
# NOTE: the pins below are the module's default (UART0). If you have changed
# the module to UART1 (by soldering H1 and H2), change them to match.

from machine import UART, Pin
from time import ticks_diff, ticks_ms

# UART0 on the Pico uses GP0 (TX) and GP1 (RX). The module's default speed
# is 9600 baud (bits per second).
UART_ID = 0
TX_PIN = 0
RX_PIN = 1
BAUD_RATE = 9600

# If nothing arrives for this many milliseconds, warn the user.
NO_DATA_WARNING_MS = 5000

# Descriptions of the "fix quality" number reported in GGA sentences.
FIX_QUALITY = {
    0: "No fix",
    1: "GPS fix",
    2: "Differential GPS fix",
    6: "Estimated",
}


def checksum_ok(line):
    """Return True if the sentence's checksum matches its contents.

    A sentence looks like "$GNRMC,...,D*71". The two hex digits after "*" are
    the XOR of every character between "$" and "*". A mismatch means the line
    was corrupted in transit, so we ignore it.
    """
    if not line.startswith("$") or "*" not in line:
        return False
    # Split into the part between "$" and "*", and the checksum after it.
    body, _, given = line[1:].partition("*")
    calculated = 0
    for ch in body:
        # XOR each character's code into the running total.
        calculated ^= ord(ch)
    try:
        # int(x, 16) reads the two hex digits, e.g. "71" -> 113.
        return calculated == int(given[:2], 16)
    except ValueError:
        return False


def to_degrees(value, hemisphere):
    """Convert NMEA "ddmm.mmmm" text into decimal degrees.

    NMEA gives latitude as degrees followed by minutes, for example
    "2232.4682" means 22 degrees and 32.4682 minutes. We convert that to
    degrees only (22 + 32.4682 / 60). South and West are negative.
    Returns None if the field is empty (no fix yet).
    """
    if not value or "." not in value:
        return None
    # The minutes are always the last two digits before the decimal point.
    dot = value.index(".")
    degrees = int(value[:dot - 2])
    minutes = float(value[dot - 2:])
    decimal = degrees + minutes / 60
    if hemisphere in ("S", "W"):
        decimal = -decimal
    return decimal


def to_float(text):
    """Convert text to a float, or None if it is empty or invalid."""
    try:
        return float(text)
    except ValueError:
        return None


def format_time(text):
    """Turn NMEA time "hhmmss.sss" into "hh:mm:ss" (UTC)."""
    if len(text) < 6:
        return "--:--:--"
    return "{}:{}:{}".format(text[0:2], text[2:4], text[4:6])


def format_date(text):
    """Turn NMEA date "ddmmyy" into "dd/mm/20yy"."""
    if len(text) != 6:
        return "--/--/----"
    return "{}/{}/20{}".format(text[0:2], text[2:4], text[4:6])


def handle_sentence(line, data):
    """Read one valid sentence and store useful values in the 'data' dict.

    Returns True when an RMC sentence was handled. The module sends one RMC
    per update, so we use it as the signal to print a summary.
    """
    fields = line[1:].split("*")[0].split(",")
    # fields[0] is like "GNRMC": two letters for the satellite system
    # (GP = GPS, BD = BeiDou, GN = combined) then the 3-letter sentence type.
    kind = fields[0][2:]

    if kind == "RMC" and len(fields) >= 10:
        # RMC: time, status (A = valid, V = no fix), latitude, longitude,
        # speed in knots, course, date.
        data["time"] = format_time(fields[1])
        data["valid"] = fields[2] == "A"
        data["lat"] = to_degrees(fields[3], fields[4])
        data["lon"] = to_degrees(fields[5], fields[6])
        data["speed_knots"] = to_float(fields[7])
        data["course"] = to_float(fields[8])
        data["date"] = format_date(fields[9])
        return True

    if kind == "GGA" and len(fields) >= 10:
        # GGA: fix quality, number of satellites, HDOP (accuracy: lower is
        # better), and altitude above sea level in metres.
        data["quality"] = int(fields[6]) if fields[6].isdigit() else 0
        data["satellites"] = int(fields[7]) if fields[7].isdigit() else 0
        data["hdop"] = to_float(fields[8])
        data["altitude"] = to_float(fields[9])

    return False


def print_summary(data):
    """Print the latest readings in a human-readable form."""
    print("UTC:", data.get("date", "--/--/----"), data.get("time", "--:--:--"))
    print("Fix:", FIX_QUALITY.get(data.get("quality", 0), "Unknown"),
          "| Satellites in use:", data.get("satellites", 0))

    if data.get("valid") and data.get("lat") is not None:
        lat = data["lat"]
        lon = data["lon"]
        print("Latitude: {:.6f}  Longitude: {:.6f}".format(lat, lon))
        # Paste this line into Google Maps' search box to see where you are.
        print("Google Maps: {:.6f},{:.6f}".format(lat, lon))
        if data.get("altitude") is not None:
            print("Altitude: {:.1f} m  HDOP: {}".format(data["altitude"], data.get("hdop")))
        if data.get("speed_knots") is not None:
            # 1 knot = 1.852 km/h.
            print("Speed: {:.1f} km/h  Course: {}".format(
                data["speed_knots"] * 1.852, data.get("course")))
    else:
        print("Waiting for a position fix. Take the module outdoors or to a")
        print("window with the antenna facing the sky; the first fix can take")
        print("30 seconds or more.")
    print("")


def main():
    # Open the serial connection to the module.
    uart = UART(UART_ID, baudrate=BAUD_RATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN))

    # The latest values we have decoded, shared between sentences.
    data = {}
    last_rx = ticks_ms()
    warned = False

    while True:
        # readline() returns one full line of text, or None if none is ready.
        raw = uart.readline()
        if raw is None:
            # Warn once if the module has gone quiet (bad wiring or power).
            if not warned and ticks_diff(ticks_ms(), last_rx) > NO_DATA_WARNING_MS:
                print("No data from the GPS module. Check it is plugged in the right way round.")
                warned = True
            continue

        last_rx = ticks_ms()
        warned = False

        try:
            # Bytes -> text. Noise can create invalid characters, so be careful.
            line = raw.decode("ascii").strip()
        except UnicodeError:
            continue

        # Skip corrupted or unrelated lines.
        if not checksum_ok(line):
            continue

        # Print a summary each time a new RMC sentence (once per update) arrives.
        if handle_sentence(line, data):
            print_summary(data)


if __name__ == "__main__":
    main()
