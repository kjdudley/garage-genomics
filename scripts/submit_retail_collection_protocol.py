#!/usr/bin/env python3
"""
Create the Retail tissue collection procedure on LibreBiotech.

Usage:
    export LIBREBIOTECH_API_KEY=...
    python submit_retail_collection_protocol.py --dry-run
    python submit_retail_collection_protocol.py              # POST /procedures

This is the sample_prep procedure for field collection of retail fish/seafood
tissue. One Process per market trip; Samples registered against that Process
via create_samples_from_csv.py. Upstream of the COI barcoding assay in the
Sushi Truth pilot.

No equipment, materials, or reagents are declared in the LibreBiotech payload —
retail field work doesn't consume lab stock, and any hardware items (cooler,
smartphone, tubes) belong in preparation notes not catalog rows.

No measurement_type_curie / technology_type_curie: this is a sample_prep
procedure (no measurements emitted). PR 6b's exporter correctly skips
sample_prep in Assay Table grouping because measurement_type is null.

API reference: https://librebiotech.org/?action=docs&page=api#procedures
"""

import argparse
import json
import sys

from submit_coi_protocol import api

TITLE = "Retail tissue collection for mislabeling studies"
DESCRIPTION = (
    "Standardised collection of retail fish/seafood tissue (sushi, sashimi, "
    "fillets) for downstream species-ID. Captures the vendor's labelled "
    "species at purchase time as the a priori claim; preserved alongside the "
    "post-measurement call so mislabel audits always have both values visible. "
    "Upstream of species-ID assays such as COI barcoding."
)
CATEGORY = "sample_prep"
VISIBILITY = "public"
LICENSE = "CC-BY-4.0"
URL = "https://github.com/kjdudley/garage-genomics/blob/main/protocols/retail-sample-collection/README.md"

VERSION_NUMBER = "0.1.0"
EFFECTIVE_DATE = "2026-04-19"
CHANGELOG = "Initial release. Companion sample_prep protocol for the Sushi Truth pilot, upstream of COI barcoding."

SAFETY_TEXT = (
    "- **Food-grade handling.** Buy samples you or others would normally eat. "
    "Discard remaining tissue after excising the subsample if you don't intend "
    "to consume the rest.\n"
    "- **Labelling discipline in the field.** Mislabeled tubes cascade into "
    "wrong BLAST calls downstream. Pre-print labels; cross-check tube → field "
    "log → LibreBiotech Sample ID before moving to the next vendor.\n"
    "- **Cold chain.** On ice from purchase until freezer or extraction bench. "
    "Fresh at ambient acceptable for ≤ 4 h if extraction is same-day; otherwise "
    "−20 °C immediately.\n"
    "- **No cross-contamination.** Fresh pick/scalpel per sample; change gloves "
    "between samples; no re-use of utensils."
)

PREPARATION_TEXT = (
    "**Field kit** (no reagents): smartphone/camera with EXIF timestamps; "
    "cooler bag with ≥ 2 h ice; 1.5–2 mL sample tubes (n + 20 % spares); "
    "sterile picks or disposable scalpels (one per sample); waterproof marker "
    "+ pre-printed labels; field log (one row per sample).\n\n"
    "**Pre-printed labels** are strongly recommended. Use a consistent scheme "
    "matching what will be registered in LibreBiotech, e.g. "
    "`SashimiPilot-001`, `SashimiPilot-002`, …\n\n"
    "**Target species list.** Know in advance which taxa you're testing claims "
    "against — BLAST coverage against BOLD / NCBI nr is uneven across clades. "
    "Ward et al. 2005 is a solid reference for teleost fish.\n\n"
    "**Photograph the claim before the purchase.** The vendor's label, menu "
    "entry, or signage showing the claimed species — with vendor name in frame."
)

TIMING_TEXT = (
    "- **Per sample, ~3–5 minutes** (longer at busy vendors if photography is "
    "constrained)\n"
    "- **Market trip total, 30–90 minutes** depending on sample count\n"
    "- **Cold-chain budget:** ≤ 4 h ambient before extraction or freezer; "
    "frozen indefinitely"
)

COMPLETION_TEXT = (
    "**Per-sample deliverables at session end:**\n"
    "- Labelled tube in the cooler, ~20 mg excised tissue\n"
    "- LibreBiotech Sample record pre-registered with `samples.organism_curie` "
    "= NCBITaxon claim (as-labelled, not as-interpreted) and annotations "
    "`collected_at`, `vendor`, `purchase_price` + `unit_curie` (currency), "
    "`photo_ref` URL\n"
    "- Photos with EXIF timestamp preceding the Sample's `created_at` in "
    "LibreBiotech — this is the audit story (claim preceded any measurement)\n\n"
    "**Record the claim as-labelled, not as-interpreted.** Transliterate "
    "Japanese menu names, vernacular names, or vague labels verbatim. Do not "
    "guess the scientific species until post-BLAST — that defeats the "
    "claim-vs-measurement design."
)

STEPS = [
    "Record the market trip metadata in your field log before any purchase: vendor / market name, location, date, session start time, collector.",
    "Photograph the vendor's claim — label, menu entry, or display signage showing the claimed species with vendor name visible in frame.",
    "Purchase the sample. Retain the receipt; photograph it separately.",
    "Assign a unique Sample ID from your pre-printed label pool (e.g. SashimiPilot-001). Record it in the field log with vendor, claimed species as written, price, and purchase time.",
    "Photograph the purchased piece with its Sample ID label visible — this is the physical provenance chain.",
    "Excise ~20 mg tissue (rice-grain size) into the labelled tube using a fresh pick or scalpel. Close tightly.",
    "Place tube in cooler with ice. Use a foam rack or zip bag to keep tubes off direct ice contact.",
    "Change gloves; dispose of the used pick. No re-use across samples.",
    "At session end, return to lab or home freezer. Register each Sample in LibreBiotech via create_samples_from_csv.py with the session's collection Process as process_id and the Sushi Truth Study attached via study_ids. Upload photos to a public store and capture the URL as annotation slot photo_ref on each Sample.",
]

REFERENCES = [
    {
        "citation": "Ward RD, Zemlak TS, Innes BH, Last PR, Hebert PDN (2005). DNA barcoding Australia's fish species. Phil Trans R Soc B 360:1847–57.",
        "doi": "10.1098/rstb.2005.1716",
        "url": None,
        "ref_type": "paper",
    },
    {
        "citation": "BOLD Systems — Barcode of Life Data System",
        "doi": None,
        "url": "https://boldsystems.org",
        "ref_type": "other",
    },
]


def build_payload():
    return {
        "title":       TITLE,
        "description": DESCRIPTION,
        "category":    CATEGORY,
        "visibility":  VISIBILITY,
        "license":     LICENSE,
        "url":         URL,
        "initial_version": {
            "version_number":         VERSION_NUMBER,
            "effective_date":         EFFECTIVE_DATE,
            "change_log":             CHANGELOG,
            "safety_text":            SAFETY_TEXT,
            "preparation_notes_text": PREPARATION_TEXT,
            "timing_text":            TIMING_TEXT,
            "completion_notes_text":  COMPLETION_TEXT,
            "steps":                  [{"content": s} for s in STEPS],
            "equipment":              [],
            "materials":              [],
            "parameters":             [],
            "references":             REFERENCES,
        },
    }


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true", help="Print payload; do not POST")
    args = ap.parse_args()

    payload = build_payload()

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", "/procedures", json=payload)
    print(f"HTTP {code}")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
