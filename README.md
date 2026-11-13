# A catalogue of R Coronae Borealis and dustless HdC stars

Positions, classifications and literature provenance for the known
**R Coronae Borealis (RCB)**, **hot RCB** and **dustless HdC (dLHdC)** stars
of the Milky Way and the Magellanic Clouds. Companion to
[rcb.iap.fr](https://rcb.iap.fr).

**v1.0 — 235 confirmed objects** (192 RCB, 7 hot RCB, 36 dLHdC).

Every classification carries its provenance: the paper that proposed each
object and the paper that confirmed it, with ADS bibcodes. Each release is
archived with a DOI.

## Contents (v1)
| file | what it is |
|---|---|
| `data/core.csv` | one row per confirmed star: name, Gaia DR3 id, ICRS position, class, confidence, host galaxy, SIMBAD id |
| `data/classification.csv` | classification history — one row per event (proposed / confirmed / strong_candidate / reclassified) with method and reference |
| `data/references.bib` | one BibTeX entry per ADS bibcode used |
| `schema/` | column definitions and controlled vocabularies, enforced by CI |
| `scripts/validate.py` | validation gate (run before every commit) |
| `scripts/build_release.py` | generates the release products in `build/` |

A monitoring registry (candidate follow-up, light-curve monitoring) and
enrichment tables (aliases, temperatures, extinctions) are scaffolded for a
later release — see the stage-2 to-do.

## Columns (core.csv)
`name, gaia_dr3_source_id, ra_deg, dec_deg, class, class_confidence,
location, rcb_iap_url, simbad_id, comment`
- `class`: RCB | Hot_RCB | dLHdC
- `class_confidence`: confirmed | strong_candidate
- SIMBAD URL = `https://simbad.cds.unistra.fr/simbad/sim-id?Ident=` + URL-encoded `simbad_id`

## Build & validate
```
pip install pyyaml
python3 scripts/validate.py            # must report 0 errors
python3 scripts/build_release.py --version 1.0.0
```

## Citation
Cite the Zenodo DOI (see CITATION.cff). Data are CC BY 4.0; scripts MIT.
