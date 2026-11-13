# Monitoring registry — three source files, one logical table

Candidates and follow-up targets live in three source-partitioned files that
share a common column schema (validated as one logical table):

| file | holds | source-specific columns |
|---|---|---|
| `data/T2020_RCB-ToI_monitoring.csv` | Tisserand et al. 2020 ToIs & candidates | `toi_number`, `priority_group`, `followup_method`, `spec_date` |
| `data/T2022_dLHdC_Candidates_monitoring.csv` | Tisserand et al. 2022 dLHdC candidates | `dlhdc_group`, `shell_flag` |
| `data/OtherSources_RCB_Candidates_monitoring.csv` | candidates from other papers | `origin_survey` |

**Common columns (required in all three):**
`name, gaia_dr3_source_id, ra_deg, dec_deg, source, status, nature,
ref_bibcode, public, monitor, comment`

- `status`: pending | weak_candidate | strong_candidate | confirmed | rejected
- `nature`: for rejected — Mira | RVTau | M_star | YSO | carbon_star | … (blank otherwise)
- `public`: true → may be published; false → held back (unpublished/your priority)
- `monitor`: true → fed to the Fink watchlist

The validator checks all three against the shared schema + vocabulary, and
rejects a `gaia_dr3_source_id` that appears in more than one file (one home
per object). A monitoring object whose gaia id is already in `core.csv`
(a graduated object) gets a warning — `core.csv` is authoritative.

## Build outputs (`python3 scripts/build_release.py --version X.Y.Z`)

Public (safe to publish):
- `build/core_public.csv` — the confirmed catalogue
- `build/candidates_public.csv` — `public=true` candidates, minus graduates
- `build/core_fink.csv` — what the public Fink module loads (catalogue + public candidates)

Private (LOCAL ONLY — feeds rcbmon, never published):
- `build/monitoring_watchlist.csv` — every `monitor=true` object (core + all
  three files), deduped by gaia id, with a `public` column so you see what is
  held back. Point rcbmon at this file.

## Graduation rule
When a candidate becomes confirmed, add it to `core.csv` and set its registry
row `status=confirmed` (keep the row — it preserves the selection-function
record). The build dedups by gaia id so it is published once, via the
catalogue, never double-counted as a candidate.
