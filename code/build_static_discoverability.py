#!/usr/bin/env python3
"""Build static discoverability artifacts for Wiki Leaks (site 5/9 polish pass 3).

Regenerates, from the on-disk data (single source of truth):
  1. The STATIC crawlable bizarre-dossier count block in index.html
     (between <!-- STATIC-COUNT-START --> / <!-- STATIC-COUNT-END --> markers),
     with "as of YYYY-MM-DD" and a note on what it counts.
  2. sitemap-records-1.xml — one URL per bizarre dossier (?dossier=JAH-LEAK-B######).
  3. api.json records_approx / records_as_of.
  4. FIX-SITE5-2: chunked incremental JSON feed of the newest 1,000 dossiers
     (data/bizarre/feed/index.json + feed-0001.json ... 250/chunk, newest first),
     plus sitemap-recent.xml (the same 1,000 dossier URLs) registered in
     sitemap-index.xml, so scrapers catch each +1,000 drip batch without
     pagination pain.
  5. FIX-SITE5-3: pre-rendered static fallback index pages —
     categories.html (per-category counts + top 25 dossiers each, anchor links)
     and recent.html (newest 100 dossiers, anchor links) — for non-JS crawlers.

The page's JS live counters keep reading the same data at runtime; the static
artifacts are for curl / crawlers / machines that don't run JavaScript.

Called at the end of code/drip_bizarre.py; also runnable standalone.
"""
import gzip
import json
import os
import re
import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/"
BASE_FILE = os.path.join(REPO, "data", "bizarre.json")
CHUNK_DIR = os.path.join(REPO, "data", "bizarre", "chunks")
INDEX = os.path.join(REPO, "index.html")
SITEMAP = os.path.join(REPO, "sitemap-records-1.xml")
SITEMAP_RECENT = os.path.join(REPO, "sitemap-recent.xml")
SITEMAP_INDEX = os.path.join(REPO, "sitemap-index.xml")
API = os.path.join(REPO, "api.json")
FEED_DIR = os.path.join(REPO, "data", "bizarre", "feed")
FEED_CHUNK_SIZE = 250
FEED_KEEP = 1000

STATIC_CSS = """
body{background:#0e1626;color:#e9effc;font-family:"Courier New",ui-monospace,Menlo,Consolas,monospace;
font-size:14px;line-height:1.6;max-width:1000px;margin:0 auto;padding:24px 16px}
a{color:#3dff78}a:hover{color:#ffb000}
h1{color:#ffb000;letter-spacing:3px;font-size:22px}
h2{color:#ff95a0;letter-spacing:2px;font-size:16px;margin-top:28px;border-bottom:1px solid #2c3f66;padding-bottom:6px}
.c{color:#a9bce4;font-size:12px}.n{color:#ffb000;font-weight:bold}
ul{list-style:none;padding:0}li{margin:6px 0}.id{color:#ffb000;font-size:12px}
.note{border:1px solid #2c3f66;background:#182642;padding:12px 16px;margin:16px 0;font-size:12px;color:#a9bce4}
.jahnet{background:#0a0a0a;border-bottom:1px solid #3a0d0d;color:#8a8f7a;font-size:.76em;padding:6px 10px;text-align:center;line-height:2;letter-spacing:.02em}
.jahnet-t{color:#ff4444;font-weight:700;letter-spacing:.25em;margin-right:10px}
.jahnet a{color:#7aaa7a;text-decoration:none;margin:0 7px;white-space:nowrap}
.jahnet a:hover{text-decoration:underline}
.jahnet-here{color:#ff4444;font-weight:700;letter-spacing:.2em;border:1px solid #ff4444;padding:1px 8px;margin-left:10px;white-space:nowrap;display:inline-block}
.sitekicker{color:#ff4444;font-weight:700;letter-spacing:.2em;font-size:.85em;border:1px solid #ff4444;padding:1px 8px;margin-right:10px;white-space:nowrap;display:inline-block}
"""

JAHNET_NAV = """
<!-- JAH NETWORK: bottom nav, above footer (one instance per page) -->
<nav aria-label="JAH Network Global Ecosystem" role="navigation"><div class="jahnet"><span class="jahnet-t">THE JAH NETWORK</span><span class="sitekicker">SITE 5 OF 27</span><a href="https://justinahiggins614-cmyk.github.io/signature-math/">1 Signature Math</a><a href="https://justinahiggins614-cmyk.github.io/jah-calculator/">2 Signature Universal Paradox Immune Calculator</a><a href="https://justinahiggins614-cmyk.github.io/jah-dictionary/">3 The Signature Dictionary</a><a href="https://justinahiggins614-cmyk.github.io/jah-wiki/">4 JAH Wiki</a><a href="https://justinahiggins614-cmyk.github.io/signature-llama/">6 Signature Llama: The Fully Cyber Utilizable AI</a><a href="https://justinahiggins614-cmyk.github.io/jah-ai-models/">7 The Signature AI Phone Book</a><a href="https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/">8 Globally Rejustered Patent Catalog</a><a href="https://justinahiggins614-cmyk.github.io/signature-one-archive/specs.html">9 Signature Spec Catalog Pending Patents</a><a href="https://justinahiggins614-cmyk.github.io/jah-computer-systems/">10 The Signature PC System Depository</a><a href="https://justinahiggins614-cmyk.github.io/signature-books/">11 The Signature Book Depository</a><a href="https://justinahiggins614-cmyk.github.io/signature-comics/">12 The Signature Comic Store</a><a href="https://justinahiggins614-cmyk.github.io/signature-newspapers/">13 The Signature Global Newspaper Archive</a><a href="https://justinahiggins614-cmyk.github.io/signature-backend/">14 The Signature AI Mad Scientist Creation Lab</a><a href="https://justinahiggins614-cmyk.github.io/signature-boundless-generators/">15 The Signature Boundless Generator Archive</a><a href="https://justinahiggins614-cmyk.github.io/signature-ai-mixlab/">16 The Signature AI Mix Lab</a><a href="https://justinahiggins614-cmyk.github.io/signature-ai-olypics/">17 AI Olympics</a><a href="https://justinahiggins614-cmyk.github.io/signature-chip-maker/">18 The Signature Computer Chip Maker and Archive</a><a href="https://justinahiggins614-cmyk.github.io/signature-app-archive/">19 The Signature App Archive</a><a href="https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/">20 The Signature AI Robot Matcher</a><a href="https://justinahiggins614-cmyk.github.io/signature-experiment-solver/">21 The Signature Experiment Solver</a><a href="https://justinahiggins614-cmyk.github.io/signature-ai-image-video-maker/">22 Signature AI Pixel</a><a href="https://justinahiggins614-cmyk.github.io/signature-ai-song-maker/">23 Signature Music Studio</a><a href="https://justinahiggins614-cmyk.github.io/signature-fixit/">24 The Signature Mr Fix-It</a><a href="https://justinahiggins614-cmyk.github.io/signature-university/">25 The Signature University</a><a href="https://justinahiggins614-cmyk.github.io/signature-cyber-mega-mall/">26 The Signature Cyber Mega-Mall</a><a href="https://justinahiggins614-cmyk.github.io/signature-3d-print/">27 The Signature 3D Print Mega Mall</a><span class="jahnet-here">5 JAH-N Wiki Leaks — YOU ARE HERE</span></div></nav>
"""


def collect_ids():
    ids = []
    with open(BASE_FILE, encoding="utf-8") as fh:
        for rec in json.load(fh):
            ids.append(rec["id"])
    for fn in sorted(os.listdir(CHUNK_DIR)):
        if not fn.endswith(".json.gz"):
            continue
        with gzip.open(os.path.join(CHUNK_DIR, fn), "rt", encoding="utf-8") as fh:
            for rec in json.load(fh):
                ids.append(rec["id"])
    return ids


def id_num(did):
    m = re.search(r"(\d+)$", did or "")
    return int(m.group(1)) if m else 0


def collect_records():
    """Compact rows for the incremental feed + static fallback pages."""
    recs = []
    with open(BASE_FILE, encoding="utf-8") as fh:
        for r in json.load(fh):
            recs.append({
                "id": r["id"], "subject": r.get("subject", ""),
                "category": r.get("category", ""), "classification": r.get("classification", ""),
                "date_filed": r.get("date_filed", ""), "chunk": None,
            })
    for fn in sorted(os.listdir(CHUNK_DIR)):
        if not fn.endswith(".json.gz"):
            continue
        with gzip.open(os.path.join(CHUNK_DIR, fn), "rt", encoding="utf-8") as fh:
            for r in json.load(fh):
                recs.append({
                    "id": r["id"], "subject": r.get("subject", ""),
                    "category": r.get("category", ""), "classification": r.get("classification", ""),
                    "date_filed": r.get("date_filed", ""), "chunk": fn[:-len(".json.gz")],
                })
    recs.sort(key=lambda r: id_num(r["id"]), reverse=True)
    return recs


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fmt(n):
    return "{:,}".format(n)


def static_page(title, h1, body_html, note):
    return ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
            "<title>" + esc(title) + "</title><style>" + STATIC_CSS + "</style></head><body>"
            "<h1>" + esc(h1) + "</h1>"
            "<div class=\"note\">" + note + "</div>"
            + body_html +
            "<div class=\"note\">INTERNAL SIGNATURE ARCHIVE — NOT A GOVERNMENT ARCHIVE. "
            "NOT AFFILIATED WITH ANY GOVERNMENT AGENCY. Official within the JAH-N system only.</div>"
            + JAHNET_NAV + "</body></html>")


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

    # ---- FIX-SITE5-2: incremental chunked JSON feed (newest dossiers first) ----
    recs = collect_records()
    recent = recs[:FEED_KEEP]
    os.makedirs(FEED_DIR, exist_ok=True)
    # wipe stale feed chunks (chunk count changes as the archive grows)
    for fn in os.listdir(FEED_DIR):
        if fn.startswith("feed-") and fn.endswith(".json"):
            os.remove(os.path.join(FEED_DIR, fn))
    feed_chunks = []
    for i in range(0, len(recent), FEED_CHUNK_SIZE):
        chunk = recent[i:i + FEED_CHUNK_SIZE]
        fname = "feed-%04d.json" % (i // FEED_CHUNK_SIZE + 1)
        rows = [[r["id"], r["subject"], r["category"], r["classification"],
                 r["date_filed"], r["chunk"], SITE + "?dossier=" + r["id"]] for r in chunk]
        with open(os.path.join(FEED_DIR, fname), "w", encoding="utf-8") as fh:
            json.dump({"chunk": fname, "generated": today,
                       "count": len(rows),
                       "id_range": [chunk[0]["id"], chunk[-1]["id"]],
                       "columns": ["id", "subject", "category", "classification",
                                   "date_filed", "chunk", "deep_link"],
                       "rows": rows}, fh, ensure_ascii=False)
        feed_chunks.append({"file": fname, "count": len(rows),
                            "id_range": [chunk[0]["id"], chunk[-1]["id"]]})
    feed_index = {"feed": "Wiki Leaks incremental dossier feed",
                  "generated": today,
                  "total_bizarre": total,
                  "feed_chunks": feed_chunks,
                  "note": ("Newest dossiers first, 250 per chunk. The 2h bizarre drip regenerates this "
                           "feed, so scrapers can diff index.json against their last fetch to find new files.")}
    with open(os.path.join(FEED_DIR, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(feed_index, fh, ensure_ascii=False, indent=1)
    print(f"feed: {len(feed_chunks)} chunks, {fmt(len(recent))} newest dossiers")

    # sitemap-recent.xml for the same newest batch, registered in the sitemap index
    rsm = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for r in recent:
        rsm.append(f"  <url><loc>{SITE}?dossier={r['id']}</loc><changefreq>daily</changefreq></url>")
    rsm.append("</urlset>")
    open(SITEMAP_RECENT, "w", encoding="utf-8").write("\n".join(rsm) + "\n")
    sidx = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <sitemap><loc>{SITE}sitemap.xml</loc></sitemap>\n'
            f'  <sitemap><loc>{SITE}sitemap-records-1.xml</loc></sitemap>\n'
            f'  <sitemap><loc>{SITE}sitemap-recent.xml</loc></sitemap>\n'
            '</sitemapindex>\n')
    open(SITEMAP_INDEX, "w", encoding="utf-8").write(sidx)
    print(f"sitemap-recent.xml: {fmt(len(recent))} URLs; sitemap-index.xml updated")

    # ---- FIX-SITE5-3: static fallback index pages ----
    cats = {}
    for r in recs:
        cats.setdefault(r["category"] or "UNCATEGORIZED", []).append(r)
    cat_body = ""
    for cat in sorted(cats):
        rows = cats[cat]
        cat_body += ("<h2>" + esc(cat) + " — <span class=\"n\">" + fmt(len(rows)) + "</span> dossiers</h2><ul>")
        for r in rows[:25]:
            cat_body += ("<li><span class=\"id\">" + esc(r["id"]) + "</span> "
                         "<a href=\"" + SITE + "?dossier=" + esc(r["id"]) + "\">" + esc(r["subject"]) + "</a></li>")
        if len(rows) > 25:
            cat_body += ("<li class=\"c\">…and " + fmt(len(rows) - 25) +
                         " more in this category (see the sitemap or the JSON feed)</li>")
        cat_body += "</ul>"
    cat_page = static_page(
        "Wiki Leaks — Category Index (static)",
        "▓ JAH-N WIKI — DOSSIER CATEGORY INDEX (STATIC)",
        "<p class=\"c\">" + fmt(total) + " bizarre dossiers across " + str(len(cats)) +
        " categories, as of " + today + ". Top 25 per category shown; every link opens the live file.</p>" + cat_body,
        "Static fallback for non-JS crawlers and AI indexers. Live counters on the main page refresh from the same data.")
    with open(os.path.join(REPO, "categories.html"), "w", encoding="utf-8") as fh:
        fh.write(cat_page)
    print(f"categories.html: {len(cats)} categories")

    rec_body = "<ul>"
    for r in recent[:100]:
        rec_body += ("<li><span class=\"id\">" + esc(r["id"]) + "</span> "
                     "<a href=\"" + SITE + "?dossier=" + esc(r["id"]) + "\">" + esc(r["subject"]) + "</a> "
                     "<span class=\"c\">— " + esc(r["category"]) + "</span></li>")
    rec_body += "</ul>"
    rec_page = static_page(
        "Wiki Leaks — Newest Files (static)",
        "▓ JAH-N WIKI — NEWEST 100 DOSSIERS (STATIC)",
        "<p class=\"c\">The 100 most recent bizarre dossiers, as of " + today + ".</p>" + rec_body,
        "Static fallback for non-JS crawlers and AI indexers. Regenerated by the 2h bizarre drip.")
    with open(os.path.join(REPO, "recent.html"), "w", encoding="utf-8") as fh:
        fh.write(rec_page)
    print("recent.html: newest 100 dossiers")

    # robots.txt: point crawlers at the incremental feed
    robots = os.path.join(REPO, "robots.txt")
    rt = open(robots, encoding="utf-8").read()
    feed_line = "# Incremental dossier feed (newest first, chunked JSON): " + SITE + "data/bizarre/feed/index.json"
    if feed_line not in rt:
        rt = rt.rstrip("\n") + "\n" + feed_line + "\n"
        open(robots, "w", encoding="utf-8").write(rt)
        print("robots.txt: feed reference added")

    api = json.load(open(API, encoding="utf-8"))
    api["records_approx"] = total
    api["records_as_of"] = today
    api["incremental_feed"] = SITE + "data/bizarre/feed/index.json"
    api["static_fallbacks"] = [SITE + "categories.html", SITE + "recent.html", SITE + "browse.html"]
    json.dump(api, open(API, "w", encoding="utf-8"), indent=2)
    open(API, "a", encoding="utf-8").write("\n")
    print(f"api.json: records_approx={fmt(total)} as_of={today}")

    # ---- A-Z archive: per-letter lazy chunks + browse.html (count stamped) ----
    # Runs AFTER the index/state flush in the drip, so the A-Z counts are always
    # current with this run — never one run behind.
    import build_az_archive as baz
    baz.main()


if __name__ == "__main__":
    main()
