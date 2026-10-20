# Project 11: Live GPS map
#
# Runs on the PC (not the Pico). Reads the lines printed by project 10
# (projects/10-gps-position/main.py, running on the Pico) over USB serial and
# shows the position on a live OpenStreetMap map in your browser.
#
#   python projects\11-gps-map\map_server.py
#   python projects\11-gps-map\map_server.py --port COM4
#   python projects\11-gps-map\map_server.py --demo     (fake walking position)

import argparse
import json
import math
import random
import re
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import serial
from serial.tools import list_ports

POSITION_RE = re.compile(r"Latitude:\s*(-?\d+\.\d+)\s+Longitude:\s*(-?\d+\.\d+)")
HDOP_RE = re.compile(r"HDOP\s+(\d+(?:\.\d+)?)")
PICO_VENDOR_ID = 0x2E8A
MAX_TRAIL_POINTS = 2000
# Rough error in metres per unit of HDOP. HDOP only describes satellite
# geometry, so the accuracy circle is an estimate, not a measured error.
METRES_PER_HDOP = 5.0

# Measured precision: scatter of the recent fixes around their mean position.
# Only meaningful while the module is stationary.
SCATTER_WINDOW_S = 60
SCATTER_MIN_POINTS = 10
MIN_DRIFT_M = 1.0 # Never call a smaller shift of the mean "moving"
MOVING_SIGMAS = 3.5 # Shifts beyond this many standard errors count as moving
EARTH_RADIUS_M = 6371000.0

state = {"lat": None, "lon": None, "hdop": None, "accuracy_m": None,
         "scatter": None, "status": "Starting...", "updated": None,
         "trail": [], "port": None}
recent_fixes = [] # (time, lat, lon) within SCATTER_WINDOW_S
lock = threading.Lock()


def percentile(sorted_values, fraction):
    index = fraction * (len(sorted_values) - 1)
    low = int(index)
    high = min(low + 1, len(sorted_values) - 1)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (index - low)


def mean_point(points):
    return (sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points))


def scatter_estimate(fixes):
    """Precision from the spread of recent fixes, or a reason it isn't valid."""
    if len(fixes) < SCATTER_MIN_POINTS:
        return {"state": "collecting", "points": len(fixes),
                "needed": SCATTER_MIN_POINTS}

    lat0 = sum(f[1] for f in fixes) / len(fixes)
    lon0 = sum(f[2] for f in fixes) / len(fixes)
    metres_per_deg_lat = math.pi * EARTH_RADIUS_M / 180
    metres_per_deg_lon = metres_per_deg_lat * math.cos(math.radians(lat0))
    offsets = [((f[2] - lon0) * metres_per_deg_lon,
                (f[1] - lat0) * metres_per_deg_lat) for f in fixes]

    # Compare the first and second halves of the window: a stationary receiver
    # keeps the same mean, a moving one doesn't. The allowed difference scales
    # with the noise inside each half, so noisy fixes don't look like movement.
    half = len(offsets) // 2
    first_half, second_half = offsets[:half], offsets[half:]
    first_mean = mean_point(first_half)
    second_mean = mean_point(second_half)
    drift = math.hypot(second_mean[0] - first_mean[0], second_mean[1] - first_mean[1])
    within = 0.0
    for points, centre in ((first_half, first_mean), (second_half, second_mean)):
        within += sum((x - centre[0]) ** 2 + (y - centre[1]) ** 2 for x, y in points)
    noise_per_axis = math.sqrt(within / (2 * len(offsets)))
    allowed_drift = max(MIN_DRIFT_M, MOVING_SIGMAS * noise_per_axis * math.sqrt(2 / half))
    if drift > allowed_drift:
        return {"state": "moving", "drift_m": round(drift, 1)}

    radii = sorted(math.hypot(x, y) for x, y in offsets)
    sigma_e = math.sqrt(sum(x * x for x, _ in offsets) / len(offsets))
    sigma_n = math.sqrt(sum(y * y for _, y in offsets) / len(offsets))
    return {"state": "ok", "points": len(fixes), "lat": lat0, "lon": lon0,
            "cep50_m": round(percentile(radii, 0.5), 2),
            "r95_m": round(percentile(radii, 0.95), 2),
            "sigma_east_m": round(sigma_e, 2), "sigma_north_m": round(sigma_n, 2)}


def set_status(text):
    with lock:
        state["status"] = text


def set_position(lat, lon, hdop=None):
    with lock:
        now = time.time()
        state["lat"], state["lon"] = lat, lon
        state["hdop"] = hdop
        state["accuracy_m"] = None if hdop is None else round(hdop * METRES_PER_HDOP, 1)
        state["updated"] = now
        trail = state["trail"]
        if not trail or trail[-1] != [lat, lon]:
            trail.append([lat, lon])
            del trail[:-MAX_TRAIL_POINTS]
        recent_fixes.append((now, lat, lon))
        while recent_fixes[0][0] < now - SCATTER_WINDOW_S:
            recent_fixes.pop(0)
        state["scatter"] = scatter_estimate(recent_fixes)


def handle_line(line):
    print(line)
    match = POSITION_RE.search(line)
    if match:
        hdop_match = HDOP_RE.search(line)
        set_position(float(match.group(1)), float(match.group(2)),
                     float(hdop_match.group(1)) if hdop_match else None)
        set_status(line)
    elif line:
        set_status(line)


def find_port(wanted):
    if wanted:
        return wanted
    for port in list_ports.comports():
        if port.vid == PICO_VENDOR_ID:
            return port.device
    ports = list_ports.comports()
    return ports[0].device if len(ports) == 1 else None


def read_serial(wanted_port):
    while True:
        port = find_port(wanted_port)
        if not port:
            set_status("No Pico found. Plug it in (and close Thonny/mpremote).")
            time.sleep(2)
            continue
        try:
            with serial.Serial(port, 115200, timeout=1) as connection:
                with lock:
                    state["port"] = port
                set_status("Connected to " + port + ", waiting for the Pico...")
                while True:
                    raw = connection.readline()
                    if raw:
                        handle_line(raw.decode(errors="replace").strip())
        except (serial.SerialException, OSError) as error:
            set_status("Serial problem on {}: {}. Retrying...".format(port, error))
            time.sleep(2)


def demo():
    set_status("DEMO: simulated position (no Pico needed)")
    angle = 0.0
    step = 0
    while True:
        # 90 s standing still with GPS-like noise, then 30 s walking.
        walking = step % 120 >= 90
        if walking:
            angle += 0.0004
        noise = 0.00003
        set_position(51.5007 + 0.002 * math.sin(angle) + random.gauss(0, noise),
                     -0.1246 + 0.003 * math.cos(angle) + random.gauss(0, noise * 1.6),
                     1.2 + 0.8 * math.sin(step / 20))
        step += 1
        time.sleep(1)


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Pico GPS map</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body, #map { height: 100%; margin: 0; }
  #info { position: absolute; z-index: 1000; top: 10px; left: 60px; right: 10px;
          max-width: 560px; background: rgba(255,255,255,.92); padding: 8px 12px;
          border-radius: 6px; font: 14px sans-serif; box-shadow: 0 1px 5px #0005; }
  #coords { font-weight: bold; font-size: 16px; }
  #precision { color: #174; margin-top: 2px; }
  #status { color: #555; margin-top: 2px; }
</style></head><body>
<div id="info"><div id="coords">No position yet</div>
  <div id="precision"></div><div id="status"></div></div>
<div id="map"></div>
<script>
  const map = L.map('map').setView([20, 0], 2);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'}).addTo(map);
  let marker = null, circle = null, first = true;
  let r95Circle = null, cepCircle = null;
  const trail = L.polyline([], {color: '#d33', weight: 3}).addTo(map);

  function describeScatter(sc) {
    if (!sc) { return ''; }
    if (sc.state === 'collecting') {
      return 'Measuring precision... ' + sc.points + '/' + sc.needed + ' fixes';
    }
    if (sc.state === 'moving') {
      return 'Moving (' + sc.drift_m + ' m drift): measured precision needs the ' +
             'receiver to stay still';
    }
    return 'Measured over last ' + sc.points + ' fixes: 50% within ' + sc.cep50_m +
           ' m, 95% within ' + sc.r95_m + ' m (\u03c3 E ' + sc.sigma_east_m +
           ' m, N ' + sc.sigma_north_m + ' m)';
  }

  function updateScatter(sc) {
    const ok = sc && sc.state === 'ok';
    if (ok && !r95Circle) {
      r95Circle = L.circle([sc.lat, sc.lon], {radius: 1, color: '#2a2',
        weight: 2, fillOpacity: 0.08}).addTo(map);
      cepCircle = L.circle([sc.lat, sc.lon], {radius: 1, color: '#2a2',
        weight: 2, dashArray: '4 4', fillOpacity: 0.12}).addTo(map);
    }
    if (!r95Circle) { return; }
    for (const c of [r95Circle, cepCircle]) {
      c.setStyle({opacity: ok ? 1 : 0, fillOpacity: ok ? 0.1 : 0});
    }
    if (ok) {
      r95Circle.setLatLng([sc.lat, sc.lon]).setRadius(Math.max(sc.r95_m, 0.1));
      cepCircle.setLatLng([sc.lat, sc.lon]).setRadius(Math.max(sc.cep50_m, 0.1));
    }
  }

  async function refresh() {
    try {
      const s = await (await fetch('/api/state')).json();
      document.getElementById('status').textContent = s.status;
      document.getElementById('precision').textContent = describeScatter(s.scatter);
      updateScatter(s.scatter);
      if (s.lat !== null) {
        const here = [s.lat, s.lon];
        const age = Math.round(Date.now() / 1000 - s.updated);
        const accuracy = s.accuracy_m === null ? '' :
          '  \u00b1' + s.accuracy_m + ' m (HDOP ' + s.hdop + ', estimate)';
        document.getElementById('coords').textContent =
          s.lat.toFixed(6) + ', ' + s.lon.toFixed(6) + accuracy +
          '  (updated ' + age + ' s ago)';
        if (!marker) {
          marker = L.marker(here).addTo(map);
          circle = L.circle(here, {radius: 1, color: '#36f', weight: 1,
                                   fillOpacity: 0.15}).addTo(map);
        } else {
          marker.setLatLng(here);
          circle.setLatLng(here);
        }
        circle.setStyle({opacity: s.accuracy_m === null ? 0 : 1,
                         fillOpacity: s.accuracy_m === null ? 0 : 0.15});
        if (s.accuracy_m !== null) { circle.setRadius(s.accuracy_m); }
        trail.setLatLngs(s.trail);
        if (first) { map.setView(here, 17); first = false; }
        else if (!map.getBounds().pad(-0.2).contains(here)) { map.panTo(here); }
      }
    } catch (e) {
      document.getElementById('status').textContent = 'Lost connection to the server';
    }
  }
  refresh();
  setInterval(refresh, 1000);
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            with lock:
                body = json.dumps(state).encode()
            content_type = "application/json"
        elif self.path in ("/", "/index.html"):
            body = PAGE.encode()
            content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Live map of the Pico GPS position")
    parser.add_argument("--port", help="Pico serial port, e.g. COM4 (default: auto)")
    parser.add_argument("--http-port", type=int, default=8000)
    parser.add_argument("--demo", action="store_true", help="simulate a position")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    target = demo if args.demo else (lambda: read_serial(args.port))
    threading.Thread(target=target, daemon=True).start()

    server = ThreadingHTTPServer(("127.0.0.1", args.http_port), Handler)
    url = "http://127.0.0.1:{}/".format(args.http_port)
    print("Map running at", url, "- press Ctrl+C to stop")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
