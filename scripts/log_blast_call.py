#!/usr/bin/env python3
"""
Record BLAST results on Samples via annotations-only PUT — audit-clean pattern.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python log_blast_call.py --csv blast-results.csv --dry-run
    python log_blast_call.py --csv blast-results.csv

For each row, this script:
 1. GETs the Sample to read its claimed organism_curie (the a priori claim).
 2. Compares to the BLAST call from the CSV to compute mislabel_flag.
 3. PUTs /samples/{id} with annotations — NEVER touches samples.organism_curie.

The claim stays in samples.organism_curie forever. The BLAST call lands as
a separate annotation (slot='blast_call') alongside supporting metadata. This
is the mislabeling-study audit pattern — claim and call both visible in
perpetuity; readers can verify the claim preceded the measurement by the
timestamp ordering (sample.created_at < any blast_call annotation.created_at).

CSV schema (header row required):
    sample_id              — required, int. LibreBiotech sample.id (not label)
    blast_call_curie       — required. NCBITaxon CURIE of the BLAST top hit
    blast_call_label       — optional. Human-readable species (belt-and-braces)
    percent_identity       — optional, float. BLAST top-hit %ID
    query_coverage         — optional, float. BLAST top-hit query coverage
    accession              — optional. Top-hit database accession
    database               — optional. BOLD, NCBI nr, etc.
    blast_date             — optional. ISO date of the BLAST run
    mislabel_flag          — optional. Override auto-compute (yes|no|indeterminate).
                             Useful for genus-only calls where direct CURIE
                             comparison isn't meaningful.
    notes                  — optional. Free-text

Annotations written (one sample, many rows in annotations table):
    blast_call             — term-typed (term_curie + term_label)
    mislabel_flag          — value_text (yes|no|indeterminate)
    blast_percent_identity — value_num
    blast_query_coverage   — value_num
    blast_accession        — value_text
    blast_database         — value_text
    blast_date             — value_text
    blast_notes            — value_text

**PUT-append semantics.** Running this script twice on the same sample
creates duplicate annotations — no upsert. To correct a mistaken BLAST
call, first DELETE /api.php/v1/annotations/{id} for the wrong annotations,
then re-run. Check existing annotations via GET /samples/{id}.

Per-row errors print and continue. Exit 1 if any row failed.

API reference: https://librebiotech.org/?action=docs&page=api#samples
"""

import argparse
import csv
import json
import sys

from submit_coi_protocol import api


def fetch_claim(sample_id):
    """Return the Sample's claimed organism_curie (or None if not set)."""
    code, body = api("GET", f"/samples/{sample_id}")
    if code != 200 or not body.get("success"):
        raise LookupError(f"GET /samples/{sample_id} failed: HTTP {code}: {body.get('error', '')}")
    data = body["data"]
    term = data.get("organism_term") or {}
    return term.get("curie")


def build_annotations(row, claim_curie):
    """Assemble annotations list from CSV row + fetched claim."""
    call_curie = row["blast_call_curie"]
    annotations = [{
        "slot":       "blast_call",
        "term_curie": call_curie,
    }]
    if row.get("blast_call_label"):
        annotations[0]["term_label"] = row["blast_call_label"]

    # mislabel_flag: CSV override > auto-compute
    if row.get("mislabel_flag"):
        mislabel = row["mislabel_flag"]
    elif claim_curie is None:
        mislabel = "indeterminate"
    else:
        mislabel = "no" if call_curie == claim_curie else "yes"
    annotations.append({"slot": "mislabel_flag", "value_text": mislabel})

    if row.get("percent_identity"):
        try:
            annotations.append({"slot": "blast_percent_identity",
                                "value_num": float(row["percent_identity"])})
        except ValueError:
            raise ValueError(f"percent_identity not numeric: {row['percent_identity']!r}")
    if row.get("query_coverage"):
        try:
            annotations.append({"slot": "blast_query_coverage",
                                "value_num": float(row["query_coverage"])})
        except ValueError:
            raise ValueError(f"query_coverage not numeric: {row['query_coverage']!r}")
    if row.get("accession"):
        annotations.append({"slot": "blast_accession", "value_text": row["accession"]})
    if row.get("database"):
        annotations.append({"slot": "blast_database", "value_text": row["database"]})
    if row.get("blast_date"):
        annotations.append({"slot": "blast_date", "value_text": row["blast_date"]})
    if row.get("notes"):
        annotations.append({"slot": "blast_notes", "value_text": row["notes"]})

    return annotations


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--csv", required=True, help="Path to BLAST results CSV")
    ap.add_argument("--dry-run", action="store_true", help="Print payloads; do not PUT")
    args = ap.parse_args()

    with open(args.csv, newline="") as f:
        rows = [
            {k: (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            for r in csv.DictReader(f)
        ]
    if not rows:
        sys.exit("error: CSV has no data rows")

    print(f"Loaded {len(rows)} rows from {args.csv}", file=sys.stderr)
    print(file=sys.stderr)

    updated = []
    errors  = []

    for i, row in enumerate(rows, start=1):
        sid_raw = row.get("sample_id", "")
        call    = row.get("blast_call_curie", "")

        def record_error(msg):
            print(f"row {i} (sample {sid_raw}): {msg}", file=sys.stderr)
            errors.append((i, sid_raw, msg))

        if not sid_raw or not call:
            record_error("missing sample_id or blast_call_curie")
            continue
        try:
            sample_id = int(sid_raw)
        except ValueError:
            record_error(f"sample_id {sid_raw!r} not an integer")
            continue

        try:
            claim_curie = fetch_claim(sample_id)
        except LookupError as e:
            record_error(str(e))
            continue

        try:
            annotations = build_annotations(row, claim_curie)
        except ValueError as e:
            record_error(str(e))
            continue

        mislabel = next(a["value_text"] for a in annotations if a["slot"] == "mislabel_flag")
        payload  = {"annotations": annotations}

        if args.dry_run:
            print(f"--- row {i}: sample {sample_id}, claim={claim_curie}, call={call}, mislabel={mislabel} ---")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            continue

        code, body = api("PUT", f"/samples/{sample_id}", json=payload)
        if code not in (200, 201) or not body.get("success"):
            record_error(body.get("error") or f"HTTP {code}")
            continue

        print(f"row {i}: sample {sample_id}, claim={claim_curie}, call={call}, mislabel={mislabel}")
        updated.append((i, sample_id, mislabel))

    print(file=sys.stderr)
    print("=== Summary ===", file=sys.stderr)
    print(f"Updated: {len(updated)} / {len(rows)}", file=sys.stderr)
    print(f"Errors:  {len(errors)}", file=sys.stderr)
    if updated:
        yes_count  = sum(1 for _, _, m in updated if m == "yes")
        no_count   = sum(1 for _, _, m in updated if m == "no")
        other      = len(updated) - yes_count - no_count
        print(f"Mislabel rate: {yes_count}/{yes_count+no_count} ({100.0*yes_count/(yes_count+no_count):.1f}%)" if (yes_count+no_count) else "Mislabel rate: n/a", file=sys.stderr)
        if other:
            print(f"(indeterminate/other: {other})", file=sys.stderr)
    for i, sid, msg in errors:
        print(f"  row {i} (sample {sid}): {msg}", file=sys.stderr)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
