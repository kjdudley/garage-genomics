# COI DNA Barcoding for Consumer Fish Samples

**Version:** 0.1.0 (pilot)
**License:** CC-BY-4.0
**Status:** Pre-dry-run. Expect v0.1.x patches after end-to-end validation.

Identifies teleost fish to species via the Folmer COI barcode region using the Ward et al. 2005 primer cocktail. Designed for citizen-science fish-mislabeling studies on consumer sushi/sashimi samples.

**Not a clinical or regulatory-grade assay.** Results are for open-dataset research — not consumer complaints or legal action.

## What you'll need

**Equipment**
- Pi-controlled thermocycler (see `hardware/thermocycler/`)
- Pi-controlled blue-LED gel imager with amber filter (see `hardware/gel-imager/`)
- Heat block capable of 56 °C and 95–100 °C
- Microcentrifuge (≥ 12,000 × g)
- Horizontal gel electrophoresis rig + ≥ 100 V PSU
- P10, P200, P1000 pipettes with filter tips

**Reagents** (per 25 µL PCR reaction; order enough for n+1 samples including a no-template control)

| Item | Source | Per reaction |
|---|---|---|
| 5 % Chelex-100 in low-EDTA TE | Bio-Rad 142-1253 | 200 µL |
| Proteinase K 20 mg/mL | NEB P8107S | 5 µL |
| OneTaq 2X Master Mix | NEB M0482S | 12.5 µL |
| FishF1 primer 10 µM | IDT custom | 0.25 µL |
| FishF2 primer 10 µM | IDT custom | 0.25 µL |
| FishR1 primer 10 µM | IDT custom | 0.25 µL |
| FishR2 primer 10 µM | IDT custom | 0.25 µL |
| Agarose | Sigma A9539 | 0.4 g / gel |
| SYBR Safe | Invitrogen S33102 | 1× final |
| 1× TBE buffer | — | 500 mL / gel |
| 100 bp ladder | NEB N3231S | 5 µL / lane |
| 6× gel loading dye | NEB B7024S | 1 µL / well |
| Nuclease-free water | — | to 25 µL |

Primer sequences: `primers.fasta`.
Thermocycler program: `thermocycler-program.json`.

## Safety

- BSL-1 only. No human-subject, clinical, or regulated samples.
- 95 °C heat step requires a closed-lid heat block.
- Gloves and filter tips throughout; change gloves between extraction and PCR setup.
- SYBR Safe is a DNA intercalator — gloves, seal gel waste per local rules.
- Blue LED only, **not UV** — required if teaching in schools.

## Timing

- **Day 1 active wet lab, ~3.5 h:** extraction 45 min • PCR setup 15 min • cycling 2 h hands-off • gel 45 min
- **Day 1 → Day 3:** Sanger service turnaround (~24–48 h)
- **Day 3, ~1 h:** trim, BLAST, log

Chelex extract is best used fresh; store at −20 °C if delaying. Run the gel the same day as cycling.

## Procedure

### 1. Sample collection
Collect 2–3 tissue pieces per sample before sauces are applied. In your LibreBiotech Study, create a Sample record with claimed species, vendor, price, date/time, photo, and claim source.

### 2. Chelex extraction
1. Transfer ~20 mg tissue (rice-grain size) to a labeled 1.5 mL tube; cut into small fragments.
2. Add 200 µL freshly vortexed 5 % Chelex-100 and 5 µL 20 mg/mL Proteinase K.
3. Incubate 56 °C, 30 min. Vortex briefly at 15 min.
4. Incubate 95 °C, 10 min.
5. Vortex 10 s; centrifuge 12,000 × g, 2 min.
6. Transfer ~100 µL of the clear upper phase to a new tube, avoiding the Chelex pellet. This is the DNA template.

### 3. PCR
1. Prepare master mix for n+1 reactions including a no-template control. Per reaction: 12.5 µL OneTaq 2X, 0.5 µL F-mix (10 µM total), 0.5 µL R-mix (10 µM total), 10.5 µL water.
2. Aliquot 24 µL per tube. Add 1 µL template to sample tubes; 1 µL water to the NTC.
3. Cycle: 94 °C 2 min; 35× [94 °C 30 s, 52 °C 30 s, 72 °C 45 s]; 72 °C 10 min; 4 °C hold.
4. Export the Pi thermocycler temperature log and attach it to the PCR Process record in LibreBiotech.

### 4. Gel verification
1. Cast a 1.5 % agarose gel in 1× TBE with 1× SYBR Safe.
2. Load 5 µL PCR product + 1 µL loading dye; include a 100 bp ladder lane.
3. Run at 100 V for ~30 min until the dye front reaches ⅔ of the gel.
4. Image on the blue-LED transilluminator with amber filter. Upload the image to the PCR Process record.

Expected: a single sharp band at ~655 bp.

### 5. Sanger submission
Submit 10–20 µL unpurified PCR product to a Sanger service (e.g. Plasmidsaurus Premium PCR) with FishF1 as the sequencing primer. Label tubes with the LibreBiotech Sample ID exactly.

### 6. Analysis and species call
1. Trim reads to Q20.
2. BLAST consensus against [BOLD](https://boldsystems.org) (primary) and NCBI nr (secondary).
3. Accept a species-level call if: top hit ≥ 98 % identity, query coverage ≥ 90 %, gap to next species ≥ 1 %. Otherwise report to genus.
4. Log the call, accession, %ID, query coverage, and rationale on the Sample record. Set `mislabeled=true` when the call differs from the claim.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| No band (cooked sample) | DNA degraded | Mini-barcode primers (Shokralla 2015); extend PK to 2 h |
| Band in NTC | Contamination | Bleach bench, fresh aliquots, new tips — do not proceed |
| Multiple bands | Non-specific priming | Anneal at 54 °C; dilute template 1:10 |
| Smear | Template overload / degraded | Dilute Chelex extract 1:10 |
| Low Sanger quality | Primer-dimer / carryover | Request cleanup; or gel-extract the 655 bp band |
| Ambiguous BLAST (top two within 1 %) | Closely related species | Report to genus; note on Sample record |

## Submitting to LibreBiotech

This protocol is versioned on LibreBiotech and submitted via `scripts/submit_coi_protocol.py`. See that script's docstring for the workflow.

## References

- Ward RD, Zemlak TS, Innes BH, Last PR, Hebert PDN (2005). DNA barcoding Australia's fish species. *Phil Trans R Soc B* 360:1847–57. [doi:10.1098/rstb.2005.1716](https://doi.org/10.1098/rstb.2005.1716)
- Folmer O, Black M, Hoeh W, Lutz R, Vrijenhoek R (1994). COI primers for invertebrates. *Mol Mar Biol Biotechnol* 3:294–9.
- Shokralla S et al. (2015). Next-generation DNA barcoding via nanopore sequencing. *Sci Rep* 5:9687. [doi:10.1038/srep09687](https://doi.org/10.1038/srep09687)
- Walsh PS, Metzger DA, Higuchi R (1991). Chelex 100 as a medium for simple extraction of DNA. *BioTechniques* 10:506–13.
- [BOLD Systems](https://boldsystems.org)
- [NCBI BLAST](https://blast.ncbi.nlm.nih.gov)
