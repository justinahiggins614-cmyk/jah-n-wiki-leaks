#!/usr/bin/env python3
"""QA: static discoverability artifacts (site 5/9 polish pass 3).

Checks:
  - index.html has the static crawlable count block between the markers and the
    number matches the on-disk data (bizarre.json + chunks), with an "as of"
    date and a note on what is counted.
  - sitemap-records-1.xml lists one URL per bizarre dossier ID, contiguous, no dupes.
  - robots.txt has no Disallow and points at the sitemap index.
  - index.html has a canonical link and site-level JSON-LD (WebSite/CreativeWork).
  - index.html has the #methodology section restating both disclaimers.

Exit 0 = pass, 1 = findings. Run from the repo root.
"""
import gzip
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = "https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/"
findings = []


def note(m):
    findings.append(m)


def collect_ids():
    ids = []
    for rec in json.load(open(os.path.join(REPO, "data", "bizarre.json"), encoding="utf-8")):
        ids.append(rec["id"])
    cd = os.path.join(REPO, "data", "bizarre", "chunks")
    for fn in sorted(os.listdir(cd)):
        if fn.endswith(".json.gz"):
            for rec in json.load(gzip.open(os.path.join(cd, fn), "rt", encoding="utf-8")):
                ids.append(rec["id"])
    return ids


ids = collect_ids()
total = len(ids)
html = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()

# 1. static count block
m = re.search(r"<!-- STATIC-COUNT-START -->(.*?)<!-- STATIC-COUNT-END -->", html, re.S)
if not m:
    note("static count block missing")
else:
    block = m.group(1)
    n = re.search(r'<span id="crawlcount-n">([\d,]+)</span>', block)
    if not n or int(n.group(1).replace(",", "")) != total:
        note(f"static count mismatch: block={n.group(1) if n else None} data={total}")
    if "as of" not in block.lower() and "as of" not in block:
        note("static count block lacks 'as of' date note")
    if not re.search(r'<span id="crawlcount-d">[\d-]+', block):
        note("static count block lacks as-of date span")
    if "counted separately" not in block.lower():
        note("static count block lacks note on what is counted (spec/patent counted separately)")

# 2. sitemap
sm = open(os.path.join(REPO, "sitemap-records-1.xml"), encoding="utf-8").read()
urls = re.findall(r"<loc>(.*?)</loc>", sm)
expected = [f"{SITE}?dossier={d}" for d in ids]
if sorted(urls) != sorted(expected):
    missing = set(expected) - set(urls)
    extra = set(urls) - set(expected)
    note(f"sitemap mismatch: {len(urls)} urls vs {total} ids, missing={len(missing)}, extra={len(extra)}")
if len(urls) != len(set(urls)):
    note("sitemap contains duplicate URLs")

# 3. robots
robots = open(os.path.join(REPO, "robots.txt"), encoding="utf-8").read()
if re.search(r"(?m)^Disallow:\s*/\s*$", robots):
    note("robots.txt disallows crawling")
if "sitemap-index.xml" not in robots and "sitemap.xml" not in robots:
    note("robots.txt does not point at the sitemap")

# 4. canonical + JSON-LD
if '<link id="canon" rel="canonical"' not in html:
    note("canonical link missing")
if '"@type":"WebSite"' not in html and '"@type": "WebSite"' not in html:
    note("site JSON-LD (WebSite) missing")
if "ld-dossier" not in html:
    note("per-dossier JSON-LD injection (openDossier) missing")

# 5. methodology section + disclaimers
mm = re.search(r'<section class="method" id="methodology"(.*?)</section>', html, re.S)
if not mm:
    note("#methodology section missing")
else:
    sec = mm.group(0)
    if "CREATIVE SIMULATION — NOT A GOVERNMENT ARCHIVE" not in sec:
        note("methodology lacks 'CREATIVE SIMULATION — NOT A GOVERNMENT ARCHIVE'")
    if "NOT AFFILIATED WITH ANY GOVERNMENT AGENCY" not in sec:
        note("methodology lacks 'NOT AFFILIATED WITH ANY GOVERNMENT AGENCY'")
    for term in ("JAH-LEAK-B######", "FILE CLASSIFICATION", "PROVENANCE", "v1.0", "never re-used"):
        if term not in sec:
            note(f"methodology lacks expected term: {term}")

# 6. real <a> links for cards + browse
if 'class="fcard' not in html or 'href="?dossier=' not in html:
    note("dossier cards are not real <a> links")
if 'href="?az=' not in html:
    note("A-Z browse links missing")

if findings:
    print("FINDINGS:")
    for f in findings:
        print(" -", f)
    sys.exit(1)
print(f"PASS: static count {total:,}, sitemap {len(urls)} urls, robots ok, JSON-LD ok, methodology ok, links ok")
