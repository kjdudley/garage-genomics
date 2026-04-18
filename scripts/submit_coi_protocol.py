#!/usr/bin/env python3
"""
Submit the COI Fish Barcoding protocol (v0.1.0) to LibreBiotech via its REST API.

Flow:
    export LIBREBIOTECH_API_KEY=...
    python submit_coi_protocol.py --list-catalog   # print all equipment/material IDs
    # edit EQUIPMENT_CATALOG_MAP and MATERIAL_CATALOG_MAP below with the IDs you found
    python submit_coi_protocol.py --dry-run        # print the payload, do not submit
    python submit_coi_protocol.py                  # submit for real (POST /procedures)

API reference: https://librebiotech.org/?action=docs&page=api
Protocol schema: https://librebiotech.org/?action=docs&page=protocols#schema-reference
"""

import argparse
import json
import os
import sys

import requests

API_BASE = "https://librebiotech.org/api.php/v1"


# ---------------------------------------------------------------------------
# Catalog ID overrides
# ---------------------------------------------------------------------------
# After `--list-catalog`, paste integer IDs here. Any row left as None will be
# dropped from the payload and reported as a "catalog gap" so you can decide
# whether to request the missing catalog entry, submit generic, or edit the
# protocol. Matching is by the exact name string used in the rows below.

EQUIPMENT_CATALOG_MAP = {
    # equipment name below  ->  equipment_type_id  (int, from /catalog/equipment-types)
    "Thermocycler":               None,
    "Gel documentation system":   None,
    "Heat block":                 None,
    "Microcentrifuge":            None,
    "Gel electrophoresis system": None,
    "Pipettes":                   None,
}

# (material_type_name, product_name_or_None)  ->  (material_type_id, material_product_id_or_None)
# product_id may stay None to submit as "generic (any)" with free-text notes.
MATERIAL_CATALOG_MAP = {
    ("Chelating resin",    None):                         (None, None),
    ("Protease",           "Proteinase K"):               (None, None),
    ("PCR master mix",     None):                         (None, None),
    ("Oligonucleotide",    "FishF1 primer, 10 µM"):       (None, None),
    ("Oligonucleotide",    "FishF2 primer, 10 µM"):       (None, None),
    ("Oligonucleotide",    "FishR1 primer, 10 µM"):       (None, None),
    ("Oligonucleotide",    "FishR2 primer, 10 µM"):       (None, None),
    ("Agarose",            None):                         (None, None),
    ("Nucleic acid stain", "SYBR Safe"):                  (None, None),
    ("Buffer",             "1X TBE"):                     (None, None),
    ("DNA ladder",         "100 bp ladder"):              (None, None),
    ("Loading dye",        "6X gel loading dye"):         (None, None),
    ("Water",              "Nuclease-free water"):        (None, None),
}


# ---------------------------------------------------------------------------
# Protocol content
# ---------------------------------------------------------------------------

TITLE = "COI DNA Barcoding for Consumer Fish Samples"

DESCRIPTION = (
    "Identifies teleost fish to species via the Folmer COI barcode region using "
    "the Ward et al. 2005 primer cocktail. Designed for citizen-science fish-"
    "mislabeling studies using consumer sushi/sashimi samples. Not a clinical "
    "or regulatory-grade assay."
)

CATEGORY = "measurement_qc"   # valid: sample_prep | measurement_qc | data_transformation | sequencing | management
VISIBILITY = "public"
LICENSE = "CC-BY-4.0"
EXTERNAL_URL = "https://github.com/kjdudley/garage-genomics/blob/main/protocols/coi-fish-barcoding/README.md"

VERSION_NUMBER = "0.1.0"
EFFECTIVE_DATE = "2026-04-18"
CHANGELOG = (
    "Initial pilot release. Monolithic procedure "
    "(sample → Chelex extraction → COI PCR → agarose gel → Sanger submission → "
    "BLAST species call). Planned v1.0 splits into atomic Sample Prep / "
    "Measurement & QC / Sequencing protocols once the dry run identifies the "
    "natural seams."
)

SAFETY_TEXT = """\
- **BSL-1 work only.** No human-subject, clinical, or regulated samples.
- **95–100°C heat step.** Use a dedicated heat block with closed lids; never open flame. Eye protection.
- **Pipetting hygiene.** Gloves and filter tips throughout. Change gloves between extraction and PCR setup.
- **SYBR Safe** is safer than ethidium bromide but still a DNA intercalator — gloves, no skin contact, seal gel waste per local biohazard rules.
- **Blue-LED transilluminator with amber filter — NOT UV.** Required if the protocol will be taught in schools.
- **PCR waste.** Bleach-treat pipette tips and tubes; discard in sealed bag.
- **No clinical interpretation.** Mislabeling calls are for open-dataset research, not consumer complaints or legal action.
"""

PREPARATION_TEXT = """\
**Sample specification.** ~20 mg teleost tissue per sample, rice-grain size. Raw or sashimi-grade preferred; lightly seared acceptable. Fully cooked, heavily processed, or surimi products require mini-barcode primers (see Completion Notes / Troubleshooting).

**Primer prep.** Order FishF1, FishF2, FishR1, FishR2 as separate 25-nmol oligos from IDT. Resuspend each to 100 µM in TE; dilute working stocks to 10 µM. Make two mixes: F-mix = equimolar F1+F2 at 10 µM total; R-mix = equimolar R1+R2 at 10 µM total.

**Chelex prep.** 5% w/v Chelex-100 in low-EDTA TE. Keep the suspension mixed — resin settles fast; pipette immediately after vortexing.

**Bench prep.** Bleach-wipe pre- and post-PCR areas. Dedicated pipette sets if available; otherwise filter tips plus strict glove changes. No-template controls are mandatory.

**LibreBiotech setup.** Before wet lab: create the Investigation ("Sushi Truth: Consumer Fish Mislabeling"), nested Study ("Pilot Season 1 — [city]"), and pre-register Sample records with claimed species, vendor metadata, and photos.
"""

TIMING_TEXT = """\
- **Day 1 (active wet lab, ~3.5 h):** extraction 45 min • PCR setup 15 min • thermocycling 2 h (hands-off) • gel run + image 45 min
- **Day 1→3 (external):** Sanger sequencing 24–48 h turnaround
- **Day 3 (analysis, ~1 h):** trim, BLAST, species call, log to LibreBiotech
- **Time-sensitive:** Chelex extract is best used within 4 h fresh or stored at –20°C. Run the gel the same day as cycling — do not leave PCR plates at room temp overnight.
"""

COMPLETION_TEXT = """\
**Expected outcome.** Single sharp ~655 bp band per sample on gel; clean Sanger trace (≥Q30 across amplicon); BLAST top hit to BOLD ≥98% identity, query coverage ≥90%, gap to next species ≥1% → species-level call.

**Storage.** Chelex extracts: –20°C, up to 1 year. PCR products: –20°C, up to 6 months.

**Data logging.** Every sample should end with a Sample record in LibreBiotech containing: claimed species, BLAST call, %ID, accession, thermocycler log, gel image, Sanger read. Flag `mislabeled=true` when the call differs from the claim.

**Troubleshooting.**

| Symptom | Likely cause | Fix |
|---|---|---|
| No band (cooked sample) | DNA degraded | Mini-barcode primers (Shokralla 2015); extend Proteinase K to 2 h |
| Band in no-template control | Reagent / bench contamination | Bleach bench, fresh aliquots, new tips — do not proceed |
| Multiple bands | Non-specific priming | Raise annealing to 54°C; dilute template 1:10 |
| Smear | Template overload or degradation | Dilute Chelex extract 1:10 |
| Low Sanger quality | Primer-dimer / PCR carryover | Request cleanup service; or gel-extract the 655 bp band |
| BLAST call ambiguous (top two hits within 1%) | Closely related species | Report to genus; note on Sample record |
"""

STEPS = [
    "Collect 2–3 tissue pieces per sample, ideally before sauces are applied. Create a Sample record in your Study with claimed species, vendor, price, date/time, photo, and claim source.",
    "Transfer ~20 mg tissue (rice-grain size) to a labeled 1.5 mL tube and cut into small fragments.",
    "Add 200 µL of freshly vortexed 5% Chelex-100 suspension and 5 µL of 20 mg/mL Proteinase K to the tube.",
    "Incubate at 56°C for 30 min. Vortex briefly once at the 15 min mark.",
    "Transfer to 95°C and incubate for 10 min.",
    "Vortex 10 s; centrifuge at 12,000 × g for 2 min.",
    "Carefully transfer ~100 µL of the clear upper phase to a new labeled tube, avoiding the Chelex pellet. This is the DNA template.",
    "Prepare a PCR master mix for n+1 reactions (always include a no-template control). Per reaction: 12.5 µL OneTaq 2X, 0.5 µL F-mix (10 µM), 0.5 µL R-mix (10 µM), 10.5 µL nuclease-free water.",
    "Aliquot 24 µL master mix into each PCR tube. Add 1 µL template to sample tubes; add 1 µL water to the NTC tube.",
    "Run the thermocycler: 94°C 2 min; 35 cycles of [94°C 30 s, 52°C 30 s, 72°C 45 s]; 72°C 10 min; 4°C hold.",
    "Export the thermocycler temperature log from the Pi controller. Attach it to the PCR Process record in LibreBiotech.",
    "Cast a 1.5% agarose gel in 1X TBE containing 1X SYBR Safe.",
    "Load 5 µL PCR product + 1 µL 6X loading dye per well. Include a 100 bp DNA ladder lane.",
    "Run at 100 V for ~30 min, until the dye front is two-thirds down the gel.",
    "Image the gel on a blue-LED transilluminator with amber filter. Expected: single sharp band at ~655 bp. Upload the image to the PCR Process record.",
    "For clean single-band samples, submit 10–20 µL unpurified PCR product to a Sanger service (e.g. Plasmidsaurus Premium PCR) with FishF1 as the sequencing primer. Label tubes with the LibreBiotech Sample ID exactly.",
    "When sequences return, trim reads to Q20 and BLAST the consensus against BOLD (primary) and NCBI nr (secondary).",
    "Accept a species-level call if top hit ≥98% identity, query coverage ≥90%, and gap to next species ≥1%. Otherwise report to genus only.",
    "Log the BLAST call, accession, %ID, query coverage, and rationale on the Sample record. Set `mislabeled=true` when the call differs from the claimed species.",
]

EQUIPMENT_ROWS = [
    {"name": "Thermocycler",               "specifications": "25 µL tubes, programmable ramp, heated lid",                "notes": "Pi-controlled OpenPCR-compatible build; schematics in repo"},
    {"name": "Gel documentation system",   "specifications": "Blue-LED transilluminator + amber filter; Pi HQ camera",    "notes": "DIY build in repo; NOT UV"},
    {"name": "Heat block",                 "specifications": "56°C and 95–100°C capable",                                 "notes": ""},
    {"name": "Microcentrifuge",            "specifications": "≥12,000 × g",                                               "notes": "Benchtop"},
    {"name": "Gel electrophoresis system", "specifications": "Horizontal, ≥100 V PSU",                                    "notes": "Mini gel format"},
    {"name": "Pipettes",                   "specifications": "P10, P200, P1000",                                          "notes": "Calibrated; filter tips only"},
]

MATERIAL_ROWS = [
    {"type": "Chelating resin",    "product": None,                         "quantity": "200",  "unit": "µL",          "notes": "Bio-Rad 142-1253, 5% w/v in low-EDTA TE"},
    {"type": "Protease",           "product": "Proteinase K",               "quantity": "5",    "unit": "µL",          "notes": "NEB P8107S, 20 mg/mL"},
    {"type": "PCR master mix",     "product": None,                         "quantity": "12.5", "unit": "µL",          "notes": "NEB OneTaq 2X M0482S; alt: NEB Q5 2X"},
    {"type": "Oligonucleotide",    "product": "FishF1 primer, 10 µM",       "quantity": "0.25", "unit": "µL",          "notes": "IDT custom; 5'-TCAACCAACCACAAAGACATTGGCAC-3' (Ward 2005)"},
    {"type": "Oligonucleotide",    "product": "FishF2 primer, 10 µM",       "quantity": "0.25", "unit": "µL",          "notes": "IDT; 5'-TCGACTAATCATAAAGATATCGGCAC-3'"},
    {"type": "Oligonucleotide",    "product": "FishR1 primer, 10 µM",       "quantity": "0.25", "unit": "µL",          "notes": "IDT; 5'-TAGACTTCTGGGTGGCCAAAGAATCA-3'"},
    {"type": "Oligonucleotide",    "product": "FishR2 primer, 10 µM",       "quantity": "0.25", "unit": "µL",          "notes": "IDT; 5'-ACTTCAGGGTGACCGAAGAATCAGAA-3'"},
    {"type": "Agarose",            "product": None,                         "quantity": "0.4",  "unit": "g per gel",   "notes": "Molecular grade"},
    {"type": "Nucleic acid stain", "product": "SYBR Safe",                  "quantity": "1",    "unit": "X (final)",   "notes": "Invitrogen S33102 from 10,000X stock"},
    {"type": "Buffer",             "product": "1X TBE",                     "quantity": "500",  "unit": "mL per gel",  "notes": ""},
    {"type": "DNA ladder",         "product": "100 bp ladder",              "quantity": "5",    "unit": "µL per lane", "notes": "NEB N3231S"},
    {"type": "Loading dye",        "product": "6X gel loading dye",         "quantity": "1",    "unit": "µL per well", "notes": "NEB B7024S"},
    {"type": "Water",              "product": "Nuclease-free water",        "quantity": "q.s.", "unit": "µL",          "notes": "To 25 µL per reaction"},
]

REFERENCES = [
    {"citation": "Ward RD, Zemlak TS, Innes BH, Last PR, Hebert PDN (2005). DNA barcoding Australia's fish species. Phil Trans R Soc B 360:1847–57.",
     "doi": "10.1098/rstb.2005.1716", "url": None, "ref_type": "paper"},
    {"citation": "Folmer O, Black M, Hoeh W, Lutz R, Vrijenhoek R (1994). COI primers for invertebrates. Mol Mar Biol Biotechnol 3:294–9.",
     "doi": None, "url": None, "ref_type": "paper"},
    {"citation": "Shokralla S et al. (2015). Next-generation DNA barcoding: using nanopore sequencing to enhance species monitoring. Sci Rep 5:9687.",
     "doi": "10.1038/srep09687", "url": None, "ref_type": "paper"},
    {"citation": "Walsh PS, Metzger DA, Higuchi R (1991). Chelex 100 as a medium for simple extraction of DNA. BioTechniques 10:506–13.",
     "doi": None, "url": None, "ref_type": "paper"},
    {"citation": "BOLD Systems — Barcode of Life Data System",
     "doi": None, "url": "https://boldsystems.org", "ref_type": "other"},
    {"citation": "NCBI BLAST",
     "doi": None, "url": "https://blast.ncbi.nlm.nih.gov", "ref_type": "other"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api(method, path, **kwargs):
    key = os.environ.get("LIBREBIOTECH_API_KEY")
    if not key:
        sys.exit("error: set LIBREBIOTECH_API_KEY before running")
    headers = kwargs.pop("headers", {})
    headers["X-API-Key"] = key
    headers.setdefault("Content-Type", "application/json")
    resp = requests.request(method, f"{API_BASE}{path}", headers=headers, **kwargs)
    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text}
    return resp.status_code, body


def list_catalog():
    for endpoint, label in [
        ("/catalog/equipment-types",  "Equipment types"),
        ("/catalog/material-types",   "Material types"),
        ("/catalog/material-products", "Material products"),
    ]:
        code, body = api("GET", endpoint)
        print(f"\n=== {label}  ({endpoint})  HTTP {code} ===")
        print(json.dumps(body, indent=2, ensure_ascii=False))


def build_equipment():
    out, gaps = [], []
    for row in EQUIPMENT_ROWS:
        eid = EQUIPMENT_CATALOG_MAP.get(row["name"])
        if eid is None:
            gaps.append(f"equipment: {row['name']}")
            continue
        out.append({
            "equipment_type_id": eid,
            "specifications": row["specifications"],
            "notes": row["notes"],
        })
    return out, gaps


def build_materials():
    out, gaps = [], []
    for row in MATERIAL_ROWS:
        key = (row["type"], row["product"])
        type_id, product_id = MATERIAL_CATALOG_MAP.get(key, (None, None))
        if type_id is None:
            gaps.append(f"material: {key}")
            continue
        out.append({
            "material_type_id": type_id,
            "material_product_id": product_id,   # may be null for generic
            "quantity": row["quantity"],
            "unit": row["unit"],
            "notes": row["notes"],
        })
    return out, gaps


def build_payload():
    equipment, eq_gaps = build_equipment()
    materials, mat_gaps = build_materials()
    payload = {
        "title": TITLE,
        "description": DESCRIPTION,
        "category": CATEGORY,
        "visibility": VISIBILITY,
        "license": LICENSE,
        "url": EXTERNAL_URL,
        "initial_version": {
            "version_number": VERSION_NUMBER,
            "effective_date": EFFECTIVE_DATE,
            "change_log": CHANGELOG,
            "safety_text": SAFETY_TEXT,
            "preparation_notes_text": PREPARATION_TEXT,
            "timing_text": TIMING_TEXT,
            "completion_notes_text": COMPLETION_TEXT,
            "steps": [{"content": s} for s in STEPS],
            "equipment": equipment,
            "materials": materials,
            "references": REFERENCES,
        },
    }
    return payload, eq_gaps + mat_gaps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-catalog", action="store_true", help="Print catalog IDs and exit")
    ap.add_argument("--dry-run", action="store_true", help="Print payload; do not POST")
    args = ap.parse_args()

    if args.list_catalog:
        list_catalog()
        return

    payload, gaps = build_payload()
    if gaps:
        print("Catalog gaps (rows dropped from payload):", file=sys.stderr)
        for g in gaps:
            print(f"  - {g}", file=sys.stderr)
        print("Run --list-catalog to find IDs, update the MAP dicts at top of file.\n", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    code, body = api("POST", "/procedures", json=payload)
    print(f"HTTP {code}")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
