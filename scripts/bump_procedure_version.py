#!/usr/bin/env python3
"""
Bump procedure 55 (COI Fish Barcoding) to v0.1.1 — adds per-run parameters.

Flow:
    export LIBREBIOTECH_API_KEY=...
    python bump_procedure_version.py --dry-run    # print payload
    python bump_procedure_version.py              # POST /procedures/55/versions

v0.1.1 intentionally carries the same content as v0.1.0 for steps, equipment,
materials, and references — only the `parameters` list is new. Those unchanged
fields are imported from submit_coi_protocol.py so the two source-of-truth
definitions can't drift. The version-specific delta (version_number,
change_log, effective_date) is declared here.

API reference: https://librebiotech.org/?action=docs&page=api
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

VERSION_NUMBER = "0.1.1"
EFFECTIVE_DATE = "2026-04-19"
CHANGELOG = (
    "Adds two per-run parameters (annealing_temp_c, chelex_incubation_time_min) "
    "for per-Assay capture on the measurement matrix. No changes to steps, "
    "equipment, materials, or references — content inherited verbatim from "
    "v0.1.0 via submit_coi_protocol.py."
)


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
        print("Run `submit_coi_protocol.py --list-catalog` to resolve and update the MAPs.\n", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", f"/procedures/{PROCEDURE_ID}/versions", json=payload)
    print(f"HTTP {code}")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
