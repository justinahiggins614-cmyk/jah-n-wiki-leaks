#!/usr/bin/env python3
"""check_provenance.py — dossier integrity: every dossier must carry the
provenance fields the page promises (ID, subject, classification, category,
filed date, and a SOURCES section for bizarre files).

Streams chunks + data/bizarre.json. Exit 0 = pass, 1 = findings.
"""
import gzip
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CHUNKS = os.path.join(ROOT, "data", "bizarre", "chunks")
MAIN = os.path.join(ROOT, "data", "bizarre.json")

REQUIRED = ["id", "subject", "classification", "category", "date_filed"]
REQUIRED_BIZ_SOURCES = True  # bizarre dossiers must have a sources section

findings = []
total = 0
seen = set()


def check(d, where):
    global total
    total += 1
    did = d.get("id", "?")
    if did in seen:
        findings.append(f"DUPE ID {did} at {where}")
    seen.add(did)
    for f in REQUIRED:
        if not d.get(f):
            findings.append(f"MISSING {f} on {did} at {where}")
    if REQUIRED_BIZ_SOURCES and d.get("kind", "bizarre") == "bizarre":
        if not d.get("sources"):
            findings.append(f"MISSING sources section on {did} at {where}")


def main():
    if os.path.exists(MAIN):
        with open(MAIN, encoding="utf-8") as fh:
            data = json.load(fh)
        for d in (data if isinstance(data, list) else [data]):
            if isinstance(d, dict):
                check(d, "data/bizarre.json")
    for f in sorted(glob.glob(os.path.join(CHUNKS, "*.json.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                batch = json.loads(line)
                for d in (batch if isinstance(batch, list) else [batch]):
                    if isinstance(d, dict):
                        check(d, os.path.basename(f))
    print(f"checked {total} dossiers, {len(findings)} findings")
    for x in findings[:25]:
        print(" -", x)
    if len(findings) > 25:
        print(f" ... and {len(findings)-25} more")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
