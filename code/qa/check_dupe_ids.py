#!/usr/bin/env python3
"""TIER 2-8 checker: duplicate IDs across and within every dossier source.
Sources: data/bizarre.json, data/bizarre/bizarre.idx.json.gz, every chunk row,
data/patents.idx.json.gz.
Note: idx<->chunks overlap is BY DESIGN (index rows point at chunk rows holding
the same IDs), so only WITHIN-source dupes, or bizarre.json-vs-drip-range
overlap, are real problems. Usage: python3 code/qa/check_dupe_ids.py."""
import json, gzip, glob, sys
from collections import Counter

REPO = "/home/hatch/workspace/jah-n-wiki-leaks"

def main():
    errs = []
    # per-source dupes
    def per_source(name, ids):
        c = Counter(ids)
        return [(name, i, n) for i, n in c.items() if n > 1]
    biz = json.load(open(REPO + "/data/bizarre.json"))
    biz_ids = [r["id"] for r in biz]
    idx_ids = []
    for line in gzip.open(REPO + "/data/bizarre/bizarre.idx.json.gz"):
        line = line.strip()
        if line:
            idx_ids.append(json.loads(line)[0])
    chunk_ids = []
    for f in glob.glob(REPO + "/data/bizarre/chunks/*.json.gz"):
        chunk_ids += [r["id"] for r in json.loads(gzip.open(f).read().decode())]
    pat_ids = []
    for line in gzip.open(REPO + "/data/patents.idx.json.gz"):
        line = line.strip()
        if line:
            pat_ids.append(json.loads(line)[0])
    for name, ids in [("bizarre.json", biz_ids), ("bizarre.idx", idx_ids),
                      ("chunks", chunk_ids), ("patents.idx", pat_ids)]:
        for n, i, k in per_source(name, ids):
            errs.append("WITHIN-source dupe: %s %s x%d" % (n, i, k))
    # bizarre.json range (B0001-B0120) must not overlap drip range (B0121+)
    biz_set, idx_set = set(biz_ids), set(idx_ids)
    overlap = biz_set & idx_set
    if overlap:
        errs.append("bizarre.json overlaps drip idx: %s" % sorted(overlap)[:10])
    overlap2 = biz_set & set(chunk_ids)
    if overlap2:
        errs.append("bizarre.json overlaps chunks: %s" % sorted(overlap2)[:10])
    # chunk set must equal idx set exactly (same IDs, no extras)
    if set(chunk_ids) != idx_set:
        errs.append("chunk ID set != idx ID set (%d vs %d)" % (len(set(chunk_ids)), len(idx_set)))
    print("bizarre.json: %d ids | idx: %d ids | chunks: %d ids | patents: %d ids" % (
        len(biz_set), len(idx_set), len(set(chunk_ids)), len(set(pat_ids))))
    if errs:
        print("PROBLEMS:")
        for e in errs[:25]:
            print("  " + e)
        return 1
    print("no duplicate IDs")
    return 0

if __name__ == "__main__":
    sys.exit(main())
