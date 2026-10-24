# Wi-Fi and network time for the Pico W / Pico 2 W.

import network
import ntptime
import time
from time import sleep_ms, ticks_diff, ticks_ms


def sync(ssid, password, connect_timeout_ms=15000):
    """Connect to Wi-Fi, set the clock (in UTC) from the internet, then switch Wi-Fi off.

    Returns True if the clock was set."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        if not wlan.isconnected():
            wlan.connect(ssid, password)
            start = ticks_ms()
            while not wlan.isconnected() and ticks_diff(ticks_ms(), start) < connect_timeout_ms:
                sleep_ms(200)
        if not wlan.isconnected():
            print("Wi-Fi: could not connect")
            return False
        for _ in range(3):
            try:
                ntptime.settime()
                print("Time set from the internet")
                return True
            except OSError:
                sleep_ms(500)
        print("Wi-Fi: could not reach the time server")
        return False
    finally:
        wlan.disconnect()
        wlan.active(False)


def _last_sunday(year, month):
    # March and October both have 31 days
    weekday = time.localtime(time.mktime((year, month, 31, 0, 0, 0, 0, 0)))[6]
    return 31 - (weekday + 1) % 7


def local_time(utc_offset_hours=0, uk_daylight_saving=True):
    """The local time as a localtime() tuple.

    With uk_daylight_saving, one hour is added from 01:00 UTC on the last Sunday
    of March to 01:00 UTC on the last Sunday of October."""
    utc = time.time()
    offset = utc_offset_hours * 3600
    if uk_daylight_saving:
        year = time.localtime(utc)[0]
        start = time.mktime((year, 3, _last_sunday(year, 3), 1, 0, 0, 0, 0))
        end = time.mktime((year, 10, _last_sunday(year, 10), 1, 0, 0, 0, 0))
        if start <= utc < end:
            offset += 3600
    return time.localtime(utc + int(offset))
