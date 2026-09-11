# PROJECT:     SWARM-DEVICE-AGNOSTIC (web reference)
# CREATED:     2026-09-10 17:59 MDT | 19:59 EDT | 23:59 Zulu
# DESCRIPTION: The fusion pipeline, laid out so you can SEE the architecture and exactly where each
#              advanced capability attaches. The reference ships the plain, textbook stages that make
#              the demo run end to end; the high-value stages (coherent combining, classification,
#              advanced direction finding) are present as CLEARLY MARKED extension points with no
#              implementation inside. This is a reference skeleton, not the production engine.
#
#   Stage flow (see server.py for the wiring):
#     observation  ->  detect  ->  [classify hook]  ->  crossfix  ->  [coherent hook]  ->  picture
#
#   Implemented here (plain, public-domain DSP/geometry):
#     - detect.py   : energy/onset gate reference
#     - crossfix.py : least-squares bearing cross-fix (schoolbook triangulation)
#   Extension points here (empty on purpose, this is where the cool stuff goes):
#     - classify.py : the acoustic classifier plugs in here
#     - coherent.py : CoHear coherent multi-node combining plugs in here
