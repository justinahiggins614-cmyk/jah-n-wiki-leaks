#!/usr/bin/env python3
"""TIER 2-8 checker: counts in data vs what the page will display.
Derives every number from the data files (never hardcoded) and verifies:
  - state.json counter == bizarre.idx rows == sum(chunk rows)
  - page's bizarre total formula: len(bizarre.json) + idx rows (disjoint ID ranges)
Usage: python3 code/qa/check_counts.py ; exit 0 = consistent, 1 = mismatch."""
import json, gzip, glob, sys

REPO = "/home/hatch/workspace/jah-n-wiki-leaks"

def load_idx_rows():
    rows = []
    for line in gzip.open(REPO + "/data/bizarre/bizarre.idx.json.gz"):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows

def main():
    errs = []
    state = json.load(open(REPO + "/data/bizarre/state.json"))
    biz = json.load(open(REPO + "/data/bizarre.json"))
    idx = load_idx_rows()
    chunk_files = sorted(glob.glob(REPO + "/data/bizarre/chunks/*.json.gz"))
    chunk_rows = 0
    for f in chunk_files:
        rows = json.loads(gzip.open(f).read().decode())
        chunk_rows += len(rows)
    pats = [l for l in gzip.open(REPO + "/data/patents.idx.json.gz").read().decode().splitlines() if l.strip()]
    print("bizarre.json rows      : %d" % len(biz))
    print("bizarre.idx rows      : %d" % len(idx))
    print("chunk rows total      : %d  (%d chunk files)" % (chunk_rows, len(chunk_files)))
    print("state.json counter    : %d  (next_id=%s next_chunk=%s)" % (state["counter"], state["next_id"], state["next_chunk"]))
    print("patents.idx rows      : %d" % len(pats))
    biz_total = len(biz) + len(idx)   # page formula: BIZ.length + BIZIDX.length
    print("page BIZARRE total    : %d  (bizarre.json + idx)" % biz_total)
    if state["counter"] != len(idx):
        errs.append("state.counter (%d) != idx rows (%d)" % (state["counter"], len(idx)))
    if len(idx) != chunk_rows:
        errs.append("idx rows (%d) != chunk rows (%d)" % (len(idx), chunk_rows))
    # idx first-column IDs vs chunk coverage is checked by check_missing_ids; here range sanity:
    ids = [r[0] for r in idx]
    n = [int(i.split("-B")[-1]) for i in ids if i.startswith("JAH-LEAK-B")]
    if n:
        print("idx ID range          : B%06d .. B%06d (n=%d)" % (min(n), max(n), len(n)))
    if errs:
        print("MISMATCH:")
        for e in errs:
            print("  " + e)
        return 1
    print("counts consistent")
    return 0

if __name__ == "__main__":
    sys.exit(main())
