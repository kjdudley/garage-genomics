# Project state

Last updated: 2026-04-18

## What this is

Public video series about accessible molecular biology on a Raspberry Pi. Three planned project arcs:

1. **DNA barcoding** — pilot, in progress
2. **Environmental DNA (eDNA)** — not started
3. **LAMP pathogen testing** — not started

Meta-thesis ("garage genomics"): what used to cost $50k is now a Pi, a few open-source hardware designs, and ~$12/sample in reagents. The audience ends up with their own LibreBiotech account, their own data, and their project published into a shared open dataset.

## What exists now

### Repo: <https://github.com/kjdudley/garage-genomics> (public)

- Top-level MIT (scripts/analysis), `protocols/` CC-BY-4.0, `hardware/` CERN-OHL-S
- Full directory scaffold for all three arcs; only `protocols/coi-fish-barcoding/` has real content
- Primer FASTA and thermocycler program JSON under that pilot directory

### LibreBiotech

- **Group "Garage Genomics"** — id **16**, Kevin is Leader (created 2026-04-18)
- **Investigation "Sushi Truth: Consumer Fish Mislabeling"** — id **5**, under group 16, visibility `group`, license CC-BY-4.0
- **Protocol** — procedure id **56**, current version v0.1.1 (version id 58), visibility `public`
  - Title: *COI DNA Barcoding for Consumer Fish Samples*, category `measurement_qc`
  - v0.1.0 (id 56) → v0.1.1 (id 58, adds `annealing_temp_c` + `chelex_incubation_time_min` parameters)
  - **Pilot not yet dry-run validated** — expect v0.1.x patches; v0.1.2 will add ISA Assay classification (OBI:0002767 amplicon sequencing + OBI:0000695 chain-termination) before first wet-lab Process
  - History: originally procedure id 55, deleted 2026-04-19 via a DELETE-scope API bug (since hotfixed) while repairing an empty v0.1.2 bump. Recreated cleanly as procedure 56.
- Catalog resolution done: all 6 equipment + 13 material rows resolved (Nucleic acid stain type 63 was added by the platform after initial gap report)
- **No Study, Process, or Sample records yet** — that's the next ISA level to scaffold

### Scripts (`scripts/`)

All three have been run once already. Kept in repo for reproducibility and fork templating.

- `create_group.py` — POSTs *Garage Genomics* to `/groups`. Ran once → id 16.
- `create_investigation.py` — POSTs *Sushi Truth* to `/investigations`. Ran once (`--group-id 16`) → id 5.
- `submit_coi_protocol.py` — POSTs the monolithic COI protocol with all nested steps/equipment/materials/references. Current canonical procedure id **56** (re-created 2026-04-19 after the procedure-55 DELETE incident). Hard-coded catalog IDs in `EQUIPMENT_CATALOG_MAP` / `MATERIAL_CATALOG_MAP`. Flags: `--list-catalog`, `--dry-run`.
- `bump_procedure_version.py` — POSTs v0.1.1 on procedure 56 (adds per-run parameters). `PROCEDURE_ID = 56`. Content inherited via import from `submit_coi_protocol.py` so the two sources can't drift.
- *Not yet written:* `create_study.py` (Pilot Season 1), `create_sample.py` (per-sample logging).

## Key decisions and why

1. **Monolithic protocol at v0.1**, split into atomic (extraction / PCR / gel / Sanger) at v1.0 once the dry run surfaces natural seams. LibreBiotech's `category` enum is atomic (sample_prep / measurement_qc / sequencing) and points toward the eventual split.
2. **Public by default** (GitHub repo, LibreBiotech protocol, audience-owned LibreBiotech projects). The premise is viewer-reproducibility.
3. **License split per directory**: MIT for code, CC-BY-4.0 for protocols, CERN-OHL-S for hardware.
4. **AGRF is NOT an option for AU viewers.** Explicitly institutional-only per their FAQ. Paths for an AU public audience: (a) BioFoundry or other community biolab with pooled institutional account; (b) Plasmidsaurus via international shipping of PCR product (ambient, works in practice); (c) DIY nanopore sequencing via Oxford Nanopore MinION (ONT sells to individuals).
5. **Pilot episode to shoot first: "Is Your Sushi Lying to You?"** — single 22–26 min ep, 3-day real-time arc compressed, cold open with the BLAST result. Shoot before committing to the rest of the series to validate the format cheaply.

## Pending / blocked

- **Study scaffold** — next ISA level under Investigation 5. Suggested: *"Pilot Season 1 — [city]"*. No `create_study.py` yet.
- **Wet-lab dry run** end-to-end on 3 sashimi samples, logging every step in LibreBiotech. Must happen before any filming. This surfaces v0.1.1 patches and the real LibreBiotech UX gaps.
- **AU reagent sourcing section** to add to the protocol (NEB→Genesearch, IDT AU, Merck Australia, Astral Scientific, Rowe Scientific; ABN tip; BioFoundry partnership).
- **Sequencing strategy for AU viewers** — probably BioFoundry partnership for the pilot; revisit nanopore in a later episode.
- **Investigation visibility flip** — currently `group`. Decide whether to flip to `public` (`PUT /investigations/5`) before or after sample data starts flowing in.
- **Idea parked**: suggest to LibreBiotech they integrate with a sequencing provider (Plasmidsaurus / Macrogen / ONT) via a `POST /samples/{id}/sequence` broker endpoint. Not "LibreBiotech runs sequencing" — that's scope creep — but "LibreBiotech brokers the handoff." User wants to leave this alone for now.
- **API key rotation.** The key used in this session was pasted in chat — treat as compromised. Revoke at librebiotech.org → API Keys → create fresh.

## Next session quick-start

1. `cd ~/garage-genomics && git log --oneline`
2. Rotate and export a fresh LibreBiotech API key: `export LIBREBIOTECH_API_KEY=...`
3. Sanity check: `GET /api.php/v1/groups/16` and `/investigations/5` still resolve as expected.
4. Write `create_study.py` under Investigation 5 (*Pilot Season 1 — [city]*).
5. Order IDT primers + NEB reagents — 2-week lead time.
6. Start the wet-lab dry run.

## Reference

- LibreBiotech API base: `https://librebiotech.org/api.php/v1`
- API docs: <https://librebiotech.org/?action=docs&page=api>
- Protocol schema: <https://librebiotech.org/?action=docs&page=protocols#schema-reference>
- Published protocol (API): `GET /api.php/v1/procedures/56`
- Auth header: `X-API-Key: <key>`
- Rate limit: 1000 req/hr per key
