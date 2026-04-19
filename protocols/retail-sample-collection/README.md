# Retail tissue collection for mislabeling studies

**Version:** 0.1.0 (pilot)
**License:** CC-BY-4.0
**Category:** sample_prep
**Status:** Pre-dry-run. Ships alongside `coi-fish-barcoding` for the Sushi Truth pilot.

Standardised collection of retail fish and seafood tissue (sushi, sashimi, fillets) for downstream species-ID. Captures the vendor's labelled species at purchase time as the *a priori claim*; that claim is preserved alongside the post-measurement BLAST call so mislabel audits always have both values visible. Upstream of the COI barcoding protocol (or any other species-ID assay you run in LibreBiotech).

**Not a food-safety or regulatory workflow.** Results are for open-dataset research — not consumer complaints or legal action.

## What you'll need

**Field kit** (no reagents)

- Smartphone or camera with timestamped image metadata (EXIF)
- Cooler bag with ice, ≥ 2 h cold-chain capacity
- 1.5–2 mL sample tubes, one per planned sample plus 20 % spares
- Sterile disposable picks, toothpicks, or single-use scalpels — one per sample
- Waterproof marker and pre-printed labels (or pre-labelled tubes)
- Field log (paper or mobile spreadsheet) — one row per sample

**Target species list.** Know in advance which taxa you're testing claims against — BLAST coverage against BOLD / NCBI nr is uneven across clades. For COI barcoding of teleost fish, Ward et al. 2005 is a solid reference set.

## Safety

- Buy samples you or others would normally eat. Discard the remaining tissue after excising the subsample if you don't intend to consume the rest.
- **Labelling discipline in the field.** Mislabeled tubes cascade into wrong BLAST calls downstream. Pre-print labels and cross-check tube → log → LibreBiotech Sample ID before moving on to the next vendor.
- **Cold chain.** Keep tissue on ice from purchase until it reaches a freezer or extraction bench. Fresh at ambient is acceptable for ≤ 4 h if the extraction is same-day; otherwise −20 °C immediately.
- **No cross-contamination.** Change gloves between samples. Fresh pick or scalpel per sample — do not re-use.

## Timing

- **Per sample, ~3–5 minutes** (longer at busy vendors if photography is constrained)
- **Market trip total, 30–90 minutes** depending on sample count
- **Cold-chain budget:** ≤ 4 h ambient before extraction or freezer; frozen indefinitely

## Procedure

### 1. Session setup
Record the market trip metadata in your field log before purchasing anything: vendor / market name, location, date, session start time, collector.

### 2. For each candidate sample

1. **Photograph the claim.** Capture the vendor's label, menu entry, or display-case signage showing the claimed species — with the vendor name visible in frame.
2. **Purchase the sample.** Retain the receipt; photograph it separately. The receipt timestamp is part of the audit trail.
3. **Assign a unique Sample ID** from your pre-printed label pool (e.g. `SashimiPilot-001`). Record it in the field log alongside vendor, claimed species as written, price, and purchase time.
4. **Photograph the piece.** One shot of the purchased piece with the Sample ID label visible. This is the physical provenance chain.
5. **Excise ~20 mg tissue** (rice-grain size) into the labelled tube using a fresh pick or scalpel. Close tightly.
6. **Place in cooler.** Use a foam rack or zip bag to keep tubes off direct ice contact.
7. **Change gloves, dispose of the used pick.** Do not re-use utensils across samples.

### 3. Session close
1. Seal the cooler and return to lab or home freezer.
2. Register each Sample in LibreBiotech via `create_samples_from_csv.py` with the session's collection Process as `process_id` (one Process per market trip) and the Sushi Truth Study attached via `study_ids`.
3. Upload photos to a public image store (e.g. the garage-genomics GitHub repo) and capture the URL as annotation slot `photo_ref` on each Sample.

## Completion notes

Per-sample deliverables at session end:
- Labelled tube in the cooler, ~20 mg excised tissue
- LibreBiotech Sample record pre-registered with:
  - `samples.organism_curie` = NCBITaxon claim (what the vendor labelled it)
  - annotations: `collected_at`, `vendor`, `purchase_price` + `unit_curie` (currency), `photo_ref` URL
- One or more photos with EXIF timestamp *preceding* the sample's `created_at` in LibreBiotech (this is the audit story — claim preceded any measurement)

**Record the claim as-labelled, not as-interpreted.** Transliterate Japanese menu names, vernacular names, or vague labels (e.g. "white fish") verbatim. Do not guess the scientific species until post-BLAST — that defeats the whole claim-vs-measurement design.

## Submitting to LibreBiotech

This protocol is versioned on LibreBiotech and submitted via `scripts/submit_retail_collection_protocol.py`. See that script's docstring for the workflow.

## Related

- [`coi-fish-barcoding`](../coi-fish-barcoding/README.md) — the downstream species-ID assay the Sushi Truth pilot uses on tissue collected via this protocol.

## References

- Ward RD, Zemlak TS, Innes BH, Last PR, Hebert PDN (2005). DNA barcoding Australia's fish species. *Phil Trans R Soc B* 360:1847–57. [doi:10.1098/rstb.2005.1716](https://doi.org/10.1098/rstb.2005.1716)
- [BOLD Systems — Barcode of Life Data System](https://boldsystems.org)
- [NCBI BLAST](https://blast.ncbi.nlm.nih.gov)
