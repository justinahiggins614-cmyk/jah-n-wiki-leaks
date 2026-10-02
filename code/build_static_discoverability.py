#!/usr/bin/env python3
"""Build static discoverability artifacts for JAH-N Wiki (site 5/9 polish pass 3).

Regenerates, from the on-disk data (single source of truth):
  1. The STATIC crawlable bizarre-dossier count block in index.html
     (between <!-- STATIC-COUNT-START --> / <!-- STATIC-COUNT-END --> markers),
     with "as of YYYY-MM-DD" and a note on what it counts.
  2. sitemap-records-1.xml — one URL per bizarre dossier (?dossier=JAH-LEAK-B######).
  3. api.json records_approx / records_as_of.

The page's JS live counters keep reading the same data at runtime; the static
block is for curl / crawlers / machines that don't run JavaScript.

Called at the end of code/drip_bizarre.py; also runnable standalone.
"""
import gzip
import json
import os
import re
import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/"
BASE_DIR = os.path.join(REPO, "data", "bizarre.json")
CHUNK_DIR = os.path.join(REPO, "data", "bizarre", "chunks")
INDEX = os.path.join(REPO, "index.html")
SITEMAP = os.path.join(REPO, "sitemap-records-1.xml")
API = os.path.join(REPO, "api.json")


def collect_ids():
    ids = []
    with open(BASE_DIR, encoding="utf-8") as fh:
        for rec in json.load(fh):
            ids.append(rec["id"])
    for fn in sorted(os.listdir(CHUNK_DIR)):
        if not fn.endswith(".json.gz"):
            continue
        with gzip.open(os.path.join(CHUNK_DIR, fn), "rt", encoding="utf-8") as fh:
            for rec in json.load(fh):
                ids.append(rec["id"])
    return ids


def fmt(n):
    return "{:,}".format(n)


def main():
    ids = collect_ids()
    total = len(ids)
    # user-facing date in the user's own timezone (EDT), matching all project logs
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).date().isoformat()

    block = (
        '<!-- STATIC-COUNT-START -->\n'
        '<div class="crawlcount" id="crawlcount">\n'
        '<b>\u25a0 <span id="crawlcount-n">' + fmt(total) + '</span> BIZARRE DOSSIERS</b> '
        '(counted in this page&#8217;s static HTML as of <span id="crawlcount-d">' + today + '</span>)<br>\n'
        '<span class="crawlsub">What this counts: bizarre-subject dossiers with permanent '
        'JAH-LEAK-B###### IDs (the base set plus the drip-fed case files, ' + ids[0] + '&#8211;' + ids[-1] + '). '
        'Spec dossiers and public-patent dossiers mirrored on this page are counted separately in their home '
        'catalogs (Signature Spec Catalog, Globally Rejustered Patent Catalog). '
        'The live counters above refresh from the same data on every visit.</span>\n'
        '</div>\n'
        '<!-- STATIC-COUNT-END -->'
    )
    html = open(INDEX, encoding="utf-8").read()
    new_html, n = re.subn(
        r"<!-- STATIC-COUNT-START -->.*?<!-- STATIC-COUNT-END -->",
        block,
        html,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("static count markers not found exactly once in index.html")
    open(INDEX, "w", encoding="utf-8").write(new_html)
    print(f"index.html static count: {fmt(total)} as of {today}")

    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for did in ids:
        sm.append(f"  <url><loc>{SITE}?dossier={did}</loc><changefreq>monthly</changefreq></url>")
    sm.append("</urlset>")
    open(SITEMAP, "w", encoding="utf-8").write("\n".join(sm) + "\n")
    print(f"sitemap-records-1.xml: {fmt(total)} URLs")

    api = json.load(open(API, encoding="utf-8"))
    api["records_approx"] = total
    api["records_as_of"] = today
    json.dump(api, open(API, "w", encoding="utf-8"), indent=2)
    open(API, "a", encoding="utf-8").write("\n")
    print(f"api.json: records_approx={fmt(total)} as_of={today}")


if __name__ == "__main__":
    main()
