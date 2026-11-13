#!/usr/bin/env python3
"""Validate the catalogue + monitoring registry.

Checks: column sets; required non-empty; controlled vocabularies (whitespace
trimmed; 'multi' columns split and each token checked); booleans; ra/dec
ranges; ADS bibcode syntax (+ presence in references.bib); foreign keys to
core.csv. For the monitoring files (group: monitoring) it additionally
verifies they share the common columns and that no gaia_dr3_source_id is
duplicated ACROSS the three files, and warns when a monitoring object's
gaia id already exists in core.csv (a graduated object -> core is
authoritative; see build_release.py dedup).

    python3 scripts/validate.py
"""
import argparse
import csv
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

BIBCODE_RE = re.compile(
    r"^\d{4}[A-Za-z0-9&.]{5}[A-Za-z0-9.]{4}[A-Za-z.][0-9A-Za-z.]{4}[A-Za-z]$")
ARXIV_RE = re.compile(r"^\d{4}arXiv\d{6,}[A-Za-z]$")
TRUE_FALSE = {"true", "false"}
# columns every monitoring file must carry (the shared schema)
MONITORING_COMMON = ["name", "gaia_dr3_source_id", "ra_deg", "dec_deg",
                     "source", "status", "nature", "ref_bibcode",
                     "public", "monitor", "comment"]

errors, warnings = [], []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    with open(os.path.join(a.root, "schema/columns.yml")) as fh:
        schema = yaml.safe_load(fh)
    with open(os.path.join(a.root, "schema/vocabularies.yml")) as fh:
        vocab = yaml.safe_load(fh)

    bib_path = os.path.join(a.root, "data/references.bib")
    known_bib = set(re.findall(r"@\w+\{([^,]+),", open(bib_path).read())) \
        if os.path.exists(bib_path) else set()
    if not known_bib:
        warnings.append("data/references.bib not found or empty")

    core_names, core_gaia, tables = set(), set(), {}
    monitoring_gaia = {}  # gaia id -> (file, name)  for cross-file dup check

    for tname, tdef in schema.items():
        path = os.path.join(a.root, tdef["file"])
        if not os.path.exists(path):
            errors.append(f"{tdef['file']} missing")
            continue
        rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
        tables[tname] = rows
        expected = list(tdef["columns"].keys())
        if rows and list(rows[0].keys()) != expected:
            errors.append(f"{tdef['file']}: columns {list(rows[0].keys())} "
                          f"!= schema {expected}")
            continue

        is_mon = tdef.get("group") == "monitoring"
        if is_mon:
            miss = [c for c in MONITORING_COMMON if c not in tdef["columns"]]
            if miss:
                errors.append(f"{tdef['file']}: missing common columns {miss}")

        for i, row in enumerate(rows, 2):
            for col, cdef in tdef["columns"].items():
                val = (row.get(col) or "").strip()
                where = f"{tdef['file']}:{i} [{col}]"
                if val != (row.get(col) or ""):
                    warnings.append(f"{where} has leading/trailing whitespace")
                if not val:
                    if cdef.get("required"):
                        errors.append(f"{where} required value empty")
                    continue
                if cdef.get("dtype") == "bool":
                    if val.lower() not in TRUE_FALSE:
                        errors.append(f"{where} '{val}' not true/false")
                if "vocab" in cdef:
                    toks = ([t.strip() for t in val.split(cdef["multi"])]
                            if cdef.get("multi") else [val])
                    for t in toks:
                        if t and t not in vocab.get(cdef["vocab"], {}):
                            errors.append(f"{where} '{t}' not in vocab "
                                          f"'{cdef['vocab']}'")
                if cdef.get("dtype") in ("float", "int"):
                    try:
                        float(val) if cdef["dtype"] == "float" else int(val)
                    except ValueError:
                        errors.append(f"{where} '{val}' not {cdef['dtype']}")
                if col == "ra_deg" and _num(val) is not None and not 0 <= float(val) < 360:
                    errors.append(f"{where} RA out of range")
                if col == "dec_deg" and _num(val) is not None and not -90 <= float(val) <= 90:
                    errors.append(f"{where} Dec out of range")
                if col == "ref_bibcode":
                    if not (BIBCODE_RE.match(val) or ARXIV_RE.match(val)):
                        errors.append(f"{where} '{val}' not a valid bibcode")
                    elif known_bib and val not in known_bib:
                        errors.append(f"{where} bibcode '{val}' absent from "
                                      f"references.bib")

            if tname == "core":
                nm = (row.get("name") or "").strip()
                core_names.add(nm)
                sid = (row.get("gaia_dr3_source_id") or "").strip()
                if sid and sid.lower() != "no detection":
                    core_gaia.add(sid)
            if is_mon:
                sid = (row.get("gaia_dr3_source_id") or "").strip()
                if sid and sid.lower() != "no detection":
                    if sid in monitoring_gaia:
                        pf, pn = monitoring_gaia[sid]
                        errors.append(f"{tdef['file']}:{i} gaia {sid} "
                                      f"('{row.get('name')}') duplicates "
                                      f"{pf} ('{pn}')")
                    monitoring_gaia[sid] = (tdef["file"], row.get("name"))

    # foreign keys for non-monitoring satellite tables
    for tname, tdef in schema.items():
        if tdef.get("foreign_key") == "name" and tname in tables:
            for i, row in enumerate(tables[tname], 2):
                if row.get("name") and row["name"] not in core_names:
                    errors.append(f"{tdef['file']}:{i} name '{row['name']}' "
                                  f"not in core.csv")

    # monitoring gaia ids that already exist in core (graduated objects)
    for sid, (f, n) in monitoring_gaia.items():
        if sid in core_gaia:
            warnings.append(f"{f}: '{n}' gaia {sid} also in core.csv "
                            f"(graduated; core is authoritative at build)")

    # core uniqueness
    if "core" in tables:
        seen, seen_sid = set(), {}
        for i, row in enumerate(tables["core"], 2):
            nm = row["name"]
            if nm in seen:
                errors.append(f"core.csv:{i} duplicate name '{nm}'")
            seen.add(nm)
            sid = (row.get("gaia_dr3_source_id") or "").strip()
            if sid and sid.lower() != "no detection":
                if sid in seen_sid:
                    errors.append(f"core.csv:{i} gaia {sid} dup of "
                                  f"'{seen_sid[sid]}'")
                seen_sid[sid] = nm

    for w in warnings:
        print(f"WARNING  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print(f"\ncore: {len(tables.get('core', []))} objects | "
          f"monitoring: {sum(len(tables.get(t, [])) for t in schema if schema[t].get('group')=='monitoring')} rows | "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    sys.exit(main())
