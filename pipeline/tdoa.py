# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-11 (MT) | (ET) | (Zulu)
# DESCRIPTION: Inter-device TDOA localization, the device-agnostic way to place a source when no single
#              device can form a bearing. A browser exposes one microphone, not the two sample-locked
#              channels a bearing needs, but it CAN timestamp when it hears an event. Across several
#              devices those arrival times differ by the extra travel distance, and the time-difference-
#              of-arrival (TDOA) between devices multilaterates the source. One mic per device is enough;
#              the array is the devices, not the mics.
#
#              This file implements the plain, textbook solver: given device positions and arrival times
#              on a COMMON clock, least-squares (Gauss-Newton) for the source position. What it does NOT
#              do is the hard part, disciplining the devices onto that common clock and recovering the
#              sub-sample alignment across independent browsers. Accurate cross-device time sync (e.g.
#              GCC-PHAT on a shared event, clock-model estimation) is the CoHear extension point; see
#              coherent.py. The reference assumes the timestamps it is given are already aligned.

import math

C_SOUND = 343.0  # m/s


def _solve3(a, b):
    """Solve a 3x3 linear system a x = b by Gaussian elimination. Returns None if singular."""
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        for r in range(3):
            if r == col:
                continue
            f = m[r][col] / m[col][col]
            for c in range(col, 4):
                m[r][c] -= f * m[col][c]
    return [m[i][3] / m[i][i] for i in range(3)]


def tdoa_fix(observers, iters=12):
    """Least-squares source localization from synchronized arrival times.

    observers: list of {"x", "y", "toa"} with toa in seconds on a COMMON clock. Needs >= 3.
    Returns {"x", "y", "residual_m", "n"} or None if under-determined / non-convergent.

    Model: for each device i, |source - p_i| = c * (toa_i - t0), where t0 is the (unknown) emission
    time. Unknowns are (sx, sy, t0). We Gauss-Newton from the device centroid. This is standard
    multilateration; the only PICKET-specific value is in getting clean, aligned toa values, which is
    the extension point, not this geometry.
    """
    if len(observers) < 3:
        return None
    xs = [o["x"] for o in observers]
    ys = [o["y"] for o in observers]
    ts = [o["toa"] for o in observers]
    # Initial guess: centroid for position, and an emission time a touch before the earliest arrival.
    sx, sy = sum(xs) / len(xs), sum(ys) / len(ys)
    t0 = min(ts) - 0.05
    for _ in range(iters):
        # Build normal equations J^T J g = J^T r for the 3 unknowns.
        JTJ = [[0.0] * 3 for _ in range(3)]
        JTr = [0.0, 0.0, 0.0]
        for x, y, t in zip(xs, ys, ts):
            r = math.hypot(sx - x, sy - y)
            if r < 1e-6:
                r = 1e-6
            resid = r - C_SOUND * (t - t0)              # want this = 0
            jx, jy, jt = (sx - x) / r, (sy - y) / r, C_SOUND   # d resid / d(sx,sy,t0)
            jac = (jx, jy, jt)
            for a in range(3):
                JTr[a] += jac[a] * resid
                for b in range(3):
                    JTJ[a][b] += jac[a] * jac[b]
        step = _solve3(JTJ, JTr)
        if step is None:
            return None
        sx -= step[0]; sy -= step[1]; t0 -= step[2]
        if abs(step[0]) + abs(step[1]) < 1e-4:
            break
    # Residual: RMS of the range-vs-time mismatch across devices (a fit-quality cue, in metres).
    ss = 0.0
    for x, y, t in zip(xs, ys, ts):
        ss += (math.hypot(sx - x, sy - y) - C_SOUND * (t - t0)) ** 2
    return {"x": sx, "y": sy, "residual_m": math.sqrt(ss / len(observers)), "n": len(observers)}
