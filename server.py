#!/usr/bin/env python3
# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-10 17:59 MDT | 19:59 EDT | 23:59 Zulu
# DESCRIPTION: A neutered, web-based reference fusion server for the SWARM device-agnostic approach.
#              Any browser can act as a sensor node (see web/): it posts an observation (its position
#              and a world bearing to a source), and this server fuses the observations into a live
#              picture with a report-level bearing cross-fix. It serves the web UI and a JSON picture.
#
#              What it is NOT: the production PICKET engine. It stops at the plain stages in
#              pipeline/ and calls the coherent/classifier stages through their extension points,
#              which are empty in this repository (see pipeline/coherent.py, pipeline/classify.py).
#              Standard library only; no external dependencies, no keys, no model.
#
# USAGE:       python3 server.py                 # http://127.0.0.1:8080 (localhost demo)
#              python3 server.py --demo          # also spawn synthetic sensor nodes so it runs solo
#              python3 server.py --cert c.pem --key k.pem --host 0.0.0.0   # HTTPS for real devices
#
# ARCHITECTURE: one server; devices join over the network and STREAM observations to it (each browser
#   posts to /observe on a timer while it is detecting; the server holds the latest per device and
#   fuses them for /api/picture). Real remote devices must connect over HTTPS: browsers only grant
#   mic access in a secure context, so off-localhost you must run with --cert/--key (a self-signed
#   cert is fine on a LAN; the browser will show a one-time warning).

import argparse
import json
import math
import os
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pipeline import crossfix, classify, coherent

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
OBSERVER_TTL_S = 10.0                          # an observation older than this drops out of the picture

# ---- in-memory state (one latest observation per device) --------------------------------------
_lock = threading.Lock()
_observers = {}                                # device_id -> observation dict (+ received monotonic ts)


def ingest(obs):
    """Store the latest observation for a device. Missing fields are tolerated."""
    did = str(obs.get("device_id", "anon"))
    with _lock:
        _observers[did] = {
            "device_id": did,
            "x": float(obs.get("x", 0.0)),
            "y": float(obs.get("y", 0.0)),
            "bearing_deg": (None if obs.get("bearing_deg") is None else float(obs["bearing_deg"])),
            "edge_label": obs.get("edge_label"),
            "rx": time.monotonic(),
        }


def picture():
    """Fuse the currently-active observers into a picture dict for the UI."""
    now = time.monotonic()
    with _lock:
        active = [o for o in _observers.values() if now - o["rx"] <= OBSERVER_TTL_S]
    # Report-level cross-fix over observers that actually carry a bearing.
    with_bearing = [o for o in active if o["bearing_deg"] is not None]
    fix = crossfix.cross_fix(with_bearing) if len(with_bearing) >= 2 else None
    # Coherent stage is an extension point; in this reference it is not wired, so we note that.
    coh = coherent.combine(clips=None, observers=with_bearing)  # returns None here by design
    # Classifier is an extension point; pass the edge labels through.
    labels = [classify.classify(features=None, edge_label=o.get("edge_label")) for o in active]
    return {
        "observers": [
            {"device_id": o["device_id"], "x": o["x"], "y": o["y"], "bearing_deg": o["bearing_deg"],
             "edge_label": o["edge_label"]}
            for o in active
        ],
        "fix": fix,
        "labels": labels,
        "stages": {
            "crossfix": "report-level (reference)",
            "coherent": ("wired" if coherent.available() else "extension point - not in this repo"),
            "classifier": ("wired" if classify.available() else "extension point - not in this repo"),
        },
        "coherent_result": (None if coh is None else coh.__dict__),
    }


# ---- HTTP -------------------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _static(self, name, ctype):
        path = os.path.join(WEB_DIR, name)
        if not os.path.isfile(path):
            return self._send(404, "not found", "text/plain")
        with open(path, "rb") as f:
            self._send(200, f.read(), ctype)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._static("index.html", "text/html; charset=utf-8")
        if self.path == "/app.js":
            return self._static("app.js", "text/javascript")
        if self.path == "/style.css":
            return self._static("style.css", "text/css")
        if self.path == "/api/picture":
            return self._send(200, json.dumps(picture()))
        return self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/observe":
            return self._send(404, "not found", "text/plain")
        try:
            n = int(self.headers.get("Content-Length", 0))
            obs = json.loads(self.rfile.read(n) or b"{}")
            ingest(obs)
            self._send(200, json.dumps({"ok": True}))
        except Exception as e:
            self._send(400, json.dumps({"ok": False, "error": str(e)}))

    def log_message(self, *_):            # keep the console quiet
        pass


# ---- synthetic demo ---------------------------------------------------------------------------
def _demo_thread():
    """Spawn virtual sensor nodes around a moving source and feed observations, so the server runs
    with no real devices. Pure geometry: each node reports a (noisy) true bearing to the source."""
    n = 6
    ring = [(60 * math.cos(2 * math.pi * i / n), 60 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    step = 0
    # A tiny deterministic pseudo-noise (no RNG needed): vary by index and step.
    while True:
        sx = 40 * math.cos(step / 15.0)       # source wanders on a slow circle
        sy = 40 * math.sin(step / 15.0)
        for i, (x, y) in enumerate(ring):
            true_b = math.degrees(math.atan2(sx - x, sy - y)) % 360.0   # clockwise from +Y
            jitter = 2.0 * math.sin(step / 3.0 + i)                     # +/- 2 deg wobble
            ingest({"device_id": f"demo-{i}", "x": x, "y": y,
                    "bearing_deg": (true_b + jitter) % 360.0, "edge_label": "drone"})
        step += 1
        time.sleep(0.5)


def main():
    ap = argparse.ArgumentParser(description="SWARM device-agnostic web reference server.")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 for LAN devices)")
    ap.add_argument("--cert", help="TLS certificate (PEM); enables HTTPS for real remote devices")
    ap.add_argument("--key", help="TLS private key (PEM); pair with --cert")
    ap.add_argument("--demo", action="store_true", help="spawn synthetic sensor nodes")
    args = ap.parse_args()
    if args.demo:
        threading.Thread(target=_demo_thread, daemon=True).start()
        print("demo: 6 synthetic sensor nodes feeding observations")
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    scheme = "http"
    if args.cert and args.key:
        # Wrap the listening socket in TLS so browsers off-localhost will grant mic access.
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=args.cert, keyfile=args.key)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        scheme = "https"
    elif args.host not in ("127.0.0.1", "localhost"):
        print("WARNING: serving plain HTTP off localhost - browsers will refuse mic access. "
              "Pass --cert/--key for HTTPS.")
    print(f"SWARM device-agnostic reference on {scheme}://{args.host}:{args.port}/  "
          f"(coherent + classifier stages are empty extension points)")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
