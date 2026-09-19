#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical checks on the workbook chapters, the way check_tests.py guards the tests.

Five writers produce these chapters in parallel from WB_SPEC_ES.md, so the things
that go wrong are the things a person cannot see by reading one chapter: a block
that is two items short, an exercise with no answer, a spiral item that prints the
unit it came from on the question page, an answer key that says only "b".

    python3 check_workbook.py
"""
import re, sys, os, glob, unicodedata

BUILD = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BUILD)

# block letter -> items required by WB_SPEC_ES.md §2
WANT = {"A": 6, "B": 6, "C": 8, "D": 6, "D2": 3, "E": 16, "F": 5, "G": 4, "H1": 3}
# H2 is one open task and is counted by its **Espacio.** directive instead

findings = []


def flag(ch, kind, msg):
    findings.append((ch, kind, msg))


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s)).strip()


def chapters():
    for f in sorted(glob.glob(f"{BUILD}/wb_part*.md")):
        txt = open(f, encoding="utf-8").read()
        for ch in re.split(r"^## Unidad ", txt, flags=re.M)[1:]:
            head = ch.split("\n")[0]
            m = re.match(r"(\d+)\s*[—–-]\s*(.+?)\s*\{(.+?)\}", head)
            if not m:
                flag(head[:40], "parse", "chapter heading does not match the expected shape")
                continue
            meta = dict(re.findall(r"#(\w+)=([^\s}]+)", m.group(3)))
            key = f"{meta.get('nivel','A1')}-{int(m.group(1))}"
            am = re.search(r"^\*\*Answers\.?\*\*", ch, flags=re.M)
            body, ans = (ch[: am.start()], ch[am.end():]) if am else (ch, "")
            yield os.path.basename(f), key, body, ans


for fname, ch, body, ans in chapters():
    secs = re.split(r"^### ", body, flags=re.M)[1:]
    seen = {}
    for s in secs:
        name = s.split("\n")[0].strip()
        bm = re.match(r"([A-H][0-9]?)\b", name)
        if not bm:
            flag(ch, "section", f"heading does not start with a block letter: “{name}”")
            continue
        b = bm.group(1)
        seen[b] = s

    # 1. every block present, and none short
    for b, n in WANT.items():
        if b not in seen:
            flag(ch, "block", f"block {b} is missing")
            continue
        got = len(re.findall(r"^[a-z]\) ", seen[b], re.M))
        if got != n:
            flag(ch, "block", f"block {b} has {got} items, spec says {n}")
    if "H2" not in seen:
        flag(ch, "block", "block H2 (the writing task) is missing")
    elif not re.search(r"^\*\*Espacio\.\*\*\s*\d+", seen.get("H2", ""), re.M):
        flag(ch, "block", "block H2 has no **Espacio.** directive, so no room to write")

    # 2. the split point, exactly once, between D2 and E
    cuts = len(re.findall(r"^\*\*Corte\.\*\*", body, re.M))
    if cuts != 1:
        flag(ch, "corte", f"{cuts} split points, expected exactly 1")

    # 3. a reading passage, exactly once
    if len(re.findall(r"^\*\*Texto\.\*\*", body, re.M)) != 1:
        flag(ch, "texto", "expected exactly one **Texto.** reading passage")

    # 4. every exercise has an answer entry, and vice versa
    exq = {int(m.group(1)) for m in re.finditer(r"^\*\*Exercise\s+(\d+)", body, re.M)}
    exa = {int(m.group(1)) for m in re.finditer(r"^\*\*Ex\s*(\d+)\s*[—:-]", ans, re.M)}
    for n in sorted(exq - exa):
        flag(ch, "key", f"Exercise {n} has no answer entry")
    for n in sorted(exa - exq):
        flag(ch, "key", f"answer entry Ex {n} has no exercise")

    # 5. the spiral must not print its source unit once the scaffold comes off
    scaffold = ch in ("A1-0", "A1-1", "A1-2", "A1-3", "A1-4")
    if not scaffold and "E" in seen:
        tags = re.findall(r"\((?:U\d+|A[12]-\d+)\)", seen["E"])
        if tags:
            flag(ch, "spiral", f"block E prints the source unit on the question page: {tags[:4]}")

    # 6. a worked model in every block that has lettered items. H2 is one open
    #    task: its model belongs in the key, labelled "one possible answer", and
    #    printing a model essay on the question page would just be the answer.
    MODEL = ("*(model", "modelo", "one possible answer")
    for b in WANT:
        if b in seen and not any(k in seen[b] for k in MODEL):
            flag(ch, "model", f"block {b} has no worked model item")

    # 7. the key must teach, not just state — a bare one-word answer is the
    #    defect the spec's five-field rule exists to prevent
    # the writing task's entry is a model answer and the reconstruct block's is a
    #    scoring rubric; neither takes a rule note, so only count the rest
    open_ex = set()
    # H1 is personalisation — its "answer" is a check, not a rule
    for b in ("D2", "H1", "H2"):
        if b in seen:
            open_ex |= {int(m.group(1)) for m in re.finditer(r"^\*\*Exercise\s+(\d+)", seen[b], re.M)}
    bare = []
    for line in ans.split("\n"):
        m = re.match(r"^\*\*Ex\s*(\d+)\s*[—:-]", line)
        if not m or int(m.group(1)) in open_ex:
            continue
        if "*(" not in line:
            bare.append(int(m.group(1)))
    if bare:
        flag(ch, "key", f"answer line(s) with no explanation at all: Ex {bare}")

if not findings:
    print("All checks pass across every workbook chapter.")
    sys.exit(0)

by = {}
for ch, kind, msg in findings:
    by.setdefault(ch, []).append((kind, msg))
for ch in sorted(by):
    print(f"\n── {ch}")
    for kind, msg in by[ch]:
        print(f"   [{kind}] {msg}")
print(f"\n{len(findings)} finding(s) across {len(by)} chapter(s).")
sys.exit(1)
