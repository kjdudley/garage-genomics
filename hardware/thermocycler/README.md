# Pi thermocycler

Status: not yet designed. Placeholder directory — contributions welcome.

Planned contents:
- `BOM.csv` — bill of materials with vendor links
- `stl/` — printable enclosure parts
- `firmware/` — Pi-side PID controller and REST log export
- `README.md` — build guide

Target specs:
- 25 µL thin-wall PCR tubes, 8–16 well block
- Peltier-driven ramp ≥ 2 °C/s
- Heated lid to prevent condensation
- Temperature log streamed over JSON/HTTP for attachment to a LibreBiotech PCR Process record
