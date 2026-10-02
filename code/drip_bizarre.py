#!/usr/bin/env python3
"""JAH-N Wiki Leaks — append-only bizarre dossier drip.

Adds BATCH new bizarre dossiers per run toward the 1,000,000 wiki-file
milestone. Storage is chunked (250 dossiers per gz chunk) with an index,
so the page lazy-loads. State is append-only: ids and chunks never repeat.

Usage: python3 code/drip_bizarre.py [batch]
"""
import gzip
import json
import os
import random
import re
import sys
from datetime import date

import generate_bizarre as G

HERE = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(HERE, "..", "data", "bizarre")
CHUNKDIR = os.path.join(DATADIR, "chunks")
STATEDIR = DATADIR
STATE = os.path.join(STATEDIR, "state.json")
IDX = os.path.join(DATADIR, "bizarre.idx.json.gz")
SHARDS = os.path.join(DATADIR, "shards.json")
CHUNK_SIZE = 250
TODAY = date.today().isoformat()

# ------------------------------------------------------- topic engine ----
ASPECTS = [
    ("Origins & First Reports", ["origin", "first report", "history", "discovery"],
     "Where the {s} file begins: the earliest credible reports, how the story entered the record, and what the first investigators actually documented before the legend grew."),
    ("Evidence File", ["evidence", "photograph", "sample", "measurement"],
     "The physical case for {s}: photographs, samples, instrument readings, and forensic traces — graded piece by piece, strongest first, with chain-of-custody notes where they exist."),
    ("Scientific Analysis", ["science", "physics", "analysis", "mechanism"],
     "The {s} file under laboratory conditions: candidate mechanisms, energy budgets, and material constraints. What would have to be true for the reports to describe a real phenomenon?"),
    ("Cultural Impact", ["culture", "media", "film", "society"],
     "How {s} colonized the human imagination: films, books, news cycles, and folklore. The cultural footprint is itself evidence — of psychology, of marketing, and occasionally of something real underneath."),
    ("Declassified Timeline", ["declassified", "timeline", "document", "archive"],
     "A chronological file of every declassified or leaked document touching {s}: dates, agencies, redactions, and what the censors chose to hide — which is often more informative than the text."),
    ("Field Guide", ["field guide", "identify", "sightings", "track"],
     "A practical field guide to {s}: identification markers, typical conditions of encounter, geographic clusters, seasonal patterns, and how to document a sighting so the file can use it."),
    ("Witness Archive", ["witness", "testimony", "interview", "account"],
     "Voices from the {s} archive: witness testimony collected across decades, scored for consistency, detail, and corroboration. Patterns across independent witnesses are the signal; lone spectaculars are noise."),
    ("Mechanism Study", ["mechanism", "engineering", "how it works", "build"],
     "If {s} is real, how does it work? This study decomposes the reported effects into candidate mechanisms and matches each against the JAH Spec Catalog's buildable inventory."),
    ("Comparative Cases", ["compare", "similar", "worldwide", "cases"],
     "{s} is not alone. This file compares parallel cases worldwide — same signature, different continent — and asks what a global pattern implies about cause."),
    ("Research Frontier", ["research", "unknown", "frontier", "future"],
     "The open questions of the {s} file: what would settle it, what instruments are needed, and which experiments the JAH-N system has queued. The file stays open until the math closes it."),
    ("Incident Reports", ["incident", "report", "encounter", "event"],
     "Selected incident reports from the {s} file: dated encounters with multiple witnesses or instrument data, presented as filed — without embellishment, without dismissal."),
    ("Containment Protocols", ["protocol", "safety", "procedure", "response"],
     "If {s} is real, how should a responsible agency handle it? Proposed observation, safety, and response protocols — the file the authorities would write if they admitted the file exists."),
]

LOCATIONS = ["Nevada desert", "Scottish Highlands", "Amazon basin", "Siberian taiga", "outback Australia",
             "Pacific Northwest", "Sahara fringe", "Himalayan foothills", "Baltic coast", "Andes highlands",
             "Congo basin", "Arctic circle", "Mojave", "Carpathian mountains", "Gobi fringe",
             "Appalachian hollers", "Sahara", "Patagonia", "Borneo interior", "Icelandic lava fields",
             "Ozark mountains", "Namib desert", "Kamchatka", "Atlas mountains", "Yucatan jungle",
             "Finnish lakeland", "Mongolian steppe", "Welsh valleys", "Kyushu mountains", "Drakensberg",
             "Alaskan interior", "Tibetan plateau", "Norwegian fjords", "Madagascar highlands", "Sonoran desert",
             "Ural foothills", "Pilbara", "Corsican maquis", "Ethiopian highlands", "Chihuahuan desert",
             "Vosges", "Altai mountains", "Kalahari", "Pyrenees", "Tian Shan", "Guiana shield",
             "Zagros mountains", "Great Basin", "Flinders Ranges", "Caucasus"]
YEARS = list(range(1947, 2027))


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"next_id": 121, "next_chunk": 1, "counter": 0}


def save_state(st):
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(st, fh)


def load_spec_rows():
    rows = G.load_spec_rows()
    print(f"  {len(rows)} spec rows loaded", flush=True)
    return rows


def build_token_index(rows):
    idx = {}
    for i, r in enumerate(rows):
        text = ((r[1] or "") + " " + (r[2] or "")).lower()
        for tok in set(re.findall(r"[a-z]{4,}", text)):
            lst = idx.get(tok)
            if lst is None:
                idx[tok] = [i]
            elif len(lst) < 400:
                lst.append(i)
    print(f"  token index: {len(idx)} tokens", flush=True)
    return idx


def make_fast_find(rows, index):
    def find_specs(_rows, keywords, n=4):
        cand = {}
        for kw in keywords:
            for tok in re.findall(r"[a-z]{4,}", kw.lower()):
                for i in index.get(tok, ()):
                    cand[i] = cand.get(i, 0) + 1
        scored = []
        for i in cand:
            r = rows[i]
            text = ((r[1] or "") + " " + (r[2] or "")).lower()
            s = sum(text.count(k.lower()) for k in keywords)
            if s > 0:
                scored.append((s, r))
        scored.sort(key=lambda x: -x[0])
        out, seen = [], set()
        for s, r in scored:
            if r[0] in seen:
                continue
            seen.add(r[0])
            out.append({"spec_id": r[0], "title": r[1], "category": r[3] or "",
                        "line": r[12] or "", "score": s})
            if len(out) >= n:
                break
        return out
    return find_specs


def dossier_for(n, next_id, subjects):
    rng = random.Random(n)
    NS, NA = len(subjects), len(ASPECTS)
    s_idx = n % NS
    a_idx = (n // NS) % NA
    case = n // (NS * NA) + 1
    cat, subject, _overview, keywords = subjects[s_idx]
    aspect, aspect_kw, aspect_blurb = ASPECTS[a_idx]
    loc = rng.choice(LOCATIONS)
    year = rng.choice(YEARS)
    witnesses = rng.choice([3, 7, 12, 23, 40, 60, 100])
    if case == 1:
        subj_line = f"{subject} — {aspect}"
    else:
        subj_line = f"{subject} — {aspect} — Case #{case:04d}"
    overview = (
        f"{aspect_blurb.format(s=subject)} "
        f"This installment draws on {witnesses} catalogued reports, with the densest cluster "
        f"near the {loc} around {year}. The JAH-N assessment below cross-references the claims "
        f"against buildable mechanisms in the spec catalog."
    )
    kw = list(dict.fromkeys(list(keywords) + aspect_kw + [subject.split()[0].lower()]))
    d = G.build_dossier(next_id, cat, subj_line, overview, kw, ROWS)
    return d


def main():
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    os.makedirs(CHUNKDIR, exist_ok=True)
    st = load_state()
    global ROWS
    ROWS = load_spec_rows()
    index = build_token_index(ROWS)
    G.find_specs = make_fast_find(ROWS, index)

    subjects = G.TOPICS
    print(f"  {len(subjects)} base subjects x {len(ASPECTS)} aspects", flush=True)

    chunk_name = None
    chunk, idx_rows = [], []
    made = 0
    for k in range(batch):
        n = st["counter"] + k
        d = dossier_for(n, st["next_id"] + k, subjects)
        if not chunk:
            chunk_name = f"biz-c{st['next_chunk']:06d}"
        chunk.append(d)
        idx_rows.append([d["id"], d["subject"], d["category"], chunk_name])
        if len(chunk) >= CHUNK_SIZE:
            with gzip.open(os.path.join(CHUNKDIR, chunk_name + ".json.gz"), "wt", encoding="utf-8") as fh:
                json.dump(chunk, fh, ensure_ascii=False)
            print(f"  wrote {chunk_name}: {len(chunk)} dossiers", flush=True)
            chunk = []
            st["next_chunk"] += 1
        made += 1
    if chunk:
        with gzip.open(os.path.join(CHUNKDIR, chunk_name + ".json.gz"), "wt", encoding="utf-8") as fh:
            json.dump(chunk, fh, ensure_ascii=False)
        print(f"  wrote {chunk_name}: {len(chunk)} dossiers", flush=True)
        st["next_chunk"] += 1

    # append to index (rewrite gz)
    existing = []
    if os.path.exists(IDX):
        with gzip.open(IDX, "rt", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln:
                    existing.append(ln)
    with gzip.open(IDX, "wt", encoding="utf-8", compresslevel=6) as fh:
        for ln in existing:
            fh.write(ln + "\n")
        for row in idx_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(SHARDS, "w", encoding="utf-8") as fh:
        json.dump({"shards": [{"base": "", "index": "data/bizarre/bizarre.idx.json.gz"}]}, fh)

    st["next_id"] += made
    st["counter"] += made
    save_state(st)
    print(f"DONE: +{made} dossiers, next_id={st['next_id']}, total drip={st['counter']}")

    # refresh static discoverability artifacts (count block, sitemap, api.json)
    try:
        import build_static_discoverability as bsd
        bsd.main()
    except Exception as e:
        print(f"  static discoverability refresh skipped: {e}", flush=True)


if __name__ == "__main__":
    main()
