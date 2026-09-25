#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the two places where a workbook chapter quotes its own reading passage.

Block D2 asks the learner to write three sentences from memory, so those three
sentences have to be *in* the passage, word for word — if a rewrite of the text
leaves them behind, the learner is being scored against a sentence that no longer
exists. Block D's answer key cites a proof line for each comprehension answer,
for the same reason. Both are coupled to the text and both break silently when a
passage is rewritten, which is what this catches.

The hard part is telling a proof line from the other quoted things on a key line.
Three of them are quoted and none belong to the passage:

    → Unit 8 → Gramática → "G · Prepositions of place"   a routing target
    not "Verdadero"                                       a wrong answer
    *(not "muchos tráficos" — tráfico is uncountable)*     a wrong answer, bracketed

So the route and the bracketed notes are cut off first, and any `not "…"` clause
with them. What is quoted in the remainder is a claim about the text, and has to
survive a word-for-word lookup.

    python3 check_verbatim.py [wb_part3.md ...]
"""
import re, sys, os, glob, unicodedata

BUILD = os.path.dirname(os.path.abspath(__file__))
# the five writers each picked their own way of marking a quotation
QUOTED = re.compile(r'«([^»\n]{8,})»|\*"([^"\n]{8,})"\*|"([^"\n]{8,})"')


def fold(s):
    """Compare on words alone: emphasis, accents, quotes and spacing are noise."""
    s = s.replace("*", "").replace("_", "")
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ ]+", " ", s)).strip()


def chapters(files):
    for f in files:
        txt = open(f, encoding="utf-8").read()
        for ch in re.split(r"^## Unidad ", txt, flags=re.M)[1:]:
            head = ch.split("\n")[0]
            m = re.match(r"(\d+)\s*[—–-]\s*(.+?)\s*\{(.+?)\}", head)
            if not m:
                continue
            meta = dict(re.findall(r"#(\w+)=([^\s}]+)", m.group(3)))
            key = f"{meta.get('nivel','A1')}-{int(m.group(1))}"
            am = re.search(r"^\*\*Answers\.?\*\*", ch, flags=re.M)
            body, ans = (ch[: am.start()], ch[am.end():]) if am else (ch, "")
            yield os.path.basename(f), key, body, ans


def passage(body):
    """The **Texto.** paragraph alone.

    It has to stop at the **Exercise** directive that follows it. Reading on to
    the next ### heading swallows the questions — and item a)'s worked model,
    which quotes the passage. A proof line would then be checked against a copy
    of itself and pass however wrong it was.
    """
    m = re.search(r"^\*\*Texto\.\*\*\s*(.*?)(?=^\*\*(?:Exercise|Espacio|Corte)|^###|\Z)",
                  body, re.M | re.S)
    return m.group(1) if m else ""


def d2_lines(body):
    m = re.search(r"^### D2\b.*?(?=^###|\Z)", body, re.M | re.S)
    if not m:
        return []
    out = []
    for line in m.group(0).split("\n"):
        lm = re.match(r"^([a-z])\)\s+(.+)$", line.strip())
        if lm:
            out.append((lm.group(1), re.sub(r"\*\(.*?\)\*\s*$", "", lm.group(2)).strip()))
    return out


def d_lines(body):
    """Block D's questions. Item a) is printed worked, so the question page
    carries a proof line of its own — the same coupling as the key's."""
    m = re.search(r"^### D · .*?(?=^###|\Z)", body, re.M | re.S)
    if not m:
        return []
    return [(lm.group(1), lm.group(2))
            for line in m.group(0).split("\n")
            if (lm := re.match(r"^([a-z])\)\s+(.+)$", line.strip()))]


def key_items(ans, num):
    """The lettered items of one Ex block, in the two shapes the writers used:
    'a) … · b) …' on one line, or one '- b) …' per line."""
    m = re.search(rf"^\*\*Ex\s*{num}\s*[—:-].*?(?=^\*\*Ex\s|\Z)", ans, re.M | re.S)
    if not m:
        return []
    s = re.sub(r"\n\s*-\s+", " · ", m.group(0))
    s = re.sub(r"\s+", " ", s).strip()
    marks, want = [], "a"
    for mm in re.finditer(r"(?:(?<=^)|(?<=[·\s]))([a-z])\)\s", s):
        if mm.group(1) == want:
            marks.append((mm.start(), mm.end(), want))
            want = chr(ord(want) + 1)
    return [(l, s[e:(marks[i + 1][0] if i + 1 < len(marks) else len(s))].strip())
            for i, (b, e, l) in enumerate(marks)]


def claims(chunk):
    """What a key item quotes *about the text*, once the routing target and the
    wrong-answer notes are removed."""
    chunk = re.split(r"\s*→\s*(?:A[12]\s+)?Unit\s", chunk)[0]
    chunk = re.sub(r"\*\(.*?\)\*", " ", chunk)          # bracketed notes
    chunk = re.split(r"(?:^|[·\s])no[t]?\s+[«\"]", chunk)[0]  # 'not "…"' clauses
    return [g for m in QUOTED.finditer(chunk) for g in m.groups() if g]


def main(files):
    nfail = nd2 = npf = 0
    for fname, ch, body, ans in chapters(files):
        txt = fold(passage(body))
        if not txt:
            print(f"[{ch}] no **Texto.** passage found")
            nfail += 1
            continue
        for letter, s in d2_lines(body):
            nd2 += 1
            if fold(s) not in txt:
                print(f"[{ch}] D2 {letter}) is not in the passage word for word:\n"
                      f"      {s}")
                nfail += 1
        for where, items in (("Ex 4", key_items(ans, 4)), ("question page", d_lines(body))):
            for letter, chunk in items:
                for q in claims(chunk):
                    npf += 1
                    if fold(q) not in txt:
                        print(f"[{ch}] {where}, {letter}) quotes words the passage "
                              f"does not have:\n      “{q}”")
                        nfail += 1
    print(f"\n{nd2} reconstruct sentences and {npf} quoted proof lines checked across "
          f"{len(files)} file(s) — {nfail} failure(s).")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or sorted(glob.glob(f"{BUILD}/wb_part*.md"))))
