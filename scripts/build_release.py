#!/usr/bin/env python3
"""Build release + monitoring products from data/.

Published (public) products
  build/core_public.csv            the confirmed HdC catalogue (= core.csv)
  build/candidates_public.csv      monitoring rows with public=true and a
                                   candidate status, minus any already in
                                   core (deduped by gaia_dr3_source_id)
  build/core_fink.csv              what the public Fink module loads:
                                   core + public candidates (name, ra, dec,
                                   class/status), deduped

Private product (DO NOT publish; feeds rcbmon locally)
  build/monitoring_watchlist.csv   every row with monitor=true across core +
                                   all three registry files, deduped by
                                   gaia id (core authoritative), with a
                                   'public' column so you can see what is
                                   held back

The three registry files are concatenated (union) and deduped against core
by gaia_dr3_source_id: a graduated object is published via the catalogue,
never double-counted as a candidate.

    python3 scripts/build_release.py --version 1.0.0
"""
import argparse
import csv
import datetime
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required")

CANDIDATE_STATUS = {"weak_candidate", "strong_candidate", "pending"}


def read(path):
    return list(csv.DictReader(open(path, newline="", encoding="utf-8"))) \
        if os.path.exists(path) else []


def truthy(v):
    return (v or "").strip().lower() == "true"


def gid(row):
    s = (row.get("gaia_dr3_source_id") or "").strip()
    return "" if s.lower() in ("", "no detection") else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    root, out = a.root, os.path.join(a.root, "build")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(root, "schema/columns.yml")) as fh:
        schema = yaml.safe_load(fh)

    core = read(os.path.join(root, "data/core.csv"))
    core_gaia = {gid(r) for r in core if gid(r)}
    mon_files = [t["file"] for t in schema.values()
                 if t.get("group") == "monitoring"]
    monitoring = []
    for f in mon_files:
        for r in read(os.path.join(root, f)):
            r["_srcfile"] = os.path.basename(f)
            monitoring.append(r)

    # 1. public catalogue = core.csv
    _write(os.path.join(out, "core_public.csv"),
           [r for r in core], list(core[0].keys()) if core else [])
    print(f"  build/core_public.csv  ({len(core)} confirmed)")

    # 2. public candidates: public=true, candidate status, NOT already in core
    cand_cols = ["name", "gaia_dr3_source_id", "ra_deg", "dec_deg", "source",
                 "status", "ref_bibcode", "comment"]
    pub_cand, seen = [], set()
    for r in monitoring:
        if (truthy(r.get("public")) and r.get("status") in CANDIDATE_STATUS
                and gid(r) not in core_gaia):
            g = gid(r)
            if g and g in seen:
                continue
            if g:
                seen.add(g)
            pub_cand.append({k: r.get(k, "") for k in cand_cols})
    _write(os.path.join(out, "candidates_public.csv"), pub_cand, cand_cols)
    print(f"  build/candidates_public.csv  ({len(pub_cand)} public candidates)")

    # 3. Fink module catalogue: core (class) + public candidates (status)
    fink_cols = ["name", "ra_deg", "dec_deg", "class", "class_confidence"]
    fink = [{k: r.get(k, "") for k in fink_cols} for r in core]
    for r in pub_cand:
        fink.append({"name": r["name"], "ra_deg": r["ra_deg"],
                     "dec_deg": r["dec_deg"], "class": "RCB_candidate",
                     "class_confidence": r["status"]})
    _write(os.path.join(out, "core_fink.csv"), fink, fink_cols)
    print(f"  build/core_fink.csv  ({len(fink)} rows: public catalogue + candidates)")

    # 4. PRIVATE monitoring watchlist: monitor=true across core + registry,
    #    deduped by gaia id (core authoritative).
    watch_cols = ["name", "gaia_dr3_source_id", "ra_deg", "dec_deg", "source",
                  "status", "public", "comment"]
    watch, wseen = [], set()
    for r in core:                      # core objects are always monitored
        g = gid(r)
        if g:
            wseen.add(g)
        watch.append({"name": r.get("name", ""),
                      "gaia_dr3_source_id": r.get("gaia_dr3_source_id", ""),
                      "ra_deg": r.get("ra_deg", ""), "dec_deg": r.get("dec_deg", ""),
                      "source": "catalogue", "status": "confirmed",
                      "public": "true", "comment": ""})
    for r in monitoring:
        if not truthy(r.get("monitor")):
            continue
        g = gid(r)
        if g and g in wseen:            # already in core -> skip (dedup)
            continue
        if g:
            wseen.add(g)
        watch.append({"name": r.get("name", ""),
                      "gaia_dr3_source_id": r.get("gaia_dr3_source_id", ""),
                      "ra_deg": r.get("ra_deg", ""), "dec_deg": r.get("dec_deg", ""),
                      "source": r.get("source", ""), "status": r.get("status", ""),
                      "public": r.get("public", ""), "comment": r.get("comment", "")})
    _write(os.path.join(out, "monitoring_watchlist.csv"), watch, watch_cols)
    n_priv = sum(1 for w in watch if not truthy(w["public"]))
    print(f"  build/monitoring_watchlist.csv  ({len(watch)} to monitor, "
          f"{n_priv} private)  [LOCAL ONLY - do not publish]")

    with open(os.path.join(out, "VERSION"), "w") as fh:
        fh.write(f"{a.version}\n{datetime.datetime.now().isoformat()}\n")
    print(f"\nRelease {a.version} built.")


def _write(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
