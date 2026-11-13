# Changelog

Semantic versioning read for data: major = schema change that breaks
parsers; minor = new objects or quantities; patch = corrections.

## [1.0.0] - 2026-11
### Added
- Confirmed HdC catalogue: 235 objects (192 RCB, 7 hot RCB, 36 dLHdC) with
  Gaia DR3 ids, ICRS positions, SIMBAD identifiers.
- Classification history (classification.csv) with per-event methods and ADS
  references; references.bib with historical roots (Pigott 1797, Espin 1890).
- Schema (controlled vocabularies) + CI validator + release builder.
- Scaffolding (not yet populated) for the stage-2 monitoring registry and
  enrichment tables.

### Deferred to later releases (stage 2)
- Monitoring registry (ToI follow-up, candidates, light-curve monitoring).
- Enrichment: aliases, Crawford temperatures, extinctions, distances,
  maximum-light magnitudes.
- Extreme-helium and DY Per classes.
