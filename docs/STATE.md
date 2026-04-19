# Project state

Last updated: 2026-04-19

## What this is

Public video series about accessible molecular biology on a Raspberry Pi. Three planned project arcs:

1. **DNA barcoding** — pilot, fully scaffolded on LibreBiotech; wet-lab dry run pending
2. **Environmental DNA (eDNA)** — not started
3. **LAMP pathogen testing** — not started

Meta-thesis ("garage genomics"): what used to cost $50k is now a Pi, a few open-source hardware designs, and ~$12/sample in reagents. The audience ends up with their own LibreBiotech account, their own data, and their project published into a shared open dataset.

## Session of 2026-04-19 — major changes

Single-day sprint closed every platform-level federated-FAIR gap blocking the Sushi Truth pilot. Seven PRs shipped end-to-end on the LibreBiotech side (dev-driven, architecturally reviewed here). Five client-side pilot scripts written and committed. Two protocols live at their canonical versions; a Study scaffolded. Pilot workflow ready end-to-end; only wet-lab dry run and reagent ordering remain.

### Platform PRs shipped (LibreBiotech side)

- **PR 1** — Parameter wiring: `protocol_parameters` FK'd to `procedure_versions`; parameter-definition UI; `AssayParameterValueRepository`; exporter parameter-column projection from definitions (fixed old INNER JOIN emitting unstable schemas).
- **PR 2** — Version immutability: `procedure_versions.is_locked` auto-flips on first `processes` reference; repo-level guards; atomic fork-and-retarget for mid-run parameter realization. Discovery: the web UI Save button was already non-mutating (`createVersion()` always), so guards are defense-in-depth.
- **PR 3** — Federated-FAIR identifier contract: CURIE-primary API (`unit_term_curie`, `assay_type_curie`, etc.) with `ApiController::resolveTermId($payload, $prefix, $required)` base helper. Preferred ontologies over instance-local integer IDs.
- **PR 4** — Samples write path + annotations: `organism_curie` writer (killed the zombie), `AnnotationsApiController`, inline annotations on sample POST. Photo upload intentionally deferred (stopgap: photos in public GitHub repo, URL in `photo_ref` annotation).
- **PR 5** — `StudiesApiController` from scratch: flat + nested routes, `design_type_curie` + `factors[]`; killed `studies.design_type_term_id` and `study_factors.type_term_id` zombies. Fixed the misleading "studies hang off investigation" doc line.
- **PR 6a** — `measurement_type_{curie|label|id}` + `technology_type_{curie|label|id}` on `procedure_versions`. Path-(c) design chosen over path-(b) first-class `study_assay_types` entity: move ISA Assay classification UP to the procedure, derive Study-Assays at export time from `DISTINCT` across a Study's procedures. Project-don't-flatten one level up.
- **PR 6b** — Exporter rewrite: iterate DISTINCT `(m_type, t_type)` per Study, group measurement events into one ISA-Tab file per tuple. Protocol REF fix resolves to `procedure_version.id` with canonical name from `procedure.title + version_number` (closed the 20-PCR-runs-= 20-protocols bug). `docs/ISA_SEMANTIC_MAPPING.md` shipped alongside (codebase-name ↔ ISA-meaning Rosetta Stone, first time the mapping is written in the repo itself).
- **PR 7** — Sample → Study attachment: `study_ids: [int]` on POST/PUT `/samples`; `POST /studies/{id}/samples` + `DELETE /studies/{id}/samples/{sample_id}` for post-hoc editing. Scope-pushback kept `process_id` required (preserves ISA-canonical origin-Process pattern — nullable would have handed users a lossy shortcut).

### Zombie scorecard (final)

- **Killed — writer added:** `samples.organism_term_id` (PR 4), `studies.design_type_term_id` (PR 5), `study_factors.type_term_id` (PR 5), `procedure_versions.measurement_type_term_id` (PR 6a, newly added + writer), `procedure_versions.technology_type_term_id` (PR 6a).
- **Obsolete — refactor removed the need:** `assays.measurement_type_term_id`, `assays.technology_type_term_id`, `study_assay_types.measurement_type_term_id`, `study_assay_types.technology_type_term_id` — all four became redundant under path (c); data lives on `procedure_versions` now.
- **Structural divergences fixed in PR 6b:** `assays` row-grain ≠ ISA Assay declaration (closed by exporter grouping); `processes.title` pulled instead of `procedure_version.id` for Protocol REF (closed).

### Incidents worth remembering

- **Procedure 55 loss.** Mid-session repair attempt on a content-empty v0.1.2 hit a router-misroute bug: `DELETE /procedures/{id}/versions/{version_id}` silently routed to the whole-procedure delete handler, removing procedure 55 entirely. Dev hotfixed same session; recovery via `submit_coi_protocol.py` + `bump_procedure_version.py` landed at procedure **56**, which is the current canonical COI procedure. Confirmation-guardrail on the still-legitimate `DELETE /procedures/{id}` is filed for post-pilot (low priority).
- **`POST /procedures` shape.** Requires `initial_version: {...}` nested object; a flat payload (like a version POST) returns `400 "initial_version (object) is required"`. `submit_coi_protocol.py` uses the nested shape; `submit_retail_collection_protocol.py` was corrected to match during this session.

## What exists now

### Repo (<https://github.com/kjdudley/garage-genomics> — public)

- Top-level MIT (scripts/analysis); `protocols/` CC-BY-4.0; `hardware/` CERN-OHL-S
- Directory scaffold for all three arcs; `coi-fish-barcoding/` + `retail-sample-collection/` populated with READMEs

### LibreBiotech state

| Entity | ID | Status |
|---|---|---|
| Group "Garage Genomics" | 16 | Leader: Kevin |
| Investigation "Sushi Truth: Consumer Fish Mislabeling" | 5 | visibility=`group`, CC-BY-4.0 |
| Study "Pilot Season 1 — TBD" | 7 | design_type=OBI:0300311 (observation design); 3 factors: vendor, claimed_species, mislabel_flag |
| Procedure "COI DNA Barcoding for Consumer Fish Samples" | 56 | category=measurement_qc; current v0.1.2 (id 60) |
| Procedure "Retail tissue collection for mislabeling studies" | 58 | category=sample_prep; current v0.1.0 (id 59) |

**Procedure 56 version history:**
- v0.1.0 (procedure_version.id 56) — monolithic initial
- v0.1.1 (id 58) — adds `annealing_temp_c` + `chelex_incubation_time_min` parameters
- **v0.1.2 (id 60, current)** — adds ISA Assay classification: `measurement_type=OBI:0002767` (amplicon sequencing assay) + `technology_type=OBI:0000695` (chain termination sequencing assay)
- None yet locked — no Processes against any version

**No Processes, Samples, Assays, or Measurements exist yet.** That's the wet-lab dry run.

### Scripts (`scripts/`) — all dry-run validated; ✓ means also POSTed live

**One-shot platform setup**
- `create_group.py` ✓ → group 16
- `create_investigation.py` ✓ → investigation 5
- `create_study.py` ✓ → study 7

**Protocol registration**
- `submit_coi_protocol.py` ✓ → procedure 56 v0.1.0
- `submit_retail_collection_protocol.py` ✓ → procedure 58 v0.1.0

**Version bumps (for procedure 56)**
- `bump_procedure_version.py` ✓ — v0.1.1 (parameter definitions)
- `bump_to_v0_1_2.py` ✓ — v0.1.2 (OBI Assay classification)

**Pilot workflow — written, not yet run**
- `create_retail_collection_process.py` — one Process per market trip against procedure 58 (POST then PUT to attach procedure_version_id, which auto-locks v0.1.0 on first use per PR 2)
- `create_samples_from_csv.py` — field-log CSV → N Samples per session with inline annotations; `--process-id` from the retail-collection Process; `--study-id` defaults to 7
- `log_blast_call.py` — audit-clean post-BLAST PUT: GETs each Sample's `organism_curie` (the claim), compares to `blast_call_curie` from CSV, auto-computes `mislabel_flag`, PUTs annotations-only. **Never overwrites** `samples.organism_curie`.

## Key decisions and why

1. **Monolithic protocol at v0.1**, split into atomic (extraction / PCR / gel / Sanger) at v1.0 once the dry run surfaces natural seams.
2. **Public by default** — GitHub repo, LibreBiotech protocol, audience-owned LibreBiotech projects.
3. **License split per directory**: MIT (code), CC-BY-4.0 (protocols), CERN-OHL-S (hardware).
4. **AGRF is NOT an option for AU viewers** (institutional-only). Paths: BioFoundry or equivalent community biolab with pooled account; Plasmidsaurus via international shipping (ambient, works in practice); ONT MinION for DIY.
5. **Pilot episode to shoot first: "Is Your Sushi Lying to You?"** — single 22–26 min ep, 3-day real-time arc compressed, cold open with the BLAST result.
6. **Path (c) for ISA Assay declaration** — move `(measurement_type, technology_type)` up to `procedure_versions`; derive Study-Assays at export via DISTINCT. Auto-declaration from science; can't drift from data; matches the team's "project, don't flatten" principle.
7. **Audit-clean mislabeling pattern** — `samples.organism_curie` stores the vendor's claim forever. Post-BLAST *never* overwrites; BLAST call lands as annotation (`slot='blast_call'`). Timestamp ordering (`sample.created_at < blast_call_annotation.created_at`) is the platform-side audit story; EXIF + receipts cover the stronger "when actually bought" question.
8. **Retail tissue collection as a first-class `sample_prep` Process** — teaches ISA-canonical "everything is a Process, even non-invasive collection"; gives every Sample a real origin; groups naturally by sampling session.
9. **Scoped PR pushback policy** — when a dev proposal weakens a principle we're teaching (e.g. PR 7 item #1: make `process_id` optional), push back to keep the strict API + better pattern.

## Pending / blocked

- **Wet-lab dry run** end-to-end on 3+ sashimi samples. Must happen before filming. Expected v0.1.x patches to COI protocol will surface.
- **City for Study 7 title.** Currently placeholder "TBD"; rename via `PUT /studies/7 {"title": "Pilot Season 1 — <city>"}` once committed.
- **Order IDT primers + NEB reagents.** ~2 week lead time; currencies via AU-side sourcing (Genesearch for NEB, IDT AU, Merck Australia, Astral Scientific, Rowe Scientific; ABN tip for tax; BioFoundry partnership).
- **AU reagent sourcing section** to add to `protocols/coi-fish-barcoding/README.md`.
- **Investigation visibility flip** `PUT /investigations/5 {"visibility": "public"}` before or after sample data flows — decision pending.
- **Flow-3 demo capture** worth filming deliberately: procedure 56 at v0.1.2 ensures COI measurement events group into `a_{study}_OBI_0002767_OBI_0000695.txt` in ISA-Tab export; demonstrates federated-FAIR as verifiable not aspirational.
- **`GET /studies/{id}/samples` listing endpoint** — filed as non-urgent post-PR-7 ergonomic gap.
- **`DELETE /procedures/{id}` confirmation guardrail** — low-priority post-pilot follow-up on the platform.
- **Platform stretch (post-pilot breaking-change window):** `study_assay_types` table formal deprecation; `assays → measurement_events` rename (PR 6c).

## Next session quick-start

1. `cd ~/garage-genomics && git log --oneline -10`
2. `export LIBREBIOTECH_API_KEY=...` (mint fresh at librebiotech.org → API Keys if stale)
3. Sanity check:
   ```
   curl -sH "X-API-Key: $LIBREBIOTECH_API_KEY" \
     https://librebiotech.org/api.php/v1/procedures/56 \
     | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['current_version']['version_number'])"
   ```
   Expect `0.1.2`.
4. **If wet-lab ready:**
   - Market trip. Populate a field-log CSV per the schema in `create_samples_from_csv.py`'s docstring.
   - `python scripts/create_retail_collection_process.py --date YYYY-MM-DD --city <x> --collector "..."` → note the `process.id`
   - `python scripts/create_samples_from_csv.py --csv field-log.csv --process-id <x>`
   - Run COI wet lab per `protocols/coi-fish-barcoding/README.md`. Create a COI Process against procedure 56 v0.1.2 (locks it on first use).
   - Post-BLAST: `python scripts/log_blast_call.py --csv blast-results.csv`
5. **If pre-reagents:** order IDT primers + NEB reagents; write the AU sourcing section for the COI README; pick the pilot city.

## Reference

- LibreBiotech API base: `https://librebiotech.org/api.php/v1`
- API docs: <https://librebiotech.org/?action=docs&page=api>
- Protocol schema: <https://librebiotech.org/?action=docs&page=protocols#schema-reference>
- ISA semantic mapping doc (shipped with PR 6b): <https://librebiotech.org/?action=docs&page=isa-semantic-mapping>
- Published protocols (API): `GET /api.php/v1/procedures/56` (COI), `GET /api.php/v1/procedures/58` (retail collection)
- Published study (API): `GET /api.php/v1/studies/7`
- Auth header: `X-API-Key: <key>`
- Rate limit: 1000 req/hr per key
