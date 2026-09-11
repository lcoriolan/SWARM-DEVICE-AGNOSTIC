# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-10 17:59 MDT | 19:59 EDT | 23:59 Zulu
# DESCRIPTION: Report-level bearing cross-fix (schoolbook triangulation). Given several observers,
#              each with a planar position and a world bearing to a source, estimate the source
#              position as the least-squares intersection of the bearing lines. This is the plain,
#              public-domain geometry stage; it trusts each observer's bearing verbatim and does no
#              proprietary weighting. Coordinates are a local ENU-style plane in metres.

import math


def _dir(bearing_deg):
    """Unit direction for a bearing measured clockwise from +Y (north). Returns (dx, dy)."""
    t = math.radians(bearing_deg)
    return (math.sin(t), math.cos(t))


def cross_fix(observers):
    """Least-squares intersection of bearing lines.

    observers: list of {"x": float, "y": float, "bearing_deg": float}
    Returns {"x", "y", "residual_m", "n"} or None if under-determined / degenerate.

    Method: each bearing line through observer p with unit direction d contributes the
    perpendicular-projection normal equations (I - d d^T) x = (I - d d^T) p. Summing over
    observers and solving the 2x2 system gives the point closest to all lines. This is standard
    triangulation; there is nothing PICKET-specific in it.
    """
    if len(observers) < 2:
        return None
    # Accumulate the 2x2 system A x = b.
    a11 = a12 = a22 = b1 = b2 = 0.0
    for o in observers:
        dx, dy = _dir(o["bearing_deg"])
        # Perpendicular projector P = I - d d^T (rows of a 2x2 symmetric matrix).
        p11, p12, p22 = 1 - dx * dx, -dx * dy, 1 - dy * dy
        px, py = o["x"], o["y"]
        a11 += p11; a12 += p12; a22 += p22
        b1 += p11 * px + p12 * py
        b2 += p12 * px + p22 * py
    det = a11 * a22 - a12 * a12
    if abs(det) < 1e-9:                       # collinear observers / parallel bearings -> no fix
        return None
    x = (a22 * b1 - a12 * b2) / det
    y = (a11 * b2 - a12 * b1) / det
    # Residual: mean perpendicular distance from the fix to each bearing line (a fit-quality cue).
    resid = 0.0
    for o in observers:
        dxu, dyu = _dir(o["bearing_deg"])
        vx, vy = x - o["x"], y - o["y"]
        along = vx * dxu + vy * dyu           # component along the bearing
        perp = math.hypot(vx - along * dxu, vy - along * dyu)
        resid += perp
    return {"x": x, "y": y, "residual_m": resid / len(observers), "n": len(observers)}
