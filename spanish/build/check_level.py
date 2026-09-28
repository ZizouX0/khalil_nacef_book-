#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which Spanish words in a scene has the course book not taught yet?

A scene that needs a tense or a word the reader has not met is a scene they cannot
play. This builds the set of word forms the course book has actually printed by the
end of a given unit and lists everything in the text that falls outside it.

    python3 check_level.py A1 7 somefile.md
    python3 check_level.py A2 3 --text "¿Me trae la carta, por favor?"

A1 unit N sees A1 units 0..N. A2 unit N sees all of A1 plus A2 units 1..N.

It is ADVISORY. It carries noise both ways, so audit every flag:
  · a proper noun is fine
  · an irregular form of a taught verb may be flagged — check the unit's own table
  · a word from a later unit is not fine, and is the thing this exists to catch

One deliberate asymmetry: only regular PRESENT-tense forms are generated from an
infinitive. Past forms are licensed only where the course book prints them
literally, so a past tense smuggled into an A1 scene gets flagged instead of waved
through.
"""
import re, sys, os, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = f"{ROOT}/sources_md" if os.path.isdir(f"{ROOT}/sources_md") else f"{ROOT}/../sources_md"
FILES = {("A1", 0): "a1p1.md", ("A1", 5): "a1p2.md",
         ("A2", 1): "a2p1.md", ("A2", 6): "a2p2.md"}
WORD = re.compile(r"[a-záéíóúüñ]+(?:-[a-záéíóúüñ]+)?", re.I)


def units_in_scope(level, n):
    """[(level, unit), …] every unit a reader of level/n has already worked through."""
    out = [("A1", u) for u in range(0, 10)] if level == "A2" else []
    if level == "A1":
        out = [("A1", u) for u in range(0, n + 1)]
    else:
        out += [("A2", u) for u in range(1, n + 1)]
    return out


def unit_text(level, n):
    fname = FILES[(level, 0 if level == "A1" and n < 5 else
                   5 if level == "A1" else 1 if n < 6 else 6)]
    txt = open(f"{SRC}/{fname}", encoding="utf-8").read()
    m = re.search(rf"^## Tema:[^\n]*#nivel={level} #unidad={n}\b.*?(?=^## Tema:|\Z)",
                  txt, re.M | re.S)
    return m.group(0) if m else ""


def inflect(w):
    """Forms the course's own rules license from a headword it prints.

    Only the regular present indicative, plus the plural and feminine of a noun or
    adjective. Nothing past — see the module docstring.
    """
    out = {w}
    if len(w) > 2 and w[-2:] in ("ar", "er", "ir"):
        stem, end = w[:-2], w[-2:]
        if end == "ar":
            out |= {stem + s for s in ("o", "as", "a", "amos", "áis", "an")}
        elif end == "er":
            out |= {stem + s for s in ("o", "es", "e", "emos", "éis", "en")}
        else:
            out |= {stem + s for s in ("o", "es", "e", "imos", "ís", "en")}
    if w.endswith("o"):
        out |= {w[:-1] + "a", w + "s", w[:-1] + "as"}
    elif w.endswith("a"):
        out |= {w + "s"}
    elif w.endswith("e"):
        out |= {w + "s"}
    elif w and w[-1] not in "aeiou":
        out |= {w + "es", w + "s"}
    return out


def attested(level, n):
    """Every form a reader who has finished level/n has seen in print."""
    forms = set()
    for lv, u in units_in_scope(level, n):
        t = unit_text(lv, u)
        if not t:
            continue
        for w in WORD.findall(t.lower()):
            forms.add(w)
        # a headword printed as an infinitive licenses its regular present forms
        for cell in re.findall(r"^\|\s*([^|]{2,40}?)\s*\|", t, re.M):
            for w in WORD.findall(cell.lower()):
                forms |= inflect(w)
    return forms


def check(level, n, text):
    ok = attested(level, n)
    unknown = {}
    for w in WORD.findall(text.lower()):
        if w not in ok:
            unknown[w] = unknown.get(w, 0) + 1
    return unknown


def scan_games(path):
    """Check a whole game_part file: for each unit, gate only its Spanish fields.

    The roles and the reflection questions are deliberately in English, so gating
    them would bury the real flags in noise.
    """
    txt = open(path, encoding="utf-8").read()
    rc = 0
    for chunk in re.split(r"^## Unidad ", txt, flags=re.M)[1:]:
        head = chunk.split("\n")[0]
        m = re.match(r"(\d+)\s*[—–-]\s*(.+?)\s*\{(.+?)\}", head)
        if not m:
            continue
        meta = dict(re.findall(r"#(\w+)=([^\s}]+)", m.group(3)))
        level, n = meta.get("nivel", "A1"), int(m.group(1))
        sp = []
        for f in ("Situación", "Hablar", "Modelo"):
            sp += re.findall(r"^\*\*" + f + r"\.\*\*\s*(.*?)(?=^\*\*[A-ZÁÉÍÓÚ]|^###|\Z)",
                             chunk, re.M | re.S)
        unknown = check(level, n, "\n".join(sp))
        status = "clean" if not unknown else f"{len(unknown)} to audit"
        print(f"{level} unit {n} — {m.group(2)}: {status}")
        for w, c in sorted(unknown.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"     {w}  ×{c}")
        rc |= 1 if unknown else 0
    return rc


def main(argv):
    if "--games" in argv:
        return scan_games(argv[argv.index("--games") + 1])
    if len(argv) < 3:
        print(__doc__)
        return 2
    level, n = argv[0].upper(), int(argv[1])
    if "--text" in argv:
        text = argv[argv.index("--text") + 1]
    else:
        text = open(argv[2], encoding="utf-8").read()
    unknown = check(level, n, text)
    print(f"{level} unit {n}: {len(attested(level, n))} forms taught by here; "
          f"{len(unknown)} form(s) in the text are not among them")
    for w, c in sorted(unknown.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"   {w}  ×{c}")
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
