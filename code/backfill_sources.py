#!/usr/bin/env python3
"""Backfill the SOURCES, WITNESSES & REFERENCES section into existing bizarre dossiers.

Reads code/subject_sources.json (built by the research coordinator) and stamps
a "sources" field onto every dossier in data/bizarre.json and
data/bizarre/chunks/*.json.gz, keyed by base subject name.

Safe to re-run: overwrites the field deterministically. If the sources DB is
missing, it exits without touching anything.
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_bizarre as G

DATA = os.path.join(HERE, "..", "data")
CHUNKS = os.path.join(DATA, "bizarre", "chunks")
MAIN = os.path.join(DATA, "bizarre.json")


def patch_list(items):
    n = 0
    for d in items:
        if not isinstance(d, dict):
            continue
        txt = G.sources_text(d.get("subject", ""))
        if txt and d.get("sources") != txt:
            d["sources"] = txt
            n += 1
        elif txt and "sources" not in d:
            d["sources"] = txt
            n += 1
    return n


def main():
    if not G._load_sources():
        print("subject_sources.json missing or empty — nothing to do.")
        return
    print(f"sources DB: {len(G._load_sources())} subjects")
    total = 0
    if os.path.exists(MAIN):
        with open(MAIN, encoding="utf-8") as fh:
            data = json.load(fh)
        items = data if isinstance(data, list) else [data]
        # data/bizarre.json is a list of dossier dicts
        n = patch_list(items)
        with open(MAIN, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False)
        print(f"bizarre.json: {n} dossiers stamped")
        total += n
    for fn in sorted(os.listdir(CHUNKS)):
        if not fn.endswith(".json.gz"):
            continue
        p = os.path.join(CHUNKS, fn)
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        out_lines, n = [], 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, list):
                n += patch_list(obj)
            elif isinstance(obj, dict):
                n += patch_list([obj])
            out_lines.append(json.dumps(obj, ensure_ascii=False))
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            fh.write("\n".join(out_lines) + "\n")
        print(f"{fn}: {n} dossiers stamped")
        total += n
    print(f"TOTAL: {total} dossiers stamped with sources")


if __name__ == "__main__":
    main()
