#!/usr/bin/env python3
"""
Create the Pilot Season 1 Study under the Sushi Truth Investigation.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python create_study.py --dry-run              # show payload
    python create_study.py                        # POST with city="TBD"
    python create_study.py --city Sydney          # commit a real city now
    python create_study.py --investigation-id 5   # override (default: 5)

The Study carries the ISA-level intent for the first round of sashimi
sampling: design type + study factors. Samples registered via
create_samples_from_csv.py will attach to this Study via study_samples, and
their annotation slots (vendor, claimed_species, blast_call/mislabel) will
emit as Factor Value columns in the ISA-Tab Assay Table per PR 5 + PR 6b.

The city is a placeholder by default. Commit one later via:
    PUT /api.php/v1/studies/{id}  {"title": "Pilot Season 1 — <city>"}

Design type: OBI:0300311 "observation design" is the primary descriptor
(observational, no intervention). A secondary descriptor — OBI:0002945
"population based design" (retail vendors across multiple outlets) — is
noted in the summary because LibreBiotech currently stores one design_type
only; a future study_design_descriptors junction table will allow multiple.

API reference: https://librebiotech.org/?action=docs&page=api#studies
"""

import argparse
import json
import os
import sys

import requests

API_BASE = "https://librebiotech.org/api.php/v1"

INVESTIGATION_ID = 5   # Sushi Truth

# Primary design type — verified against OLS4 OBI 2026-04-19.
DESIGN_TYPE_CURIE = "OBI:0300311"
DESIGN_TYPE_LABEL = "observation design"
DESIGN_TYPE_TEXT  = "observational — retail sampling with post-hoc identification"

# Factors that will carry per-sample values in the ISA-Tab Assay Table:
#   vendor          — set at purchase time (PR 4 annotation slot 'vendor')
#   claimed_species — set at purchase time (samples.organism_curie = claim)
#   mislabel_flag   — set post-BLAST (PR 4 annotation slot 'mislabel')
FACTORS = [
    {"name": "vendor"},
    {"name": "claimed_species"},
    {"name": "mislabel_flag"},
]

SUMMARY = (
    "First round of sashimi sampling for the Sushi Truth investigation. "
    "Observational (OBI:0300311), also population-based in the ISA-Tab sense "
    "(OBI:0002945 population based design — retail vendors across multiple "
    "outlets); platform currently stores one design_type, so the population "
    "aspect is recorded here until study_design_descriptors junction support "
    "lands. Claim-vs-measurement: each Sample carries the vendor's label as "
    "an a priori claim (samples.organism_curie + claimed_species factor), and "
    "the post-BLAST species call is recorded as a separate annotation "
    "(slot='blast_call') so the claim stays visible alongside the measurement "
    "forever. The mislabel_flag factor splits samples by whether the call "
    "matches the claim."
)


def api(method, path, **kw):
    key = os.environ.get("LIBREBIOTECH_API_KEY")
    if not key:
        sys.exit("error: set LIBREBIOTECH_API_KEY")
    h = kw.pop("headers", {})
    h["X-API-Key"] = key
    h.setdefault("Content-Type", "application/json")
    r = requests.request(method, f"{API_BASE}{path}", headers=h, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true", help="Print payload; do not POST")
    ap.add_argument("--investigation-id", type=int, default=INVESTIGATION_ID,
                    help=f"Override investigation_id (default: {INVESTIGATION_ID})")
    ap.add_argument("--city", default="TBD",
                    help="City for the Study title (default: TBD; rename later via PUT)")
    ap.add_argument("--visibility", default="group", choices=["private", "group", "public"],
                    help="Study visibility (default: group)")
    ap.add_argument("--license", default="CC-BY-4.0",
                    help="License (default: CC-BY-4.0)")
    args = ap.parse_args()

    payload = {
        "investigation_id":  args.investigation_id,
        "title":             f"Pilot Season 1 — {args.city}",
        "summary":           SUMMARY,
        "design_type":       DESIGN_TYPE_TEXT,
        "design_type_curie": DESIGN_TYPE_CURIE,
        "design_type_label": DESIGN_TYPE_LABEL,   # belt-and-braces for findOrCreateByCurie
        "factors":           FACTORS,
        "visibility":        args.visibility,
        "license":           args.license,
    }

    if args.dry_run:
        print("POST /studies", file=sys.stderr)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", "/studies", json=payload)
    print(f"HTTP {code}")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
