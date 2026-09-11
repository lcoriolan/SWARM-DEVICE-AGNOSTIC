# SWARM-DEVICE-AGNOSTIC

A web-based, device-agnostic reference for the SWARM approach: **any browser is a sensor node.**
A node reports where it is and a bearing to a source; the server fuses the nodes into a live
picture with a report-level bearing cross-fix. It runs anywhere a browser and Python do, no app,
no native build, no dedicated hardware.

This repository is a **reference skeleton**. It ships the plain, textbook stages that make the
pipeline run end to end, and it leaves the high-value stages as **clearly marked, empty extension
points** so you can see the architecture and exactly where the advanced capability attaches. The
production PICKET engine is not here.

## The pipeline

```
observation  ->  detect  ->  [classify hook]  ->  crossfix  ->  [coherent hook]  ->  picture
```

| Stage | File | In this repo |
|---|---|---|
| Detection (energy/onset gate) | `pipeline/detect.py`, `web/app.js` | Implemented (textbook) |
| Bearing cross-fix (triangulation) | `pipeline/crossfix.py` | Implemented (textbook) |
| Classifier (what the sound is) | `pipeline/classify.py` | **Extension point, empty** |
| CoHear coherent combining | `pipeline/coherent.py` | **Extension point, empty** |
| On-device multi-mic direction finding | `pipeline/detect.py` (`bearing_from_device`) | **Extension point, empty** |

The extension-point files contain interfaces and documentation only. There is no model, no
coherent-combining engine, no proprietary DSP, and no keys anywhere in this repository. Where a
production module would plug in, the file says so.

## How it works

One server. Devices join over the network and **stream** their observations to it: each browser
posts to `/observe` on a timer while it is detecting, the server keeps the latest report per device
and fuses them for `/api/picture`. There is no app to install and no per-device pairing, a device
just opens the page.

## Run it

Localhost demo (no certificate needed):

```bash
python3 server.py --demo        # spawn 6 synthetic sensor nodes
# open http://127.0.0.1:8080/
```

Real devices over the network need **HTTPS**, because browsers only grant microphone access in a
secure context (localhost is the sole http exemption). Serve with a certificate (a self-signed one
is fine on a LAN; the browser shows a one-time warning):

```bash
# self-signed cert for a LAN, valid for your host/IP
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 90 -subj "/CN=swarm.local"
python3 server.py --host 0.0.0.0 --cert cert.pem --key key.pem
# devices open https://<server-ip>:8080/ , enable the mic, set position + bearing, stream
```

Two or more devices reporting bearings produce a fused fix on the map.

## What it is not

Not the production PICKET system. It stops at report-level cross-fix; it trusts each node's
bearing and edge label verbatim; it has no classifier and no coherent combining. Those, along with
the tuned detector, clip gating, and field hardening, are the production capability and are not
distributed here. This reference exists to make the architecture legible and to show where the
advanced stages attach.

## License

Source-available under the **PolyForm Noncommercial License 1.0.0** (see `LICENSE`) for
evaluation, research, and personal use. Commercial or operational deployment requires a separate
license.
