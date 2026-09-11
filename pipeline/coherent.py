# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-10 17:59 MDT | 19:59 EDT | 23:59 Zulu
# DESCRIPTION: EXTENSION POINT for CoHear, PICKET's coherent multi-node combining ("many devices ->
#              one big ear"). This is where sample-level alignment (sub-sample GCC-PHAT) and
#              delay-and-sum of the devices' raw clips would attach, turning independent reports into
#              a coherent array with real array gain and tighter localization.
#
#              *** THERE IS NOTHING IN HERE ON PURPOSE. ***
#              The reference server stops at report-level cross-fix (see crossfix.py). The coherent
#              engine, the clip gating and selection, the coincidence-gain weighting, and the field
#              tuning are the production PICKET capability and are not part of this repository. This
#              file exists so the architecture is legible: this is the slot the "cool stuff" plugs into.

from dataclasses import dataclass
from typing import Optional


@dataclass
class CoherentResult:
    """What a real coherent-combining stage would return."""
    fix_x: float
    fix_y: float
    array_gain_db: float
    beamformed_pcm: Optional[bytes] = None


def combine(clips, observers) -> Optional[CoherentResult]:
    """Coherent multi-node combine.

    clips:     per-device raw PCM for one shared event (not collected by this reference).
    observers: the same devices' positions/bearings passed to crossfix.

    The reference does NOT implement this. It returns None, and the server falls back to the
    report-level cross-fix. To wire the production engine, implement this function (align the clips
    to sub-sample accuracy, delay-and-sum, estimate array gain and the fix) and return a
    CoherentResult. That production module is not distributed here.
    """
    return None  # report-level only in the reference; coherent engine attaches here


def available() -> bool:
    """True when a coherent-combining implementation is wired in. False in the reference."""
    return False
