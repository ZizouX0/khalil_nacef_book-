#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical checks on the conversation-game scenes, per GAME_SPEC_ES.md §7.

Four writers produce these in parallel, so the failures that matter are the ones
nobody sees by reading one unit: a unit with three transactions and no negotiation,
a role that only answers questions, a model dialogue where one player never speaks,
a scene with no ending condition.

    python3 check_games.py
"""
import re, sys, os, glob, json, unicodedata

BUILD = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BUILD)
FIELDS = ["Situación", "Papel A", "Papel B", "Termina", "Reto", "Hablar",
          "Modelo", "Después"]
SHAPES = {"T", "N", "S"}

findings = []


def flag(where, kind, msg):
    findings.append((where, kind, msg))


def scenes(path):
    txt = open(path, encoding="utf-8").read()
    for chunk in re.split(r"^## Unidad ", txt, flags=re.M)[1:]:
        head = chunk.split("\n")[0]
        m = re.match(r"(\d+)\s*[—–-]\s*(.+?)\s*\{(.+?)\}", head)
        if not m:
            flag(head[:40], "parse", "unit heading does not match the expected shape")
            continue
        meta = dict(re.findall(r"#(\w+)=([^\s}]+)", m.group(3)))
        key = f"{meta.get('nivel','A1')}-{int(m.group(1))}"
        out = []
        for s in re.split(r"^### ", chunk, flags=re.M)[1:]:
            sh = s.split("\n")[0].strip()
            sm = re.match(r"(\d+)\s*·\s*([TNS])\s*·\s*(.+)$", sh)
            if not sm:
                flag(key, "scene", f"scene heading is not '<n> · <T|N|S> · <título>': “{sh}”")
                continue
            out.append({"n": int(sm.group(1)), "shape": sm.group(2),
                        "title": sm.group(3).strip(), "body": s})
        yield os.path.basename(path), key, out


def field(body, name):
    m = re.search(rf"^\*\*{re.escape(name)}\.\*\*\s*(.*?)(?=^\*\*(?:{'|'.join(re.escape(f) for f in FIELDS)})\.\*\*|^###|\Z)",
                  body, re.M | re.S)
    return m.group(1).strip() if m else None


units = json.load(open(f"{ROOT}/build/units.json", encoding="utf-8"))
# The game covers A1. A2 units exist in the course and the workbook but have no
# scenes, so asking for them here would report nineteen phantom failures.
LEVELS = ("A1",)
want_units = {f"{lv}-{u['unidad']}" for lv in LEVELS for u in units[lv]}
seen_units, titles = set(), {}

for path in sorted(glob.glob(f"{BUILD}/game_part*.md")):
    for fname, key, sc in scenes(path):
        seen_units.add(key)
        lvl = key.split("-")[0]

        # 1. at least three scenes
        if len(sc) < 3:
            flag(key, "count", f"{len(sc)} scene(s), spec says at least 3")

        # 8. numbering runs 1,2,3… with no gaps
        got = [s["n"] for s in sc]
        if got != list(range(1, len(sc) + 1)):
            flag(key, "number", f"scene numbers are {got}, expected {list(range(1, len(sc)+1))}")

        # 2. the first three are one T, one N and one S
        first3 = {s["shape"] for s in sc[:3]}
        if len(sc) >= 3 and first3 != SHAPES:
            flag(key, "shape", f"first three scenes are {[s['shape'] for s in sc[:3]]}, "
                               f"spec wants one T, one N and one S")

        for s in sc:
            at = f"{key} scene {s['n']}"
            # 9. a title must not repeat inside a level
            tk = (lvl, s["title"].lower())
            if tk in titles:
                flag(at, "title", f"title “{s['title']}” is already used in {titles[tk]}")
            else:
                titles[tk] = at

            # 3. every field present, in order
            vals, pos = {}, []
            for f in FIELDS:
                v = field(s["body"], f)
                vals[f] = v
                if v is None:
                    flag(at, "field", f"**{f}.** is missing")
                else:
                    pos.append((s["body"].find(f"**{f}.**"), f))
            if len(pos) == len(FIELDS) and pos != sorted(pos):
                flag(at, "order", f"fields are out of order: {[f for _, f in sorted(pos)]}")

            # 4. neither role may be passive
            for f in ("Papel A", "Papel B"):
                v = (vals.get(f) or "").lower()
                if v and not re.search(r"\bwant|\bneed|\bmust\b", v):
                    flag(at, "role", f"**{f}.** never says what the player wants "
                                     f"— the passive-role test")

            # 5. Hablar 6–10 items
            if vals.get("Hablar"):
                nh = len([x for x in vals["Hablar"].split("·") if x.strip()])
                if not 6 <= nh <= 10:
                    flag(at, "hablar", f"{nh} phrase(s) in **Hablar.**, spec says 6–10")

            # 6. Modelo 8–14 turns and both players speak
            if vals.get("Modelo"):
                turns = re.findall(r"^\s*[—-]\s*([AB])\s*:", vals["Modelo"], re.M)
                if not 8 <= len(turns) <= 14:
                    flag(at, "modelo", f"{len(turns)} turn(s) in **Modelo.**, spec says 8–14")
                if len(set(turns)) < 2:
                    flag(at, "modelo", "only one player speaks in **Modelo.**")

            # 7. Después: exactly two questions
            if vals.get("Después"):
                nq = vals["Después"].count("?")
                if nq != 2:
                    flag(at, "despues", f"{nq} question(s) in **Después.**, spec says 2")

for missing in sorted(want_units - seen_units):
    flag(missing, "unit", "unit has no scenes at all")

if not findings:
    print(f"All checks pass — {len(seen_units)} units, "
          f"{len(titles)} scenes.")
    sys.exit(0)

by = {}
for where, kind, msg in findings:
    by.setdefault(where, []).append((kind, msg))
for where in sorted(by):
    print(f"\n── {where}")
    for kind, msg in by[where]:
        print(f"   [{kind}] {msg}")
print(f"\n{len(findings)} finding(s) across {len(by)} place(s).")
sys.exit(1)
