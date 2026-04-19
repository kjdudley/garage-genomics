#!/usr/bin/env python3
"""
Create one Process for a retail sampling session — the origin Process
that all that session's Samples will attach to via process_id.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python create_retail_collection_process.py \\
        --date 2026-05-01 \\
        --city Sydney \\
        --collector "Kevin Dudley" \\
        --location "Sydney Fish Market + local sushi outlets" \\
        --dry-run

The script does two calls:
 1. POST /processes — title, owner_group_id, description, notes.
 2. PUT /processes/{id} — procedure_version_id + process_date.

Step 2 is where the Process attaches to procedure 58 (Retail tissue
collection) v0.1.0. Per PR 2, the first Process against an unlocked
procedure_version auto-locks it. Subsequent sessions run against the
same locked v0.1.0, which is the intended behaviour — multiple sessions
share the same retail-collection SOP.

Output: the new process.id. Feed it to create_samples_from_csv.py as
--process-id to register this session's Samples against it.

API reference: https://librebiotech.org/?action=docs&page=api#processes
"""

import argparse
import json
import sys

from submit_coi_protocol import api

GROUP_ID = 16              # Garage Genomics
PROCEDURE_VERSION_ID = 59  # Retail tissue collection v0.1.0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--date", required=True,
                    help="Session date, YYYY-MM-DD (goes to process_date)")
    ap.add_argument("--city", required=True,
                    help="City where sampling happened (appears in title)")
    ap.add_argument("--collector", required=True,
                    help="Who ran the collection (free text)")
    ap.add_argument("--location", default="",
                    help="Specific markets/outlets visited (free text)")
    ap.add_argument("--notes", default="",
                    help="Observations, weather, anything unusual")
    ap.add_argument("--group-id", type=int, default=GROUP_ID,
                    help=f"owner_group_id (default: {GROUP_ID})")
    ap.add_argument("--procedure-version-id", type=int, default=PROCEDURE_VERSION_ID,
                    help=f"procedure_version_id to attach to (default: {PROCEDURE_VERSION_ID} = Retail collection v0.1.0)")
    ap.add_argument("--dry-run", action="store_true", help="Print payloads; do not POST/PUT")
    args = ap.parse_args()

    title = f"Retail sashimi collection — {args.city} — {args.date}"
    description_lines = [
        f"Collector: {args.collector}",
        f"Session date: {args.date}",
        f"Location: {args.location or '(not specified)'}",
    ]
    description = "\n".join(description_lines)

    create_payload = {
        "title":          title,
        "owner_group_id": args.group_id,
        "description":    description,
        "notes":          args.notes,
    }

    attach_payload = {
        "procedure_version_id": args.procedure_version_id,
        "process_date":         args.date,
    }

    if args.dry_run:
        print("POST /processes", file=sys.stderr)
        print(json.dumps(create_payload, indent=2, ensure_ascii=False))
        print(file=sys.stderr)
        print(f"PUT /processes/<new_id>  # attaches + auto-locks procedure_version {args.procedure_version_id}", file=sys.stderr)
        print(json.dumps(attach_payload, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", "/processes", json=create_payload)
    if code not in (200, 201) or not body.get("success"):
        print(f"POST /processes failed: HTTP {code}")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        sys.exit(1)
    process_id = body["data"]["id"]
    print(f"POST /processes → HTTP {code}, process.id = {process_id}")

    code, body = api("PUT", f"/processes/{process_id}", json=attach_payload)
    if code not in (200, 201) or not body.get("success"):
        print(f"PUT /processes/{process_id} failed: HTTP {code}")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        sys.exit(1)
    print(f"PUT /processes/{process_id} → HTTP {code} (attached to procedure_version {args.procedure_version_id})")

    print()
    print("=" * 50)
    print(f"Process ready. process.id = {process_id}")
    print(f"Use --process-id {process_id} in create_samples_from_csv.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
