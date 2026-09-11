# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-11 (MT) | (ET) | (Zulu)
# DESCRIPTION: Cross-device time synchronization, the piece that lets inter-device TDOA (tdoa.py) work
#              across independent devices. It comes in two tiers:
#
#   TIER 1 - COARSE, and IMPLEMENTED (textbook, functional). Each device runs an SNTP-style offset
#            estimate against the server's /time endpoint (see web/app.js: syncClock), correcting for
#            round-trip, so every device reports arrival times on a COMMON clock. This is what makes
#            the reference run live across real browsers, not just the synchronized demo. It is only
#            ~tens of ms accurate, which localizes coarsely (sound travels ~0.34 m/ms).
#
#   TIER 2 - PRECISION, and the EXTENSION POINT (empty here). Recovering SUB-SAMPLE alignment of the
#            same event across devices (e.g. GCC-PHAT on a shared clip plus a per-device clock model)
#            is what turns coarse metres into a tight fix. That precision engine is the production
#            capability and is NOT in this repository; `refine` is where it attaches.

from typing import Optional


def refine(device_id: str, coarse_toa: float, context=None) -> Optional[float]:
    """Upgrade a coarse (SNTP-disciplined) arrival time to a sub-sample-accurate one.

    coarse_toa: the common-clock arrival time from the Tier-1 coarse sync (already usable by TDOA).
    Returns a precision-aligned arrival time, or None if no precision engine is wired in.

    The reference returns None: TDOA runs on the coarse timestamps as-is (functional, low accuracy).
    The production sub-sample alignment engine attaches here and tightens the fix. Not distributed."""
    return None


def precision_available() -> bool:
    """True when the Tier-2 sub-sample alignment engine is wired in. False in the reference (Tier-1
    coarse sync is always active client-side)."""
    return False
