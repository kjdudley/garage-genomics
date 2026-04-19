#!/usr/bin/env python3
"""
Bump procedure 56 (COI Fish Barcoding) to v0.1.2 — adds ISA Assay
classification (measurement_type + technology_type) at the procedure_version
level per PR 6a.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python bump_to_v0_1_2.py --dry-run   # print payload
    python bump_to_v0_1_2.py             # POST /procedures/56/versions

v0.1.2 carries the same content as v0.1.1 (steps, equipment, materials,
parameters, references, safety/timing/prep/completion text) — all imported
from submit_coi_protocol.py so sources can't drift. The delta is two OBI
CURIEs moved up to the procedure_version level:

  measurement_type_curie = OBI:0002767 "amplicon sequencing assay"
  technology_type_curie  = OBI:0000695 "chain termination sequencing assay"

Both labels are sent alongside the CURIEs (belt-and-braces for
findOrCreateByCurie if Hetzner's ontology_terms doesn't have them indexed).

After this ships:
 - Pre-v0.1.2 measurement events would export into a_{study}_undeclared.txt
   (null classification on procedure_version → PR 6b's undeclared bucket).
 - Post-v0.1.2, same events move into a_{study}_OBI_0002767_OBI_0000695.txt.
 - That transition is the Flow-3 demo: the platform visibly shows when a
   procedure is mis-declared and fixes via normal version bump.

API reference: https://librebiotech.org/?action=docs&page=api#procedures
"""

import argparse
import json
import sys

from submit_coi_protocol import (
    STEPS,
    SAFETY_TEXT,
    PREPARATION_TEXT,
    TIMING_TEXT,
    COMPLETION_TEXT,
    REFERENCES,
    build_equipment,
    build_materials,
    build_parameters,
    api,
)

PROCEDURE_ID = 56

VERSION_NUMBER = "0.1.2"
EFFECTIVE_DATE = "2026-04-19"
CHANGELOG = (
    "Adds ISA Assay classification at the procedure_version level per PR 6a: "
    "measurement_type=OBI:0002767 (amplicon sequencing assay), "
    "technology_type=OBI:0000695 (chain termination sequencing assay). "
    "No content changes — steps, equipment, materials, parameters, references, "
    "and narrative text carried verbatim from v0.1.1 via "
    "submit_coi_protocol.py import. Required for PR 6b's exporter to "
    "correctly group COI measurement events under a single ISA-Tab Assay Table."
)

MEASUREMENT_TYPE_CURIE = "OBI:0002767"
MEASUREMENT_TYPE_LABEL = "amplicon sequencing assay"
TECHNOLOGY_TYPE_CURIE  = "OBI:0000695"
TECHNOLOGY_TYPE_LABEL  = "chain termination sequencing assay"


def build_payload():
    equipment, eq_gaps = build_equipment()
    materials, mat_gaps = build_materials()
    parameters, param_gaps = build_parameters()
    payload = {
        "version_number":         VERSION_NUMBER,
        "effective_date":         EFFECTIVE_DATE,
        "change_log":             CHANGELOG,
        "safety_text":            SAFETY_TEXT,
        "preparation_notes_text": PREPARATION_TEXT,
        "timing_text":            TIMING_TEXT,
        "completion_notes_text":  COMPLETION_TEXT,
        "steps":                  [{"content": s} for s in STEPS],
        "equipment":              equipment,
        "materials":              materials,
        "parameters":             parameters,
        "references":             REFERENCES,
        "measurement_type_curie": MEASUREMENT_TYPE_CURIE,
        "measurement_type_label": MEASUREMENT_TYPE_LABEL,
        "technology_type_curie":  TECHNOLOGY_TYPE_CURIE,
        "technology_type_label":  TECHNOLOGY_TYPE_LABEL,
    }
    return payload, eq_gaps + mat_gaps + param_gaps


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true", help="Print payload; do not POST")
    args = ap.parse_args()

    payload, gaps = build_payload()
    if gaps:
        print("Catalog gaps (rows dropped from payload):", file=sys.stderr)
        for g in gaps:
            print(f"  - {g}", file=sys.stderr)
        print("Run `submit_coi_protocol.py --list-catalog` to resolve.\n", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", f"/procedures/{PROCEDURE_ID}/versions", json=payload)
    print(f"HTTP {code}")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
