#!/usr/bin/env python3
"""
Register retail sashimi Samples from a field-log CSV — one POST /samples
per row, attaching to the session's Process and Study 7.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python create_samples_from_csv.py \\
        --csv sampling-log.csv \\
        --process-id 42 \\
        --dry-run

    python create_samples_from_csv.py --csv sampling-log.csv --process-id 42

--process-id comes from create_retail_collection_process.py's output for
this session. --study-id defaults to 7 (Pilot Season 1).

CSV schema (header row required):
    label                          — required. Unique Sample ID e.g. SashimiPilot-001
    organism_curie                 — required. NCBITaxon CURIE of the vendor's claim
    collected_at                   — required. ISO timestamp (preserve tz)
    vendor                         — required. Vendor name, free text
    material_type                  — optional, default "sample"
    description                    — optional free-text
    purchase_price                 — optional, numeric
    purchase_price_currency_curie  — optional, unit CURIE for the currency
    photo_ref                      — optional, URL to photo (public repo, etc.)
    claimed_species_label          — optional, free-text claim as written (menu kanji, vernacular)

Record organism_curie with the NCBITaxon ID of the vendor's labelled species
— this is the *a priori claim*. Never overwrite it post-BLAST. The BLAST call
is recorded via log_blast_call.py as a separate annotation (slot='blast_call'),
leaving both claim and call visible forever.

Per-row errors print + continue — one bad row doesn't abort the session.
Exit code 1 if any row failed.

API reference: https://librebiotech.org/?action=docs&page=api#samples
"""

import argparse
import csv
import json
import sys

from submit_coi_protocol import api

REQUIRED_COLS = ["label", "organism_curie", "collected_at", "vendor"]
DEFAULT_MATERIAL_TYPE = "sample"
DEFAULT_STUDY_ID = 7


def row_to_payload(row, study_ids, process_id):
    # Strip whitespace from all values
    row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

    missing = [c for c in REQUIRED_COLS if not row.get(c)]
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    payload = {
        "process_id":     process_id,
        "study_ids":      study_ids,
        "label":          row["label"],
        "material_type":  row.get("material_type") or DEFAULT_MATERIAL_TYPE,
        "organism_curie": row["organism_curie"],
    }
    if row.get("description"):
        payload["description"] = row["description"]

    annotations = [
        {"slot": "collected_at", "value_text": row["collected_at"]},
        {"slot": "vendor",       "value_text": row["vendor"]},
    ]
    if row.get("photo_ref"):
        annotations.append({"slot": "photo_ref", "value_text": row["photo_ref"]})
    if row.get("purchase_price"):
        try:
            price_num = float(row["purchase_price"])
        except ValueError:
            raise ValueError(f"purchase_price not numeric: {row['purchase_price']!r}")
        ann = {"slot": "purchase_price", "value_num": price_num}
        if row.get("purchase_price_currency_curie"):
            ann["unit_curie"] = row["purchase_price_currency_curie"]
        annotations.append(ann)
    if row.get("claimed_species_label"):
        annotations.append({"slot": "claimed_species_label", "value_text": row["claimed_species_label"]})

    payload["annotations"] = annotations
    return payload


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--csv", required=True, help="Path to field-log CSV")
    ap.add_argument("--process-id", type=int, required=True,
                    help="Retail-collection session Process ID")
    ap.add_argument("--study-id", type=int, default=DEFAULT_STUDY_ID,
                    help=f"Study to attach samples to (default: {DEFAULT_STUDY_ID})")
    ap.add_argument("--dry-run", action="store_true", help="Print payloads; do not POST")
    args = ap.parse_args()

    with open(args.csv, newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit("error: CSV has no data rows")

    print(f"Loaded {len(rows)} rows from {args.csv}", file=sys.stderr)
    print(f"process_id = {args.process_id}, study_ids = [{args.study_id}]", file=sys.stderr)
    print(file=sys.stderr)

    created = []
    errors = []

    for i, row in enumerate(rows, start=1):
        try:
            payload = row_to_payload(row, [args.study_id], args.process_id)
        except ValueError as e:
            err = f"row {i}: {e}"
            print(err, file=sys.stderr)
            errors.append((i, row.get("label"), err))
            continue

        if args.dry_run:
            print(f"--- row {i}: {payload['label']} ---")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            continue

        code, body = api("POST", "/samples", json=payload)
        if code not in (200, 201) or not body.get("success"):
            err_msg = body.get("error") or f"HTTP {code}"
            err = f"row {i} ({payload.get('label')}): {err_msg}"
            print(err, file=sys.stderr)
            errors.append((i, payload.get("label"), err))
            continue

        sample_id = body["data"]["id"]
        print(f"row {i}: {payload['label']} → sample.id = {sample_id}")
        created.append((i, payload["label"], sample_id))

    print(file=sys.stderr)
    print("=== Summary ===", file=sys.stderr)
    print(f"Created: {len(created)} / {len(rows)}", file=sys.stderr)
    print(f"Errors:  {len(errors)}", file=sys.stderr)
    for i, label, msg in errors:
        print(f"  row {i} ({label}): {msg}", file=sys.stderr)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
