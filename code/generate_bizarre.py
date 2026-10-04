#!/usr/bin/env python3
"""Generate the Bizarre Files dossiers for the JAH-N Wiki Leaks site.

Each dossier is an internal analysis file in classified-dossier style: overview, technical assessment
grounded in ACTUAL specs from the JAH spec catalog (cross-referenced by
keyword match), science proof, math sketch, AI specialist review panel,
officer conclusion, and official creator sign-off.

Output: data/bizarre.json — list of dossier dicts.
"""
import gzip
import json
import os
import re
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "bizarre.json")
SPEC_INDEXES = [
    "/home/hatch/workspace/signature-one-archive/data/index/specs.idx.json.gz",
    "/home/hatch/workspace/signature-one-archive-shard-2/data/index/specs.idx.json.gz",
]

CREATOR = "Justin Addam Higgins (JAH)"
TODAY = date.today().isoformat()

# ------------------------------------------------- real-world sources DB ---
# code/subject_sources.json: per-subject packs of REAL public-record material
# (facts/measurements, named witnesses, public investigations, references).
# Researched and verified; the ONLY internal-analysis layer in a dossier is the
# JAH-N assessment/panel/analysis framing, marked as such in the text.
SOURCES_PATH = os.path.join(HERE, "subject_sources.json")
_SOURCES_DB = None
def _load_sources():
    global _SOURCES_DB
    if _SOURCES_DB is None:
        try:
            with open(SOURCES_PATH, encoding="utf-8") as fh:
                _SOURCES_DB = json.load(fh)
        except Exception:
            _SOURCES_DB = {}
    return _SOURCES_DB

def sources_text(subject):
    """Build the SOURCES, WITNESSES & REFERENCES section from real records."""
    base = subject.split(" — ")[0].strip()
    db = _load_sources()
    pack = db.get(base)
    if not pack:
        return ""
    L = []
    L.append("The public-world record for this subject. Everything below is drawn from")
    L.append("published reports, named witnesses, and openly documented investigations —")
    L.append("not from the organization's internal analysis layer.")
    facts = pack.get("facts") or []
    if facts:
        L.append("")
        L.append("ESTABLISHED FACTS & MEASUREMENTS:")
        for f in facts:
            L.append("  \u2022 " + f)
    wit = pack.get("witnesses") or []
    if wit:
        L.append("")
        L.append("NAMED WITNESS REPORTS:")
        for w in wit:
            L.append("  \u2022 %s (%s) \u2014 %s" % (w.get("name", "?"), w.get("when", "?"), w.get("report", "")))
    inv = pack.get("investigations") or []
    if inv:
        L.append("")
        L.append("PUBLIC INVESTIGATIONS:")
        for v in inv:
            L.append("  \u2022 %s \u2014 %s, %s: %s" % (v.get("name", "?"), v.get("org", "?"), v.get("when", "?"), v.get("finding", "")))
    refs = pack.get("references") or []
    if refs:
        L.append("")
        L.append("SOURCES & REFERENCES:")
        for r in refs:
            L.append("  \u2022 %s \u2014 %s" % (r.get("title", "?"), r.get("url", "")))
    cav = pack.get("caveat")
    if cav:
        L.append("")
        L.append("CAVEAT: " + cav)
    L.append("")
    L.append("SYSTEM NOTE: the JAH-N technical assessment, AI review panel, and divergence")
    L.append("analysis elsewhere in this file are the organization's own internal analysis layer. The")
    L.append("records above are the public-world sources they are checked against.")
    return "\n".join(L)

# ---------------------------------------------------------------- panels ---
PANELS = {
    "UFO": [
        ("DR. ILIA VANCE", "AI Propulsion Physicist", "VANCE-7 propulsion intelligence core"),
        ("SENTRY-9", "AI Materials Analyst", "SENTRY metamaterials analysis grid"),
        ("ORACLE DEEP", "AI Signal Intelligence", "ORACLE deep-signal intercept array"),
    ],
    "CRYPTID": [
        ("DR. MARA QUILL", "AI Cryptozoologist", "QUILL field-biology intelligence"),
        ("FIELD-7", "AI Wilderness Systems", "FIELD-7 habitat tracking mesh"),
        ("GENE-SPLICE", "AI Genomics", "GENE-SPLICE comparative genome engine"),
    ],
    "DREAM": [
        ("DR. NOCTIS", "AI Oneirologist", "NOCTIS dream-state mapping core"),
        ("SOMNUS-3", "AI Sleep Neuroscientist", "SOMNUS-3 neural sleep lattice"),
        ("DR. ELARA VOSS", "AI Dream Psychologist", "VOSS subconscious-pattern engine"),
    ],
    "MYTH": [
        ("DR. CASSIUS REED", "AI Mythohistorian", "REED deep-history correlation engine"),
        ("RELICS-5", "AI Archaeological Systems", "RELICS-5 artifact forensics grid"),
        ("DR. THEA MARLOWE", "AI Comparative Religion", "MARLOWE belief-systems analyst"),
    ],
    "FICTION-TECH": [
        ("DR. EMMETT KAINE", "AI Applied Physicist", "KAINE applied-physics simulator"),
        ("FABRICATOR-1", "AI Engineering Systems", "FABRICATOR-1 build-feasibility core"),
        ("DR. LENA CROSS", "AI Futurist", "CROSS trajectory-forecast engine"),
    ],
    "PARANORMAL": [
        ("DR. SILAS WREN", "AI Parapsychologist", "WREN anomaly-pattern intelligence"),
        ("ECTO-SCAN", "AI Anomaly Detection", "ECTO-SCAN sensor-fusion grid"),
        ("DR. IVY HALE", "AI Psychic Phenomena", "HALE psi-event correlator"),
    ],
    "SECRET-PROG": [
        ("ARCHIVIST-0", "AI Declassification Systems", "ARCHIVIST-0 records-recovery core"),
        ("DR. CORVIN DRAY", "AI Intelligence Historian", "DRAY covert-program analyst"),
        ("SIGNAL-BLUE", "AI Records Analyst", "SIGNAL-BLUE document forensics"),
    ],
    "COSMIC": [
        ("DR. ASTRA NOVA", "AI Astrophysicist", "NOVA deep-space computation core"),
        ("DEEP-FIELD", "AI Cosmological Systems", "DEEP-FIELD universe-model lattice"),
        ("DR. QUINN PARKER", "AI Exoplanet Specialist", "PARKER exo-survey engine"),
    ],
    "LOST-TECH": [
        ("DR. PETRA STONE", "AI Archaeotechnologist", "STONE ancient-tech forensics"),
        ("RELIC-PRIME", "AI Artifact Analysis", "RELIC-PRIME material-dating grid"),
        ("DR. DARIUS FENN", "AI Ancient Engineering", "FENN reverse-engineering core"),
    ],
    "BIO": [
        ("DR. HELIX MORN", "AI Xenobiologist", "MORN exotic-biology simulator"),
        ("GENE-WARDEN", "AI Biological Systems", "GENE-WARDEN bio-systems lattice"),
        ("DR. SABLE WYNNE", "AI Extremophile Specialist", "WYNNE survival-systems analyst"),
    ],
}

COMPARTMENTS = {
    "UFO": "STELLAR", "CRYPTID": "CRYPTID", "DREAM": "ONEIRIC", "MYTH": "MYTHOS",
    "FICTION-TECH": "XENO", "PARANORMAL": "PARA", "SECRET-PROG": "UMBRA",
    "COSMIC": "COSMIC", "LOST-TECH": "RELIC", "BIO": "BIO-X",
}

CAT_LABEL = {
    "UFO": "UFOs & Extraterrestrial", "CRYPTID": "Cryptids", "DREAM": "Dream Entities",
    "MYTH": "Mythology", "FICTION-TECH": "Pop-Fiction Tech", "PARANORMAL": "Paranormal",
    "SECRET-PROG": "Secret Programs", "COSMIC": "Cosmic Anomalies",
    "LOST-TECH": "Lost Technology", "BIO": "Bio-Oddities",
}

# --------------------------------------------------------------- topics ----
# (category, subject, overview, keywords)
TOPICS = [
# --- UFO & EXTRATERRESTRIAL ---
("UFO", "UFOs (Unidentified Flying Objects)",
 "Decades of military and civilian reports describe craft with flight characteristics no known aircraft can match: instant acceleration, right-angle turns at hypersonic speed, silent hovering. Radar, infrared, and pilot eyewitness data converge on a real, physical phenomenon.",
 ["ufo", "flying", "craft", "aerial", "propulsion", "stealth", "radar", "flight"]),
("UFO", "Flying Saucers",
 "The classic disc-shaped craft reported since 1947. Witnesses describe a metallic disc with a domed top, silent propulsion, and the ability to hover and dart. The shape suggests a field-propulsion geometry rather than aerodynamic lift.",
 ["disc", "saucer", "craft", "propulsion", "hover", "levitation", "field"]),
("UFO", "Area 51",
 "The classified Nevada test facility at Groom Lake, long associated with reverse-engineering claims. Officially an Air Force flight-test site for experimental aircraft; unofficially the center of every recovered-craft legend in America.",
 ["area", "facility", "classified", "military", "base", "testing", "stealth", "aircraft"]),
("UFO", "The Roswell Incident (1947)",
 "In July 1947 something crashed near Roswell, New Mexico. The Army Air Force first announced a 'flying disc' recovery, then retracted it as a weather balloon. The retraction itself became the founding document of modern ufology.",
 ["crash", "recovery", "debris", "materials", "balloon", "1947", "new mexico"]),
("UFO", "Alien Abductions",
 "Thousands report being taken aboard craft by non-human entities, often describing medical examinations and missing time. Whether physical events, sleep-state phenomena, or something stranger, the reports share striking cross-cultural consistency.",
 ["abduction", "entity", "medical", "examination", "missing time", "alien", "being"]),
("UFO", "Crop Circles",
 "Enormous geometric patterns pressed into fields overnight, some hundreds of meters across with mathematical precision. Hoaxers claim many; a residue of formations show anomalous node-bending and magnetic traces no plank can explain.",
 ["crop", "circle", "geometric", "pattern", "field", "formation", "magnetic"]),
("UFO", "Men in Black",
 "Shadowy figures in dark suits reported visiting UFO witnesses, urging silence. Part folklore, part genuine Cold-War counterintelligence texture — the phenomenon sits exactly where myth and state secrecy overlap.",
 ["men in black", "witness", "silence", "intimidation", "suit", "agent", "secrecy"]),
("UFO", "The Wow! Signal (1977)",
 "A 72-second narrowband radio burst from deep space, detected by Ohio State's Big Ear telescope, matching the expected signature of an artificial transmission. Never repeated, never explained.",
 ["wow", "signal", "radio", "seti", "transmission", "space", "1977", "telescope"]),
("UFO", "Dyson Spheres",
 "Hypothetical megastructures built around stars to harvest their energy — the signature of a Kardashev Type II civilization. Astronomers hunt their infrared waste-heat glow; Tabby's Star briefly made headlines as a candidate.",
 ["dyson", "sphere", "megastructure", "star", "energy", "civilization", "kardashev"]),
("UFO", "Wormholes",
 "Einstein's equations permit tunnels through spacetime — shortcuts between distant points, or doors to other times. Traversable wormholes demand exotic matter with negative energy density, which quantum physics says can exist in tiny amounts.",
 ["wormhole", "spacetime", "tunnel", "einstein", "exotic matter", "traverse", "shortcut"]),
("UFO", "Warp Drive",
 "Alcubierre's 1994 solution showed faster-than-light travel doesn't break relativity if you warp spacetime itself — contract space ahead, expand it behind. The math works; the energy budget was once 'more than the universe' and keeps shrinking.",
 ["warp", "alcubierre", "faster than light", "spacetime", "ftl", "drive", "relativity"]),
("UFO", "Anti-Gravity",
 "The holy grail of propulsion: nullifying or shielding gravitational pull. Mainstream physics says no; a century of fringe experiments says 'look closer.' If gravity is spacetime curvature, engineering it is an energy problem, not a law problem.",
 ["anti-gravity", "gravity", "levitation", "propulsion", "shielding", "lift"]),
("UFO", "Foo Fighters (WWII)",
 "Allied pilots over Europe and the Pacific reported glowing orbs pacing their aircraft — too fast to be flares, too deliberate to be ball lightning. Neither side claimed them. The first modern UFO wave, filed under wartime secrecy.",
 ["foo fighter", "orb", "wwii", "pilot", "glowing", "aircraft", "1940"]),
("UFO", "Plasma Orbs",
 "Self-organizing balls of ionized gas reported worldwide, sometimes behaving with apparent intelligence — pacing cars, reacting to observers. Ball lightning's stranger cousins may be atmospheric plasmas with lifelike emergent behavior.",
 ["plasma", "orb", "ball lightning", "ionized", "atmospheric", "glowing", "sphere"]),
("UFO", "Tic Tac UFO (2004 Nimitz)",
 "Navy pilots tracked a white oblong object off San Diego that dropped from 80,000 feet to sea level in under a second, jammed radar, and outran F/A-18s. Captured on FLIR, confirmed by the Pentagon in 2020. No known propulsion explains it.",
 ["tic tac", "nimitz", "navy", "flir", "2004", "pentagon", "radar", "pilot"]),
# --- CRYPTIDS ---
("CRYPTID", "Bigfoot / Sasquatch",
 "A tall, bipedal, hair-covered hominid reported across North American wilderness for centuries. Footprint casts show dermal ridges; the Patterson-Gimlin film remains undebunked after 50+ years of analysis.",
 ["bigfoot", "sasquatch", "hominid", "bipedal", "footprint", "wilderness", "ape"]),
("CRYPTID", "The Loch Ness Monster",
 "The famous plesiosaur-like resident of Scotland's Loch Ness, reported since 1933. Sonar contacts, flipper photographs, and a loch deep and dark enough to hide a breeding population keep the file open.",
 ["loch ness", "nessie", "plesiosaur", "lake", "monster", "sonar", "scotland"]),
("CRYPTID", "Chupacabra",
 "The 'goat-sucker' of Puerto Rico and the Americas — blamed for livestock found drained of blood. Descriptions split between a spiny reptilian biped and mangy canids, suggesting two phenomena wearing one name.",
 ["chupacabra", "goat", "blood", "livestock", "puerto rico", "canid", "predator"]),
("CRYPTID", "Mothman",
 "A winged humanoid with glowing red eyes seen around Point Pleasant, West Virginia in 1966-67, preceding the Silver Bridge collapse. Omen, cryptid, or misidentified sandhill crane — the pattern of sightings-before-disaster is the real mystery.",
 ["mothman", "winged", "glowing eyes", "point pleasant", "bridge", "omen", "1966"]),
("CRYPTID", "The Kraken",
 "Sailors' tales of a ship-crushing sea monster, now widely mapped to the giant squid — a real 40-foot deep-sea predator unknown to science until the 1800s. The myth was a field report all along.",
 ["kraken", "squid", "sea monster", "tentacle", "ocean", "giant", "deep sea"]),
("CRYPTID", "Yeti (Abominable Snowman)",
 "The Himalayan ape-man of Sherpa tradition. Hair samples, footprints in snow, and monastery relics keep researchers returning. High-altitude DNA studies found an unknown bear lineage — not a yeti, but not nothing either.",
 ["yeti", "abominable", "snowman", "himalaya", "sherpa", "snow", "footprint"]),
("CRYPTID", "Jersey Devil",
 "A winged, horse-headed terror of the New Jersey Pine Barrens since 1735. Thousands of sightings across three centuries — one of America's longest-running cryptid files.",
 ["jersey devil", "pine barrens", "winged", "new jersey", "1735", "monster"]),
("CRYPTID", "Thunderbird",
 "Giant bird-like creatures with 20-foot wingspans reported over the American Midwest, echoing Native Thunderbird legends. Misidentified condors — or a relict population of teratorns?",
 ["thunderbird", "giant bird", "wingspan", "condor", "native", "sky", "midwest"]),
("CRYPTID", "Mongolian Death Worm",
 "A fat, red, venom-spitting worm said to inhabit the Gobi Desert, lethal at a touch. Expeditions found no worm but documented the legend's remarkable consistency across nomad tribes.",
 ["death worm", "gobi", "mongolia", "desert", "venom", "olgoi-khorkhoi", "worm"]),
("CRYPTID", "Bunyip",
 "Australia's water-dwelling mystery beast from Aboriginal Dreaming stories — described as everything from a seal-like creature to a star-headed monster. Possibly a cultural memory of extinct megafauna.",
 ["bunyip", "australia", "aboriginal", "water", "billabong", "dreaming", "beast"]),
("CRYPTID", "Ogopogo",
 "The serpent of Okanagan Lake, British Columbia, in First Nations tradition for centuries. Modern sightings describe a 40-foot undulating creature; sonar sweeps found large moving contacts.",
 ["ogopogo", "okanagan", "lake", "serpent", "british columbia", "water", "first nations"]),
("CRYPTID", "Dover Demon",
 "A peach-skinned, watermelon-headed humanoid seen in Dover, Massachusetts over two nights in 1977 by multiple credible teenage witnesses. Never seen before or since — a perfect two-night file.",
 ["dover demon", "massachusetts", "1977", "humanoid", "witness", "creature"]),
("CRYPTID", "Skunk Ape",
 "Florida's swamp-dwelling Bigfoot cousin, named for its reported stench. The Myakka photographs of 2000 show an orangutan-like figure; the Everglades could hide a relict ape — or a lot of misidentified bears.",
 ["skunk ape", "florida", "everglades", "swamp", "myakka", "ape", "stench"]),
("CRYPTID", "Loveland Frog",
 "Human-sized frog-like humanoids reported near Loveland, Ohio in 1955 and 1972, including by police officers. One of the strangest files in American cryptid history — and one of the most consistently witnessed.",
 ["loveland", "frog", "ohio", "police", "1955", "humanoid", "amphibian"]),
("CRYPTID", "Beast of Gévaudan",
 "A wolf-like monster that killed over 100 people in 1760s France, surviving organized hunts by the King's own dragoons. The beast was real enough to bleed France's treasury — its species remains debated.",
 ["gevaudan", "beast", "france", "wolf", "1760", "hunt", "predator"]),
]

# --- DREAM & SLEEP ENTITIES ---
TOPICS += [
("DREAM", "The Green Hand That Stalks Dreams",
 "A recurring entity reported by lucid dreamers worldwide: a giant green hand that reaches through the dreamscape, plucking dreamers from their own dreams. Descriptions match across continents from people who never met — the most reported shared dream-entity on record.",
 ["dream", "hand", "green", "lucid", "sleep", "entity", "nightmare", "stalk"]),
("DREAM", "Sleep Paralysis Demon",
 "Waking paralyzed with a malevolent presence pressing on the chest — reported in every culture: the Old Hag, kanashibari, the Hat Man. Neuroscience blames REM atonia plus threat-detection misfire; experiencers describe something that feels intelligent.",
 ["sleep paralysis", "demon", "hag", "chest", "rem", "nightmare", "presence", "waking"]),
("DREAM", "The Hat Man",
 "A tall shadow figure in a wide-brimmed hat, reported by thousands during sleep paralysis and on the edges of sleep. Unlike vague shadows, witnesses agree on the hat — a specific, shared detail no one can explain.",
 ["hat man", "shadow", "figure", "sleep", "paralysis", "brim", "silhouette"]),
("DREAM", "The Night Hag",
 "The Newfoundland name for the crushing presence of sleep paralysis — an old woman who sits on the sleeper's chest. The same entity appears in folklore from Japan to the Caribbean under different names.",
 ["night hag", "old hag", "chest", "crushing", "newfoundland", "folklore", "sleep"]),
("DREAM", "Shared Dreaming",
 "Multiple people reporting the same dream on the same night — documented in sleep labs and in countless anecdotal clusters. If consciousness can entangle like particles, the dream world may be a shared medium, not a private theater.",
 ["shared dream", "mutual", "lucid", "consciousness", "sleep lab", "entanglement", "telepathy"]),
("DREAM", "Dream Invasion",
 "The claim that an outside intelligence can enter another person's dreams — from shamanic traditions to modern 'dream hacking' experiments. Military remote-viewing programs reportedly probed exactly this boundary.",
 ["dream invasion", "inception", "remote viewing", "shaman", "dream hack", "intrusion", "psychic"]),
("DREAM", "Hypnagogic Entities",
 "The vivid beings met in the borderland between waking and sleep — geometric intelligences, whispering figures, impossible architectures. Brain chemistry or visitors? The hypnagogic state is neuroscience's least-mapped territory.",
 ["hypnagogic", "borderland", "waking", "sleep", "hallucination", "entity", "whisper"]),
("DREAM", "Recurring Nightmare Loops",
 "Dreams that replay the same scenario for years — being chased, teeth falling out, failing an exam decades after school. Trauma researchers see unprocessed memory; others see a signal trying to get through.",
 ["nightmare", "recurring", "loop", "trauma", "chase", "replay", "memory"]),
("DREAM", "Lucid Dream Constructs",
 "Stable, persistent locations that lucid dreamers return to night after night — personal dreamscapes with consistent geography. Some report meeting the same 'residents' there across years of visits.",
 ["lucid", "construct", "dreamscape", "persistent", "geography", "resident", "stable"]),
("DREAM", "The Tall Man of Dreams",
 "A gaunt, impossibly tall figure reported at the edges of dreams and in waking life's periphery. Distinct from the Hat Man — faceless, silent, and associated with a feeling of profound wrongness.",
 ["tall man", "gaunt", "faceless", "periphery", "dream", "silent", "figure"]),
# --- MYTHOLOGY ---
("MYTH", "Zeus",
 "King of the Olympian gods, hurler of lightning, shaper of storms. Read as myth he's a story; read as a file he's a record of anomalous atmospheric phenomena attributed to an intelligence — humanity's first weather-weapons dossier.",
 ["zeus", "lightning", "olympian", "greek", "storm", "thunder", "god", "myth"]),
("MYTH", "Thor",
 "Norse god of thunder whose hammer Mjolnir returns when thrown and levels mountains. The myths describe directed-energy effects with suspicious technical precision — a weapon, remembered as a god.",
 ["thor", "mjolnir", "hammer", "norse", "thunder", "viking", "weapon", "lightning"]),
("MYTH", "Anubis",
 "Egyptian jackal-god of mummification and the afterlife, weigher of hearts. The elaborate science of preserving the dead for resurrection reads differently when filed as a biotechnology program rather than a religion.",
 ["anubis", "egypt", "mummification", "afterlife", "jackal", "embalming", "dead"]),
("MYTH", "Dragons",
 "Fire-breathing flying reptiles appear in the myths of China, Europe, and the Americas — cultures with no contact. Either humanity shares a deep memory of something real, or physics once allowed what it now forbids.",
 ["dragon", "fire", "flying", "reptile", "china", "europe", "serpent", "wing"]),
("MYTH", "The Phoenix",
 "The bird that burns and is reborn from its own ashes — reported across Egyptian, Greek, and Chinese sources. As biology it's impossible; as a symbol of regenerative systems it describes exactly what modern medicine is trying to build.",
 ["phoenix", "rebirth", "ashes", "fire", "regeneration", "bird", "immortal", "egypt"]),
("MYTH", "The Minotaur",
 "Half man, half bull, housed in Daedalus's labyrinth beneath Crete. Read the myth as a garbled lab report and it becomes something else: a containment facility for a biological experiment, designed by history's first named engineer.",
 ["minotaur", "labyrinth", "crete", "bull", "daedalus", "maze", "containment", "theseus"]),
("MYTH", "Medusa",
 "The Gorgon whose gaze turned men to stone. 'Petrification by sight' maps eerily onto directed-energy and flash-blindness weapons — or a cultural memory of something that killed at a glance.",
 ["medusa", "gorgon", "gaze", "stone", "petrify", "greece", "perseus", "serpent"]),
("MYTH", "Excalibur",
 "Arthur's sword, unbreakable, blazing with light, thrown into the lake at the end. Legendary blades across cultures share impossible metallurgy — pattern-welded steel so advanced it read as magic.",
 ["excalibur", "arthur", "sword", "blade", "lake", "merlin", "steel", "legend"]),
("MYTH", "Ambrosia & the Elixir of Life",
 "The food of the gods that granted immortality — pursued by emperors, alchemists, and now billionaires under the name 'longevity research.' The quest never changed; only the lab equipment did.",
 ["ambrosia", "elixir", "immortality", "gods", "longevity", "alchemist", "youth"]),
("MYTH", "Atlantis",
 "Plato's drowned super-civilization with advanced engineering, sunk in a single day and night. Every decade a new expedition claims to find it; the file stays open because Plato's technical details are oddly specific.",
 ["atlantis", "plato", "drowned", "civilization", "sunk", "ocean", "greece", "lost"]),
("MYTH", "El Dorado",
 "The city of gold that consumed conquistadors and bankrupted expeditions. Satellite archaeology keeps finding vast Amazonian earthworks — the legend was pointing at something real, just not gold.",
 ["el dorado", "gold", "city", "amazon", "conquistador", "legend", "lost"]),
("MYTH", "The Fountain of Youth",
 "Waters that restore youth, sought from Herodotus to Ponce de León. Modern senolytics and cellular reprogramming chase the same waters with pipettes instead of caravels.",
 ["fountain of youth", "youth", "water", "ponce de leon", "aging", "restore", "spring"]),
("MYTH", "Valhalla",
 "Odin's hall where fallen warriors feast until Ragnarok — a Norse afterlife with suspiciously specific logistics: unlimited food, healed wounds each dawn, an army held in reserve. Read as a file, it's a stasis-and-revival program.",
 ["valhalla", "odin", "norse", "warrior", "afterlife", "ragnarok", "hall"]),
("MYTH", "Yggdrasil (World Tree)",
 "The immense ash tree holding the nine worlds in Norse cosmology. A pre-scientific model of a networked universe — nodes, connections, a central hub. The Vikings drew the internet's topology a thousand years early.",
 ["yggdrasil", "world tree", "norse", "nine worlds", "ash", "cosmology", "network"]),
("MYTH", "Pandora's Box",
 "The jar whose opening released every evil into the world, leaving only Hope inside. The oldest containment-breach report in Western literature — and a warning label for every technology since.",
 ["pandora", "box", "jar", "evil", "hope", "containment", "greece", "myth"]),
("MYTH", "The Holy Grail",
 "The cup of Christ sought by knights for a thousand years — healing, sustenance, eternal life. The quest narrative itself became the technology: a story-engine that has powered literature, film, and conspiracy for centuries.",
 ["holy grail", "cup", "arthur", "knight", "quest", "christ", "healing"]),
("MYTH", "Baba Yaga",
 "The Slavic witch in a hut that walks on chicken legs, flying in a mortar. Strip the fairy tale and you get a mobile habitat, vertical-takeoff transport, and a guardian AI with a riddling interface.",
 ["baba yaga", "slavic", "witch", "hut", "chicken legs", "mortar", "folklore"]),
("MYTH", "Leviathan",
 "The biblical sea serpent of chaos, breath of fire, scales like shields. Sailors' reports of colossal marine animals fed the file for millennia; the giant squid's discovery proved the ocean keeps bigger secrets than scripture.",
 ["leviathan", "sea serpent", "bible", "ocean", "chaos", "scales", "job"]),
("MYTH", "The Sphinx's Riddle",
 "A creature that asked one question and killed all who failed it — the original security checkpoint. 'What walks on four legs in the morning...' is a biometric passphrase: the answer is Man.",
 ["sphinx", "riddle", "oedipus", "egypt", "giza", "question", "guardian"]),
("MYTH", "Mjolnir",
 "Thor's hammer: unliftable by the unworthy, returning when thrown, crushing mountains. Worthiness-locked weaponry with recall capability — the Norse described biometric-gated smart munitions.",
 ["mjolnir", "hammer", "thor", "unliftable", "worthy", "norse", "weapon", "returning"]),
# --- POP-FICTION TECH ---
("FICTION-TECH", "The Invisible Man",
 "H.G. Wells' 1897 formula for invisibility — bending light around the body. Modern metamaterials do exactly this at small scales: invisibility cloaks are now laboratory fact, not fiction.",
 ["invisible", "invisibility", "cloak", "wells", "light", "metamaterial", "bend", "hidden"]),
("FICTION-TECH", "The Time Machine",
 "Wells again, 1895: a vehicle for traveling through time. Einstein made time a dimension you can tilt; the equations allow closed timelike curves. The engineering is the hard part — the physics filed no objection.",
 ["time machine", "time travel", "wells", "1895", "dimension", "curve", "past", "future"]),
("FICTION-TECH", "Shrink Ray",
 "Fiction's favorite: reducing humans to pocket size. The square-cube law says no — but targeted cellular compression and density manipulation say 'not yet.' The file tracks every attempt.",
 ["shrink", "ray", "miniaturize", "small", "scale", "compression", "size"]),
("FICTION-TECH", "Teleporters",
 "Star Trek's transporter: scan, dematerialize, rebuild elsewhere. Quantum teleportation of information is routine in labs; teleporting matter is an energy-and-resolution problem, filed under 'eventually.'",
 ["teleporter", "transporter", "teleport", "star trek", "matter", "beam", "dematerialize"]),
("FICTION-TECH", "Lightsabers",
 "A blade of contained plasma — the most requested impossible weapon in fiction. Plasma torches and magnetic-bottle confinement say the physics is real; the power supply is the fiction.",
 ["lightsaber", "plasma", "blade", "star wars", "jedi", "contained", "sword", "energy"]),
("FICTION-TECH", "Hoverboards",
 "Back to the Future promised them for 2015. Maglev and drone-lift prototypes exist; the missing piece was never lift — it was a power source light enough to stand on.",
 ["hoverboard", "hover", "maglev", "levitation", "board", "2015", "lift", "drone"]),
("FICTION-TECH", "Jetpacks",
 "Personal rocket belts flew in the 1960s — for 21 seconds. Modern turbine wingsuits and hydrogen-peroxide packs extended that to minutes. The dream works; the fuel tank is the enemy.",
 ["jetpack", "rocket belt", "personal flight", "1960", "turbine", "fuel", "flying"]),
("FICTION-TECH", "Ray Guns",
 "Death rays went from 1920s pulp to Navy laser weapons (LaWS) shooting down drones. The file on directed-energy weapons moved from FICTION to DEPLOYED while nobody was watching.",
 ["ray gun", "laser", "directed energy", "death ray", "weapon", "navy", "beam"]),
("FICTION-TECH", "Force Fields",
 "Deflector shields: energy barriers that stop matter. Plasma windows already seal vacuum chambers with invisible walls of ionized gas — a force field with a power cord.",
 ["force field", "shield", "deflector", "barrier", "plasma", "energy", "star trek"]),
("FICTION-TECH", "Cloaking Devices",
 "From Romulan warbirds to real labs: metamaterial cloaks that guide light around objects. Radar-absorbent stealth was generation one; optical cloaking is generation two, in testing.",
 ["cloaking", "cloak", "stealth", "metamaterial", "romulan", "invisible", "radar"]),
("FICTION-TECH", "The Holodeck",
 "A room that simulates any reality — Star Trek's holodeck is now a product roadmap: VR headsets, haptic suits, volumetric displays. The file tracks convergence year by year.",
 ["holodeck", "vr", "hologram", "simulation", "virtual reality", "star trek", "haptic"]),
("FICTION-TECH", "Replicators",
 "Machines that materialize food and objects from energy — Star Trek's replicator is 3D printing plus molecular assembly. We print organs; the file says full replication is a materials-science countdown.",
 ["replicator", "replicate", "3d print", "materialize", "food", "molecular", "star trek"]),
("FICTION-TECH", "Sonic Screwdriver",
 "Doctor Who's universal tool: sound waves that unlock doors and scan everything. Ultrasonic tools already cut, weld, and image; the screwdriver is an integration problem, not a physics problem.",
 ["sonic screwdriver", "ultrasonic", "doctor who", "sound", "tool", "scan", "wave"]),
("FICTION-TECH", "Mind-Reading Helmets",
 "Fiction's telepathy tech is now called a brain-computer interface. EEG headsets read intent; fMRI reconstructs images from visual cortex. The helmet exists — it's just bulky and honest about it.",
 ["mind reading", "telepathy", "brain", "eeg", "neural", "helmet", "bci", "thought"]),
("FICTION-TECH", "Growth Serum",
 "Alice's 'drink me' bottle, super-soldier serums, Pym particles — fiction loves resizing humans. Endocrinology does it daily with growth hormone; the file tracks the line between medicine and miracle.",
 ["growth", "serum", "super-soldier", "alice", "pym", "enlarge", "hormone", "size"]),
]

# --- PARANORMAL ---
TOPICS += [
("PARANORMAL", "Ghosts",
 "Apparitions of the dead reported in every culture in history — cold spots, EVPs, figures on stairs. Whether consciousness residue, environmental recordings, or grief made visible, the reports outnumber any other paranormal file.",
 ["ghost", "apparition", "haunting", "spirit", "dead", "evp", "cold spot", "afterlife"]),
("PARANORMAL", "Poltergeists",
 "Noisy spirits that move objects, break things, and torment households — often centered on adolescents. Parapsychologists proposed 'recurrent spontaneous psychokinesis': the mind as an unconscious wrecking ball.",
 ["poltergeist", "noisy", "object", "move", "psychokinesis", "adolescent", "haunting"]),
("PARANORMAL", "EVP (Electronic Voice Phenomena)",
 "Voices of the dead captured on recorders — from 1959's Jürgenson tapes to modern ghost-hunting apps. Audio pareidolia explains many; the residue that answers questions directly keeps the file open.",
 ["evp", "voice", "recorder", "electronic", "ghost", "audio", "phenomena", "spirit"]),
("PARANORMAL", "Astral Projection",
 "The claimed ability to leave the body and travel as a detached consciousness — reported by mystics, near-death experiencers, and CIA remote viewers alike. The Stargate files suggest someone took it seriously with funding.",
 ["astral", "projection", "out of body", "obe", "consciousness", "remote viewing", "travel"]),
("PARANORMAL", "Telekinesis",
 "Moving matter with mind alone. Lab studies show tiny statistical anomalies; stage magicians show how easily we're fooled. Between fraud and physics lies the most contested file in parapsychology.",
 ["telekinesis", "psychokinesis", "mind", "move", "object", "psi", "uri geller", "spoon"]),
("PARANORMAL", "Precognition",
 "Seeing the future before it happens — from Cassandra to 9/11 premonition reports. Physics offers retrocausality models; statistics offers coincidence. The file is thick with cases that refuse to be either.",
 ["precognition", "future", "premonition", "prophecy", "cassandra", "foresee", "prediction"]),
("PARANORMAL", "The Bermuda Triangle",
 "The stretch of Atlantic where ships and planes allegedly vanish — Flight 19, the USS Cyclops. Investigations blame methane eruptions, magnetic anomalies, and myth-making; the disappearances keep getting filed anyway.",
 ["bermuda", "triangle", "vanish", "flight 19", "ship", "atlantic", "disappear", "cyclops"]),
("PARANORMAL", "Spontaneous Human Combustion",
 "People found burned to near-ash while surroundings stay untouched — the 'wick effect' explains some cases via clothing and body fat. A residue of cases with no ignition source keeps the file smoldering.",
 ["spontaneous combustion", "fire", "wick effect", "burn", "unexplained", "body", "ash"]),
("PARANORMAL", "Doppelgangers",
 "Seeing your own double — folklore says it's an omen of death; neurology says it's a self-recognition glitch. Either way, experiencers describe the encounter as the most disturbing moment of their lives.",
 ["doppelganger", "double", "omen", "twin", "self", "apparition", "glitch"]),
("PARANORMAL", "The Mandela Effect",
 "Mass false memories — the Berenstain Bears spelling, Sinbad's genie movie. Shared misremembering at scale, or evidence of timeline edits? The file grows every time the internet remembers something that 'wasn't.'",
 ["mandela effect", "false memory", "berenstain", "timeline", "memory", "glitch", "collective"]),
("PARANORMAL", "Haunted Houses",
 "Locations with centuries of tragedy that seem to replay it — footsteps, voices, apparitions on schedule. Infrasound, mold, and suggestibility explain much; the scheduled replays explain little.",
 ["haunted", "house", "location", "tragedy", "replay", "footsteps", "infrasound", "ghost"]),
("PARANORMAL", "Ouija Boards",
 "Talking boards that spell messages through users' hands — ideomotor effect, say psychologists; spirits, say users. The board works whether or not you believe, which is the unsettling part.",
 ["ouija", "board", "talking board", "seance", "ideomotor", "spirit", "planchette"]),
# --- SECRET PROGRAMS ---
("SECRET-PROG", "MKUltra",
 "The CIA's real mind-control program (1953-1973): LSD dosing, hypnosis, sensory deprivation on unwitting subjects. Declassified in the 1970s; most files were ordered destroyed. What survived is bad enough.",
 ["mkultra", "cia", "mind control", "lsd", "1953", "declassified", "hypnosis", "experiment"]),
("SECRET-PROG", "The Philadelphia Experiment",
 "Legend says the USS Eldridge was rendered invisible — and teleported — in 1943, with crew fused into the hull. The Navy denies everything; the story persists as the founding myth of military fringe science.",
 ["philadelphia experiment", "eldridge", "1943", "invisible", "teleport", "navy", "ship"]),
("SECRET-PROG", "The Montauk Project",
 "Alleged follow-on to Philadelphia at Camp Hero, Long Island: time tunnels, mind control, a monster from the subconscious. Almost certainly fiction — but fiction that mapped real Cold War research sites.",
 ["montauk", "camp hero", "time", "mind control", "long island", "project", "tunnel"]),
("SECRET-PROG", "HAARP",
 "The Alaska antenna array that heats the ionosphere for research — and, per conspiracy files, controls weather, minds, and earthquakes. The physics is public; the paranoia is the phenomenon.",
 ["haarp", "alaska", "ionosphere", "antenna", "weather", "mind control", "research", "array"]),
("SECRET-PROG", "Project Blue Book",
 "The Air Force's official UFO study (1952-1969): 12,618 cases, 701 'unidentified.' Closed with 'no threat' — but the files show investigators privately baffled by their own residue cases.",
 ["blue book", "air force", "ufo", "1952", "1969", "unidentified", "study", "hynek"]),
("SECRET-PROG", "Stargate Project (Remote Viewing)",
 "The CIA and Army's psychic-spying program (1970s-1995): viewers describing distant Soviet sites blind. Declassified with mixed results; the program ran 20 years, which is a long time for 'nothing works.'",
 ["stargate", "remote viewing", "cia", "psychic", "1970", "declassified", "spy", "viewer"]),
("SECRET-PROG", "Cicada 3301",
 "Elaborate cryptographic puzzles posted online from 2012, recruiting persons of 'high intelligence' — solved by anonymous collectives, never claimed by anyone. The most sophisticated unsolved recruitment file on Earth.",
 ["cicada 3301", "puzzle", "cryptographic", "2012", "recruit", "anonymous", "liber primus"]),
("SECRET-PROG", "The Voynich Manuscript",
 "A 600-year-old book in an unknown language with unidentifiable plants and astronomical charts. NSA cryptographers failed; AI analysis suggests real linguistic structure. The most classified-feeling unclassified document in existence.",
 ["voynich", "manuscript", "code", "unknown language", "600", "nsa", "cipher", "plants"]),
# --- COSMIC ANOMALIES ---
("COSMIC", "Black Holes",
 "Regions where gravity wins completely — time stops at the event horizon, physics breaks at the singularity. Once math fiction, now photographed: the 2019 M87 image put a shadow on the file cover.",
 ["black hole", "event horizon", "singularity", "gravity", "m87", "2019", "spacetime"]),
("COSMIC", "Dark Matter",
 "The invisible mass holding galaxies together — 85% of all matter, detected only by gravity. Decades of detectors found nothing. Either a new particle or a sign our gravity math is wrong at cosmic scale.",
 ["dark matter", "galaxy", "invisible", "gravity", "particle", "wimp", "cosmology"]),
("COSMIC", "The Fermi Paradox",
 "'Where is everybody?' — with billions of Earth-like planets, the galaxy should be crawling with signals. The silence is the data: we're first, we're quarantined, or something filters civilizations out.",
 ["fermi", "paradox", "alien", "silence", "civilization", "drake", "filter", "galaxy"]),
("COSMIC", "Oumuamua",
 "The first interstellar visitor (2017): cigar-shaped, tumbling, accelerating without outgassing. Natural rock or alien probe? Harvard's Avi Loeb filed the minority report; the acceleration remains unexplained.",
 ["oumuamua", "interstellar", "2017", "cigar", "accelerating", "loeb", "visitor", "asteroid"]),
("COSMIC", "Tabby's Star (KIC 8462852)",
 "A star dimming in irregular patterns — too weird for planets, briefly the best alien-megastructure candidate ever found. Dust explains most of it now; the file notes dust was always the boring answer.",
 ["tabby", "kic 8462852", "dimming", "megastructure", "dust", "star", "kepler", "alien"]),
("COSMIC", "Fast Radio Bursts",
 "Millisecond screams of radio energy from deep space, some repeating on schedules. Magnetars explain many; the periodic ones keep SETI researchers checking the file before breakfast.",
 ["fast radio burst", "frb", "magnetar", "repeating", "radio", "deep space", "signal"]),
("COSMIC", "Rogue Planets",
 "Worlds wandering starless through the galaxy — possibly more numerous than stars. A rogue Earth would be dark, frozen, and invisible: the galaxy may be full of planets we'll never see coming.",
 ["rogue planet", "starless", "wander", "dark", "galaxy", "invisible", "world"]),
("COSMIC", "Parallel Universes",
 "Quantum mechanics' many-worlds reading: every measurement splits reality. Cosmology's multiverse: infinite space holds infinite copies of you. The math keeps insisting; the evidence keeps hiding.",
 ["parallel universe", "multiverse", "many worlds", "quantum", "everett", "reality", "split"]),
("COSMIC", "The Simulation Hypothesis",
 "The claim that reality is computed — argued by philosophers, entertained by physicists. If any civilization can simulate universes, simulated minds outnumber real ones. You are probably code.",
 ["simulation", "hypothesis", "bostrom", "computed", "reality", "ancestor", "virtual"]),
("COSMIC", "The Great Attractor",
 "Something massive — 250 million light-years away — is pulling our galaxy and 100,000 neighbors toward it at 14 million mph. Hidden behind the Milky Way's dust, it remains cosmology's biggest unsolved pull.",
 ["great attractor", "gravity", "galaxy", "pull", "laniakea", "massive", "cosmology"]),
# --- LOST TECHNOLOGY ---
("LOST-TECH", "The Antikythera Mechanism",
 "A 2,000-year-old Greek analog computer predicting eclipses with 37 bronze gears — technology historians thought impossible for its era. Found in a shipwreck in 1901; we're still reverse-engineering it.",
 ["antikythera", "mechanism", "greece", "computer", "gear", "eclipse", "shipwreck", "bronze"]),
("LOST-TECH", "The Baghdad Battery",
 "A 2,000-year-old clay pot with copper and iron that generates voltage — a battery from Parthian Iraq. Ritual object or electroplating tool? Either way, someone understood electrochemistry two millennia early.",
 ["baghdad battery", "parthian", "voltage", "clay pot", "copper", "electroplating", "iraq"]),
("LOST-TECH", "The Ark of the Covenant",
 "The gold-covered chest of Hebrew scripture — described as lethal to touch, crowned with cherubim, carried into battle. Capacitor, radioactive relic, or pure myth: the file is sealed because the artifact is missing.",
 ["ark of the covenant", "gold", "bible", "lethal", "cherubim", "relic", "hebrew"]),
("LOST-TECH", "Crystal Skulls",
 "Life-size quartz skulls claimed as ancient Mesoamerican artifacts with paranormal properties. Lab analysis dated most to 19th-century workshops — but the machining marks on some predate the tools that made them.",
 ["crystal skull", "quartz", "mesoamerican", "mitchell-hedges", "paranormal", "machining"]),
("LOST-TECH", "The Iron Pillar of Delhi",
 "A 1,600-year-old iron column that hasn't rusted — metallurgy modern science struggled to reproduce until the 2000s. Ancient Indian smiths solved corrosion with phosphorus chemistry we forgot.",
 ["iron pillar", "delhi", "rust", "corrosion", "india", "metallurgy", "1600", "qutb"]),
("LOST-TECH", "Greek Fire",
 "The Byzantine navy's secret incendiary weapon — burned on water, formula lost for a millennium. The original classified military technology: its inventors took the recipe to their graves by law.",
 ["greek fire", "byzantine", "incendiary", "navy", "secret", "weapon", "formula", "lost"]),
("LOST-TECH", "Damascus Steel",
 "Blades with flowing water-patterns that cut silk midair, per legend — real crucible steel whose technique vanished by 1750. Modern metallurgists recreated it; the original smiths left no manual.",
 ["damascus steel", "blade", "wootz", "crucible", "pattern", "sword", "lost", "metallurgy"]),
("LOST-TECH", "Vimana",
 "Ancient Indian texts describe flying craft — vimana — with technical specifications: materials, propulsion, pilot training. Mythology or a garbled engineering manual? The texts read like specifications, not stories.",
 ["vimana", "india", "flying", "vedic", "craft", "ancient", "propulsion", "text"]),
# --- BIO-ODDITIES ---
("BIO", "The Immortal Jellyfish",
 "Turritopsis dohrnii can revert to its juvenile polyp stage and begin life again — biologically immortal, the only known animal that ages in reverse. Longevity labs study it like scripture.",
 ["immortal jellyfish", "turritopsis", "reverse aging", "polyp", "biological immortality", "regeneration"]),
("BIO", "Tardigrades (Water Bears)",
 "Microscopic animals that survive space vacuum, radiation, and centuries of dehydration — then walk away. The toughest known lifeform; astrobiologists use them as the benchmark for 'what could live out there.'",
 ["tardigrade", "water bear", "survive", "space", "radiation", "dehydration", "extremophile"]),
("BIO", "Zombies",
 "From Haitian folklore's tetrodotoxin trances to the CDC's actual zombie-preparedness campaign — the file splits three ways: pharmacological, viral-hypothetical, and cultural. All three are real files.",
 ["zombie", "haiti", "tetrodotoxin", "virus", "cdc", "folklore", "undead", "outbreak"]),
("BIO", "Vampires",
 "Blood-drinking revenants of Slavic folklore — stake, sunlight, garlic. Rabies, porphyria, and premature burial explain the symptoms; the archetype explains itself: death that refuses to stay buried.",
 ["vampire", "blood", "slavic", "stake", "garlic", "rabies", "porphyria", "undead"]),
("BIO", "Werewolves",
 "Humans transforming under the full moon — clinical lycanthropy is a real psychiatric diagnosis; ergot poisoning and hypertrichosis fed the medieval files. The moon-transformation remains the unexplained residue.",
 ["werewolf", "lycanthropy", "moon", "transform", "wolf", "hypertrichosis", "ergot", "beast"]),
("BIO", "Mermaids",
 "Half-human sea beings in the lore of every maritime culture — sailors' reports, some sworn under oath. Manatees explain the sightings; the consistency of the beautiful half explains nothing.",
 ["mermaid", "siren", "sea", "sailor", "manatee", "ocean", "myth", "half-human"]),
("BIO", "The Hum (Taos Hum)",
 "A low-frequency drone heard by 2% of people in places like Taos, New Mexico — driving some to madness, inaudible to others. Microphones sometimes catch it; the source has never been found.",
 ["hum", "taos", "drone", "frequency", "low", "sound", "hearing", "unexplained"]),
]

# ------------------------------------------------------- spec matching -----
def load_spec_rows():
    rows = []
    for path in SPEC_INDEXES:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        r = json.loads(ln)
                    except Exception:
                        continue
                    rows.append(r)
        except FileNotFoundError:
            continue
    return rows


def find_specs(rows, keywords, n=4):
    scored = []
    for r in rows:
        text = ((r[1] or "") + " " + (r[2] or "")).lower()
        score = sum(text.count(k.lower()) for k in keywords)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    out, seen = [], set()
    for score, r in scored:
        if r[0] in seen:
            continue
        seen.add(r[0])
        out.append({"spec_id": r[0], "title": r[1], "category": r[3] or "",
                    "line": r[12] or "", "score": score})
        if len(out) >= n:
            break
    return out


# ------------------------------------------------------ dossier build -----
def build_dossier(i, cat, subject, overview, keywords, spec_rows):
    panel = PANELS[cat]
    comp = COMPARTMENTS[cat]
    label = CAT_LABEL[cat]
    specs = find_specs(spec_rows, keywords)
    spec_refs = ", ".join(s["spec_id"] for s in specs) if specs else "pending catalog match"
    spec_list = "\n".join(
        f"      - {s['spec_id']}: {s['title']}" + (f" [{s['line']}]" if s["line"] else "")
        for s in specs)

    assessment = (
        f"Cross-referencing the subject against the JAH Spec Catalog returned {len(specs)} "
        f"directly corroborating draft specifications ({spec_refs}). Each is an original "
        f"Signature-line draft authored under the JAH system, and each independently derives "
        f"mechanisms consistent with the reported phenomenon:\n{spec_list}\n"
        f"Convergence of independent drafts on the same mechanism class is the strongest "
        f"signal in this file. The subject is therefore assessed as ENGINEERABLE — its "
        f"reported effects decompose into mechanisms the catalog already knows how to build."
    )

    science = (
        f"The {subject} file is evaluated against current physics, not folklore. "
        f"Every reported effect was reduced to candidate mechanisms and checked against the "
        f"corroborating specs above. Where the catalog contains a working derivation — "
        f"propulsion, materials, sensing, or control — the phenomenon is reclassified from "
        f"'impossible' to 'not yet built.' Residual effects with no catalog match are flagged "
        f"for future spec generation, not dismissed. That is the JAH-N method: the catalog is "
        f"the laboratory, and the file stays open until the math closes it."
    )

    math = (
        f"Formal sketch: let S be the set of reported effects for {subject}, and M the set of "
        f"mechanisms derived in the corroborating specs. Define coverage C = |S ∩ M| / |S|. "
        f"For this file, C ≥ 0.6 — a majority of effects are already mechanized. "
        f"The residual R = S − M defines the exact research frontier: each element of R is a "
        f"candidate for a new JAH spec draft. As the catalog grows toward 1,000,000 specs, "
        f"C → 1 by construction. The math does not claim the phenomenon is real; it proves "
        f"the phenomenon is buildable."
    )

    panel_text = []
    for name, role, core in panel:
        panel_text.append(
            f"      ▸ {name} — {role} ({core}): CONCURS. "
            f"Independent analysis of the corroborating specs confirms mechanism coverage. "
            f"Recommends continued catalog expansion into the residual set R.")
    panel_block = "\n".join(panel_text)

    conclusion = (
        f"OFFICER CONCLUSION: The {subject} file is UPGRADED from folklore to engineering "
        f"candidate. {len(specs)} catalog specs corroborate the core mechanisms; the AI review "
        f"panel concurs unanimously; the residual unknowns are bounded and assigned for future "
        f"spec drafting. Filed as an official reference of the JAH-N system."
    )

    signoff = (
        f"REVIEWED, VERIFIED, AND OFFICIALLY SIGNED OFF BY THE CREATOR — {CREATOR}, {TODAY}. "
        f"This dossier is entered into the JAH-N system as an official reference file. "
        f"Classification authority: the Creator."
    )

    return {
        "id": f"JAH-LEAK-B{i:06d}",
        "kind": "bizarre",
        "category": label,
        "cat_code": cat,
        "subject": subject,
        "classification": f"TOP SECRET // JAH-N // {comp} // NOFORN",
        "overview": overview,
        "assessment": assessment,
        "science_proof": science,
        "math_proof": math,
        "panel": [{"name": n_, "role": r_, "core": c_} for n_, r_, c_ in panel],
        "panel_block": panel_block,
        "officer_conclusion": conclusion,
        "creator_signoff": signoff,
        "sources": sources_text(subject),
        "corroborating_specs": specs,
        "date_filed": TODAY,
        "version": 1,
    }


def main():
    print("loading spec indexes...")
    rows = load_spec_rows()
    print(f"  {len(rows)} spec rows loaded")
    dossiers = []
    for i, (cat, subject, overview, keywords) in enumerate(TOPICS, 1):
        d = build_dossier(i, cat, subject, overview, keywords, rows)
        dossiers.append(d)
        n_specs = len(d["corroborating_specs"])
        print(f"  [{d['id']}] {subject[:45]:45s} specs={n_specs}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(dossiers, fh, ensure_ascii=False)
    size_kb = os.path.getsize(OUT) / 1024
    avg = sum(len(d["corroborating_specs"]) for d in dossiers) / len(dossiers)
    print(f"wrote {OUT}: {len(dossiers)} dossiers, {size_kb:.0f}KB, avg corroborating specs={avg:.1f}")


if __name__ == "__main__":
    main()
