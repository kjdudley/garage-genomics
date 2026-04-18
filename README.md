# garage-genomics

A video-series companion repository for accessible molecular biology on a Raspberry Pi.

Three project arcs share this monorepo:

1. **DNA barcoding** — identify mystery fish, insects, plants. Pilot: `protocols/coi-fish-barcoding/`.
2. **Environmental DNA (eDNA)** — detect invasive species and pathogens in water samples.
3. **LAMP pathogen testing** — field-deployable colorimetric tests for agricultural and food-safety use.

Everything here is open source and targeted at non-specialist audiences: citizen scientists, teachers, farmers, makers.

## Structure

| Path | Contents | License |
|---|---|---|
| `protocols/` | Lab protocols, versioned to match [LibreBiotech](https://librebiotech.org) releases | CC-BY-4.0 |
| `hardware/` | BOMs, STLs, firmware for the Pi thermocycler and gel imager | CERN-OHL-S v2 |
| `scripts/` | Automation (e.g. LibreBiotech API submission) | MIT |
| `analysis/` | BLAST and sequence-analysis pipelines | MIT |

## Companion platform

Protocols are mirrored to [LibreBiotech](https://librebiotech.org) so samples, processes, and data stay traceable under the ISA framework. See `scripts/submit_coi_protocol.py` for the automated path.

## Status

v0.1 pilot: COI fish barcoding. Dry run in progress.
