# SWARM-DEVICE-AGNOSTIC

A web-based, device-agnostic reference for the acoustic SWARM approach: **any device with a microphone and browser is a sensor node.**
A node reports where it is and a bearing to a source; the server fuses the nodes into a live
picture with a report-level bearing cross-fix. It runs anywhere a browser and Python do, no app,
no native build, no dedicated hardware.

This repository is a **reference skeleton**. It ships the plain, textbook stages that make the
pipeline run end to end, and it leaves the high-value stages as **clearly marked, empty extension
points** so you can see the architecture and exactly where the advanced capability attaches. The
production PICKET engine is not here.

## What you get here

Runnable today, straight from this repository: turn any device with a microphone and a browser into
an acoustic sensor node. Each node detects a sound and reports a bearing; the server fuses the nodes
into a **live map picture** with a report-level bearing cross-fix. It runs anywhere a browser and
Python do, with no app, no native build, and no dedicated hardware, and it scales by simply adding
devices, more nodes widen the coverage and tighten the fix.

The wire is kept deliberately light: a node streams a compact detection record and an **ACLIP, a
lightweight acoustic signature** (envelope and peak, an averaged spectrum, a harmonic profile),
never raw audio. That keeps alerting and correlation fast as the fleet grows, and a full clip is
only ever pulled selectively, on cue. This is the plain, open reference, real end to end, textbook
DSP, and no secrets.

## What our secret sauce adds

Fill the empty hooks with the production engine and the same architecture, the same devices
streaming to one server, becomes far more than crossed bearings:

- **CoHear coherent combining** (the `coherent` hook). Instead of only crossing per-device reports,
  it aligns the nodes' raw audio to sub-sample accuracy and combines it into one coherent array, so
  a source too faint for any single device to call rises out of the noise. Array gain grows with the
  node count (about `10*log10(N)` dB), which in the weak-signal regime stretches detection range by
  roughly `sqrt(N)`, and the alignment needs no shared hardware clock, so it works across ordinary,
  software-clocked devices. In simulation the gain tracks the ideal within about 0.1 dB and
  localization reaches sub-meter.
- **Classification** (the `classify` hook). An on-device model that says what a sound *is*, drone,
  aircraft, vehicle, voice, gunfire, explosion, not merely that something is there.
- **Direction finding and elevation** (the DF hook). Real multi-mic bearing, including up/down, so a
  low, terrain-hugging FPV reads differently from one passing overhead.
- **Self-localization.** Nodes that solve their own positions from the sounds they share, so a
  deployment needs no survey and can keep placing itself even with GPS denied.

Put those together and a swarm of commodity devices becomes a passive, distributed **acoustic
battlefield situational-awareness** mesh, hearing and placing drones, gunfire, and movers on the
map, that holds when GPS and comms are jammed and gives an adversary nothing to detect or jam.
Because it is coherent, more devices mean both longer reach and a tighter fix at once. This
repository is the doorway; that capability is what plugs into these hooks. The performance figures
above are modeled and simulation-validated, not field guarantees, and range depends on the source
and the ambient noise floor. More at https://github.com/lcoriolan/PICKETCUAS-SWARM.

**Want to see the rest?** The full capability behind these hooks, coherent combining, the
classifier, direction finding, and self-localization, can be shown running, the same as with the
ATAK plugins. Open an issue on this repository (a "capability demo request") and we are glad to
demo it or discuss access.

## The distributed-device math

Three laws govern a distributed acoustic array, and they are why device count matters:

- **Array gain** grows as `10*log10(N)` dB with N coherently combined devices.
- **Detection range** stretches as about `sqrt(N)` in the weak-signal regime, so every 4x more
  devices roughly doubles the range on a faint source.
- **Coverage** scales with N at fixed spacing: more devices simply watch more ground, and dense
  spacing (nodes a hundred metres or so apart) means any source is heard by several at once.

From a single device's ~80 m bare range against a quiet small drone:

| Devices (N) | Array gain | Range vs 1 | Reach on a quiet drone* |
|---|---|---|---|
| 1 | 0 dB | 1x | ~80 m |
| 4 | +6.0 dB | 2x | ~160 m |
| 12 | +10.8 dB | 3.5x | ~280 m |
| 24 | +13.8 dB | 4.9x | ~390 m |
| 48 | +16.8 dB | 6.9x | ~555 m |
| ~96 | +19.8 dB | 10x | ~785 m |

Returns diminish past ~100 coherent devices (`sqrt(N)` needs 4x the devices to double range again),
and only devices close enough to hear an event combine coherently for it, so beyond a local cluster
more devices add **coverage**, not **range** on a single source. That is also the answer to "how
many devices equal a dedicated system": at scale, enough commodity devices approximate a
purpose-built array, the reach just follows `sqrt(N)`.

\* Modeled projection, not hardware-measured, and **set by the ambient noise floor**: every +6 dB of
ambient roughly halves the range (wind alone adds ~10-20 dB). Uses the `10*log10(N)` / `sqrt(N)`
law (validated in simulation through 12 nodes) on a modeled ~80 m single-device baseline. Real
range depends on the source, wind, and terrain.

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
