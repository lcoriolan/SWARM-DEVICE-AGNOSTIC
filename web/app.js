// PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
// CREATED:     2026-09-10 17:59 MDT | 19:59 EDT | 23:59 Zulu
// DESCRIPTION: Browser sensor client + picture renderer. The sensor path is textbook only: mic RMS
//   via WebAudio, a slow noise-floor tracker, and an energy gate (the same plain detection as
//   pipeline/detect.py). It posts observations to /observe. The picture path polls /api/picture and
//   draws observers, their bearings, and the fused fix. No external libraries.

const $ = (id) => document.getElementById(id);

// ---- sensor: mic level + textbook onset gate --------------------------------------------------
let floor = 0.02, level = 0, detecting = false;

async function enableMic() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const src = ctx.createMediaStreamSource(stream);
    const an = ctx.createAnalyser(); an.fftSize = 1024;
    src.connect(an);
    const buf = new Float32Array(an.fftSize);
    setInterval(() => {
      an.getFloatTimeDomainData(buf);
      let s = 0; for (const v of buf) s += v * v;
      level = Math.sqrt(s / buf.length);          // RMS of the frame
      floor = 0.995 * floor + 0.005 * level;      // slow floor tracker (ambient estimate)
      // Energy gate: fire when the level clears the floor by ~6 dB (same idea as detect.py).
      detecting = level > 0 && (20 * Math.log10(level / (floor + 1e-9)) >= 6);
      $("level").style.width = Math.min(100, level * 400) + "%";
      $("detect").textContent = detecting ? "DETECT" : "idle";
      $("detect").className = "badge" + (detecting ? " on" : "");
      if (detecting && $("auto").checked) send();
    }, 100);
    $("mic").textContent = "mic on";
    $("mic").disabled = true;
  } catch (e) {
    $("detect").textContent = "mic denied";
  }
}

let gpsOrigin = null;               // first GPS fix becomes the local-plane origin
let clockOffset = 0;                // seconds to add to this device's clock to reach the server clock

// Coarse SNTP-style clock discipline: ping /time a few times and estimate the offset from this
// device's clock to the server's, correcting for round-trip. This is the textbook part that lets
// independent browsers report arrival times on a COMMON clock so inter-device TDOA runs live. It is
// only ~tens of ms accurate; the sub-sample precision alignment that tightens it is the extension
// point (pipeline/timesync.py), not in this repo.
async function syncClock() {
  const samples = [];
  for (let i = 0; i < 5; i++) {
    const t0 = Date.now() / 1000;
    try {
      const r = await (await fetch("/time")).json();
      const t3 = Date.now() / 1000, rtt = t3 - t0;
      samples.push(r.server_time + rtt / 2 - t3);   // offset, assuming symmetric round-trip
    } catch (e) { /* server not up */ }
  }
  if (samples.length) { samples.sort((a, b) => a - b); clockOffset = samples[samples.length >> 1]; }
}
syncClock();
setInterval(syncClock, 30000);      // re-sync periodically to track drift

function send() {
  const obs = {
    device_id: $("did").value || "browser-1",
    x: parseFloat($("px").value) || 0,
    y: parseFloat($("py").value) || 0,
    // Arrival timestamp for inter-device TDOA, put on the shared server clock via the coarse sync
    // above. Sub-sample precision alignment (which tightens the fix) is the extension point.
    toa: Date.now() / 1000 + clockOffset,
    edge_label: $("lbl").value,
  };
  if ($("usebrg").checked) obs.bearing_deg = parseFloat($("brg").value) || 0;  // bearing is optional
  fetch("/observe", { method: "POST", body: JSON.stringify(obs) }).catch(() => {});
}

// GPS: fill this device's position from browser geolocation (with the user's consent).
$("gps").onclick = () => {
  if (!navigator.geolocation) { $("gps").textContent = "no GPS"; return; }
  navigator.geolocation.getCurrentPosition((pos) => {
    const la = pos.coords.latitude, lo = pos.coords.longitude;
    if (!gpsOrigin) gpsOrigin = { la, lo };                       // first fix = local origin (0,0)
    // Equirectangular approximation to a local metres plane around the origin.
    const x = (lo - gpsOrigin.lo) * 111320 * Math.cos(gpsOrigin.la * Math.PI / 180);
    const y = (la - gpsOrigin.la) * 111320;
    $("px").value = x.toFixed(1); $("py").value = y.toFixed(1);
    $("gps").textContent = "GPS set";
  }, () => { $("gps").textContent = "GPS denied"; });
};

$("mic").onclick = enableMic;
$("send").onclick = send;
$("brg").oninput = () => { $("brgv").textContent = $("brg").value; };

// ---- picture: poll /api/picture and draw ------------------------------------------------------
const cv = $("map"), g = cv.getContext("2d");
const W = cv.width, H = cv.height, SCALE = 3.0;             // px per metre
const toPx = (x, y) => [W / 2 + x * SCALE, H / 2 - y * SCALE]; // +Y is up (north)

function draw(pic) {
  g.clearRect(0, 0, W, H);
  // grid + origin
  g.strokeStyle = "#1e2a33"; g.lineWidth = 1;
  for (let r = 20; r <= 80; r += 20) { g.beginPath(); g.arc(W / 2, H / 2, r * SCALE, 0, 7); g.stroke(); }
  // bearing rays + observers
  for (const o of pic.observers) {
    const [ox, oy] = toPx(o.x, o.y);
    if (o.bearing_deg !== null) {
      const t = o.bearing_deg * Math.PI / 180;
      const ex = ox + Math.sin(t) * 240, ey = oy - Math.cos(t) * 240;
      g.strokeStyle = "rgba(120,180,220,0.35)"; g.beginPath();
      g.moveTo(ox, oy); g.lineTo(ex, ey); g.stroke();
    }
    g.fillStyle = "#6fd3ff"; g.beginPath(); g.arc(ox, oy, 4, 0, 7); g.fill();
    g.fillStyle = "#7f97a5"; g.font = "10px system-ui"; g.fillText(o.device_id, ox + 6, oy - 6);
  }
  // fused fix
  if (pic.fix) {
    const [fx, fy] = toPx(pic.fix.x, pic.fix.y);
    g.strokeStyle = "#ffb020"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(fx - 8, fy); g.lineTo(fx + 8, fy);
    g.moveTo(fx, fy - 8); g.lineTo(fx, fy + 8); g.stroke();
    g.beginPath(); g.arc(fx, fy, 11, 0, 7); g.stroke();
  }
}

async function poll() {
  try {
    const pic = await (await fetch("/api/picture")).json();
    draw(pic);
    $("stages").textContent =
      `crossfix: ${pic.stages.crossfix} | coherent: ${pic.stages.coherent} | classifier: ${pic.stages.classifier}`;
    const f = pic.fix;
    $("readout").textContent = f
      ? `fused fix: (${f.x.toFixed(1)}, ${f.y.toFixed(1)}) m from ${f.n} bearings, residual ${f.residual_m.toFixed(1)} m`
      : `${pic.observers.length} observer(s); need >=2 bearings for a fix`;
  } catch (e) { /* server not up yet */ }
}
setInterval(poll, 500);
poll();
