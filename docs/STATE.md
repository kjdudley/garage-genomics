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

- Published protocol: **procedure id = 55**, version id = 53, `version_number = "0.1.0"`, **visibility = public**
  - Title: *COI DNA Barcoding for Consumer Fish Samples*
  - Category: `measurement_qc`
  - v0.1.0 pilot, **not yet dry-run validated** — expect v0.1.x patches
- Catalog resolution done: all 6 equipment + 13 material rows resolved (Nucleic acid stain type 63 was added by the platform after initial gap report)
- No Investigation or Study created yet

### Scripts (`scripts/`)

- `submit_coi_protocol.py` — POSTs the monolithic COI protocol. Equipment/material catalog IDs hard-coded in `EQUIPMENT_CATALOG_MAP` / `MATERIAL_CATALOG_MAP`. Flags: `--list-catalog`, `--dry-run`.
- `create_investigation.py` — creates *"Sushi Truth: Consumer Fish Mislabeling"* investigation. **Not yet run — blocked on group selection.**

## Key decisions and why

1. **Monolithic protocol at v0.1**, split into atomic (extraction / PCR / gel / Sanger) at v1.0 once the dry run surfaces natural seams. LibreBiotech's `category` enum is atomic (sample_prep / measurement_qc / sequencing) and points toward the eventual split.
2. **Public by default** (GitHub repo, LibreBiotech protocol, audience-owned LibreBiotech projects). The premise is viewer-reproducibility.
3. **License split per directory**: MIT for code, CC-BY-4.0 for protocols, CERN-OHL-S for hardware.
4. **AGRF is NOT an option for AU viewers.** Explicitly institutional-only per their FAQ. Paths for an AU public audience: (a) BioFoundry or other community biolab with pooled institutional account; (b) Plasmidsaurus via international shipping of PCR product (ambient, works in practice); (c) DIY nanopore sequencing via Oxford Nanopore MinION (ONT sells to individuals).
5. **Pilot episode to shoot first: "Is Your Sushi Lying to You?"** — single 22–26 min ep, 3-day real-time arc compressed, cold open with the BLAST result. Shoot before committing to the rest of the series to validate the format cheaply.

## Pending / blocked

- **New LibreBiotech group for garage-genomics work.** No `POST /groups` endpoint exists in the current API; waiting on feature request from LibreBiotech. Once unblocked, re-run `create_investigation.py --group-id <N>`. Existing groups are all research-scoped and don't fit a citizen-science investigation (user declined to reuse them).
- **Wet-lab dry run** end-to-end on 3 sashimi samples, logging every step in LibreBiotech. Must happen before any filming. This surfaces v0.1.1 patches and the real LibreBiotech UX gaps.
- **AU reagent sourcing section** to add to the protocol (NEB→Genesearch, IDT AU, Merck Australia, Astral Scientific, Rowe Scientific; ABN tip; BioFoundry partnership).
- **Sequencing strategy for AU viewers** — probably BioFoundry partnership for the pilot; revisit nanopore in a later episode.
- **Investigation visibility** decision — current script defaults to `group`. Can be flipped via `PUT /investigations/{id}` once seeded.
- **Idea parked**: suggest to LibreBiotech they integrate with a sequencing provider (Plasmidsaurus / Macrogen / ONT) via a `POST /samples/{id}/sequence` broker endpoint. Not "LibreBiotech runs sequencing" — that's scope creep — but "LibreBiotech brokers the handoff." User wants to leave this alone for now.
- **API key rotation.** The key used in this session was pasted in chat — treat as compromised. Revoke at librebiotech.org → API Keys → create fresh.

## Next session quick-start

1. `cd ~/garage-genomics && git log --oneline`
2. Rotate and export a fresh LibreBiotech API key: `export LIBREBIOTECH_API_KEY=...`
3. Decide group strategy (new group created in UI, or proceed with an existing one) and update `create_investigation.py` or pass `--group-id`.
4. `python3 scripts/create_investigation.py --dry-run` then without `--dry-run`.
5. Write a `create_study.py` under that Investigation (*Pilot Season 1 — [city]*).
6. Start the wet-lab dry run. Order IDT primers + NEB reagents — 2-week lead time.

## Reference

- LibreBiotech API base: `https://librebiotech.org/api.php/v1`
- API docs: <https://librebiotech.org/?action=docs&page=api>
- Protocol schema: <https://librebiotech.org/?action=docs&page=protocols#schema-reference>
- Published protocol (API): `GET /api.php/v1/procedures/55`
- Auth header: `X-API-Key: <key>`
- Rate limit: 1000 req/hr per key
