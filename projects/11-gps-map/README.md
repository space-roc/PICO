# Project 11: Live GPS map

Show where the Pico-GPS-L76B is on a live OpenStreetMap map in your browser,
with a red trail of where it has been. This project is self-contained and has
two parts:

- `main.py` runs on the **Pico**. It reads the GPS module and prints its status
  and position over USB.
- `map_server.py` runs on the **PC**. It reads that output and serves the map.

## Set up

1. Upload this project's `main.py` to the Pico so it runs on its own:

   ```powershell
   python -m mpremote connect auto fs cp projects\11-gps-map\main.py :main.py + reset
   ```

2. Close anything else using the Pico's serial port (Thonny, `mpremote`, the
   VS Code Pico tasks). Only one program can use it at a time.
3. Start the map from the repository root:

   ```powershell
   python projects\11-gps-map\map_server.py
   ```

   Your browser opens at <http://127.0.0.1:8000/>. Stop it with Ctrl+C.

The map needs an internet connection for the map tiles. `pyserial` is needed on
the PC; it's installed with `mpremote`, or use `python -m pip install pyserial`.

## What you'll see

- The top box shows the coordinates, an estimated accuracy (such as `±6 m`),
  how long ago they updated, and the Pico's latest status message (such as
  "Searching for a fix... 8 satellites in view").
- Until the module has a fix there's no marker. Take the module outdoors or to
  a window. Once it has a fix, a marker appears and the map follows it. A blue
  circle around the marker shows the estimated accuracy.

## About the accuracy circles

There are two kinds of precision estimate on the map.

**1. HDOP estimate (blue circle).** The module reports **HDOP**, a number for
how good the satellite geometry is: under 1 is excellent, 1 to 2 good, 2 to 5
moderate, and above 5 poor. The circle's radius is HDOP × 5 m
(`METRES_PER_HDOP` in `map_server.py`). This is a rough estimate only. The
L76B doesn't send the `GST` sentence that carries a true measured error, and
HDOP ignores things like buildings and reflections.

**2. Measured scatter (green circles).** The server keeps the fixes from the
last 60 seconds (`SCATTER_WINDOW_S`) and measures how far they spread around
their mean position:

- **Dashed circle / "50% within":** CEP50, the radius holding half of the fixes.
- **Solid circle / "95% within":** R95, the radius holding 95% of the fixes.
- **σ E / σ N:** the standard deviation in metres east and north.

Notes on the measured figures:

- They're only shown while the receiver is **stationary**. If the average
  position in the first and second halves of the window differ by more than
  noise explains (at least 1 m, see `MIN_DRIFT_M` and `MOVING_SIGMAS`) the box
  says "Moving", because real movement would look like noise.
- They need at least 10 fixes (`SCATTER_MIN_POINTS`), about 10 seconds.
- They measure **repeatability**, not true accuracy. A constant offset, such
  as an atmospheric delay or reflections off a building, doesn't show up, and
  consecutive fixes are correlated, so the real error is usually larger than
  the scatter suggests.
- `--demo` simulates 90 seconds standing still with GPS-like noise, then 30
  seconds walking, so you can see both states.

## Options

```powershell
python projects\11-gps-map\map_server.py --port COM4     # choose the port
python projects\11-gps-map\map_server.py --http-port 8080
python projects\11-gps-map\map_server.py --demo          # fake position, no Pico
```

## How it works

- A background thread reads lines from the Pico's serial port (auto-detected
  by the Pico's USB vendor ID) and picks out `Latitude: ... Longitude: ...`.
  It reconnects if the Pico is unplugged.
- A small built-in web server (Python standard library) answers `/api/state`
  with the latest position, status and trail. The page asks for it every
  second and moves the marker, using [Leaflet](https://leafletjs.com/).

## Troubleshooting

- **"No Pico found" or "Serial problem":** replug the Pico and close other
  programs using it.
- **Connected but no data:** make sure this project's `main.py` is on the Pico.
  Unplug and replug it, or run the `reset` command above.
- **Blank grey map:** check your internet connection.
