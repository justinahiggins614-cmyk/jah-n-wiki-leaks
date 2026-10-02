# JAH-N Wiki QA checkers (TIER 2-8)

Re-runnable data/page consistency checkers. Run from the repo root:

    python3 code/qa/check_counts.py      # data counts vs page display formula; state.json counter == idx rows == chunk rows
    python3 code/qa/check_dupe_ids.py   # duplicate IDs within/across sources (idx<->chunks overlap is by design, not flagged)
    python3 code/qa/check_missing_ids.py# idx ID continuity + every chunk file exists and contains its IDs (~20s)
    python3 code/qa/check_links.py      # live HTTP audit of every link the page can emit (nav, sisters, deep-link targets, data files, canonical network bar)

Exit 0 = pass, 1 = findings. Ground truth as of 2026-10-01: 120 base + 28,020
drip bizarre dossiers (28,140 total bizarre), 12,748 patent dossiers, zero dupes,
zero gaps (B0001–B28140 contiguous).
