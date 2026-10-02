#!/usr/bin/env python3
"""TIER 2-8 checker: link audit for jah-n-wiki-leaks/index.html.
Extracts every outbound URL (href, fetch targets, JS constants incl. SPEC_SITE
composites) and checks HTTP status against the LIVE site.
Usage: python3 code/qa/check_links.py [--root index.html]
Exit 0 = no dead links; 1 = failures found."""
import re, sys, urllib.request, urllib.error

REPO = "/home/hatch/workspace/jah-n-wiki-leaks"
LIVE = "https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/"
SPEC_SITE = "https://justinahiggins614-cmyk.github.io/signature-one-archive/"

def get(url, timeout=25):
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "JAH-QA-linkcheck/1.0"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, "ok"
    except urllib.error.HTTPError as e:
        if e.code in (405, 501):  # HEAD not allowed -> try GET
            try:
                req2 = urllib.request.Request(url, headers={"User-Agent": "JAH-QA-linkcheck/1.0"})
                r2 = urllib.request.urlopen(req2, timeout=timeout)
                r2.read(1); r2.close()
                return r2.status, "ok-via-GET"
            except Exception as e2:
                return None, "GET failed: %s" % e2
        return e.code, "http error"
    except Exception as e:
        return None, str(e)[:120]

def main():
    path = sys.argv[2] if "--root" in sys.argv else REPO + "/index.html"
    html = open(path, encoding="utf-8").read()
    urls = set()
    # static href/src
    for m in re.findall(r'''(?:href|src)=["']([^"'#]+)["']''', html):
        m = m.strip()
        if m.startswith(("http://", "https://", "//")):
            urls.add("https:" + m if m.startswith("//") else m)
        elif m and not m.startswith(("data:", "mailto:", "javascript:", "./", "#")):
            urls.add(LIVE + m)
    # JS-declared constants: SPEC_SITE composites
    urls.add(SPEC_SITE)                      # SPEC_SITE itself
    urls.add(SPEC_SITE + "data/index/shards.json")   # loadSpecShards
    urls.add(SPEC_SITE + "specs.html")        # spec deep-link base
    # relative data files used by the page (resolve against live)
    for rel in ("data/bizarre/shards.json", "data/bizarre/bizarre.idx.json.gz",
                "data/bizarre.json", "data/patents.idx.json.gz", "robots.txt",
                "sitemap.xml", "api.json"):
        urls.add(LIVE + rel)
    # cross-site deep-link targets used by wikiURL()/patentDossier()
    urls.add("https://justinahiggins614-cmyk.github.io/jah-wiki/")
    urls.add("https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/")
    # canonical JAH NETWORK destinations (TIER 1-2)
    urls.update([
        "https://justinahiggins614-cmyk.github.io/jah-ai-models/",
        "https://justinahiggins614-cmyk.github.io/jah-calculator/",
        "https://justinahiggins614-cmyk.github.io/jah-dictionary/",
        "https://justinahiggins614-cmyk.github.io/jah-wiki/",
        "https://justinahiggins614-cmyk.github.io/jah-n-wiki-leaks/",
        "https://justinahiggins614-cmyk.github.io/cyber-patent-catalog/",
        "https://justinahiggins614-cmyk.github.io/signature-one-archive/specs.html",
        "https://justinahiggins614-cmyk.github.io/signature-llama/",
        "https://justinahiggins614-cmyk.github.io/jah-computer-systems/",
    ])
    # TTS failover tiers (failover is fine if one is down, but log status)
    tts = [
        "https://code.responsivevoice.org/getvoice.php?t=test&tl=en-US",
        "https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q=test",
        "https://translate.googleapis.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q=test",
    ]
    bad, ok = [], 0
    for u in sorted(urls):
        st, note = get(u)
        if st and 200 <= st < 400:
            ok += 1
        else:
            bad.append((u, st, note))
    tts_stat = []
    for u in tts:
        st, note = get(u)
        tts_stat.append((u.split("?")[0], st, note))
    print("checked: %d ok, %d BAD" % (ok, len(bad)))
    for u, st, note in bad:
        print("  DEAD: %s -> %s (%s)" % (u, st, note))
    for host, st, note in tts_stat:
        print("  tts tier %s -> %s" % (host, st if st else "unreachable (%s)" % note))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
