# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-10 17:59 MDT | 19:59 EDT | 23:59 Zulu
# DESCRIPTION: EXTENSION POINT for the acoustic classifier (the model that decides what a sound IS:
#              drone, aircraft, vehicle, voice, gunfire, explosion, background).
#
#              *** THERE IS NO MODEL IN HERE ON PURPOSE. ***
#              The reference trusts whatever edge label the sensor client already sent, and otherwise
#              reports "unknown". The trained model and its weights are the production PICKET
#              capability and are not part of this repository. This file marks where the classifier
#              attaches so the pipeline is legible.

CLASSES = ("background", "drone", "aircraft", "vehicle", "voice", "gunfire", "explosion")


def classify(features, edge_label=None):
    """Return a class label + confidence for an event.

    features:   whatever the sensor extracted (not used by the reference).
    edge_label: an optional label the sensor client already decided on the device.

    The reference passes the edge label through verbatim (or "unknown"); it runs no model. To wire
    the production classifier, load the model here and return its label + confidence. That model is
    not distributed in this repository.
    """
    if edge_label in CLASSES:
        return {"label": edge_label, "confidence": None, "source": "edge (passthrough)"}
    return {"label": "unknown", "confidence": None, "source": "reference has no model"}


def available() -> bool:
    """True when a classifier model is wired in. False in the reference."""
    return False
