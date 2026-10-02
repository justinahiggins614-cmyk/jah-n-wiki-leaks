#!/usr/bin/env python3
"""TIER 2-8 checker: missing IDs / chunk coverage for bizarre dossiers.
Verifies:
  1. bizarre.json holds a contiguous B0001..B0120 block with required fields.
  2. every bizarre.idx row's chunk file exists under data/bizarre/chunks/ and
     contains the ID (sample-verifies all chunks' row counts, full-verifies by
     loading each chunk once).
  3. idx IDs form the contiguous B0121.. range with no gaps.
Usage: python3 code/qa/check_missing_ids.py (takes ~20s on 28k rows)."""
import json, gzip, glob, sys, os

REPO = "/home/hatch/workspace/jah-n-wiki-leaks"
REQ = ["id", "kind", "subject", "classification", "overview", "assessment"]

def main():
    errs = []
    biz = json.load(open(REPO + "/data/bizarre.json"))
    nums = sorted(int(r["id"].split("-B")[-1]) for r in biz if r["id"].startswith("JAH-LEAK-B"))
    if nums != list(range(1, len(nums) + 1)):
        errs.append("bizarre.json ID range not contiguous 1..%d: %s" % (
            len(nums), nums[:5]))
    for r in biz:
        missing = [k for k in REQ if not r.get(k)]
        if missing:
            errs.append("bizarre.json %s missing fields %s" % (r.get("id"), missing))
    idx = []
    for line in gzip.open(REPO + "/data/bizarre/bizarre.idx.json.gz"):
        line = line.strip()
        if line:
            idx.append(json.loads(line))
    inums = sorted(int(r[0].split("-B")[-1]) for r in idx if r[0].startswith("JAH-LEAK-B"))
    if inums:
        expect = list(range(inums[0], inums[0] + len(inums)))
        if inums != expect:
            gaps = [a for a in expect if a not in set(inums)][:10]
            errs.append("idx ID range B%06d.. has %d gaps (first: %s)" % (
                inums[0], len(expect) - len(inums), ["B%06d" % g for g in gaps]))
    # chunk coverage
    by_chunk = {}
    for r in idx:
        by_chunk.setdefault(r[3], []).append(r[0])
    missing_files, missing_ids, bad_rows = 0, [], 0
    for chunk, ids in sorted(by_chunk.items()):
        path = REPO + "/data/bizarre/chunks/" + chunk + ".json.gz"
        if not os.path.exists(path):
            errs.append("chunk file missing: %s (covers %d ids)" % (chunk, len(ids)))
            missing_files += 1
            continue
        try:
            rows = json.loads(gzip.open(path).read().decode())
        except Exception as e:
            errs.append("chunk %s unreadable: %s" % (chunk, e)); continue
        have = set(r["id"] for r in rows)
        for i in ids:
            if i not in have:
                missing_ids.append((chunk, i))
        for r in rows:
            if not r.get("id") or not r.get("subject"):
                bad_rows += 1
    if missing_ids:
        errs.append("%d idx IDs not found in their chunk file (first: %s)" % (
            len(missing_ids), missing_ids[:5]))
    if bad_rows:
        errs.append("%d chunk rows missing id/subject" % bad_rows)
    print("bizarre.json: %d rows, B%06d..B%06d" % (len(biz), min(nums) if nums else 0, max(nums) if nums else 0))
    print("idx: %d rows, B%06d..B%06d across %d chunk files" % (len(idx), inums[0] if inums else 0, inums[-1] if inums else 0, len(by_chunk)))
    if errs:
        print("PROBLEMS:")
        for e in errs[:25]:
            print("  " + e)
        return 1
    print("no missing IDs; chunk coverage complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
