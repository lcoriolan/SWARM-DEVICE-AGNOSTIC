# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-10 17:59 MDT | 19:59 EDT | 23:59 Zulu
# DESCRIPTION: Plain detection reference plus the direction-finding extension point. The reference
#              detection is a textbook energy gate (the sensor client does the same thing in the
#              browser). Real multi-mic direction finding, onset time-difference-of-arrival, and the
#              tuned detector are the production PICKET capability and attach at the marked hook.


def energy_gate(rms, floor, snr_db=6.0):
    """Textbook detection: fire when the level clears the noise floor by an SNR margin.

    rms:      event level (same linear units as floor).
    floor:    current ambient level estimate.
    snr_db:   required margin above the floor.

    Detection range is set by the floor: a louder environment raises `floor` and shrinks range.
    This is the plain gate; the production detector adds spectral CFAR, tonal tracking, and tuning.
    """
    if floor <= 0:
        return False
    return 20.0 * _log10(rms / floor) >= snr_db


def bearing_from_device(clips):
    """EXTENSION POINT: multi-mic direction finding.

    *** NOT IMPLEMENTED IN THE REFERENCE. ***
    A single browser mic cannot form a bearing; real DF needs two or more sample-locked channels
    (GCC-PHAT / SRP-PHAT) and lives in the production on-device engine, which is not distributed
    here. In this reference, bearings arrive from the sensor client (device heading or a set value)
    and are cross-fixed by crossfix.py. This is the slot where on-device DF plugs in.
    """
    return None


def _log10(x):
    import math
    return math.log10(x) if x > 0 else -99.0
