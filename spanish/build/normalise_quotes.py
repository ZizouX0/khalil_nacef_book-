#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Put every proof-line quotation in the workbook into one notation.

Five writers wrote the twenty chapters in parallel and each picked a different way
to mark the line of the text that proves an answer:

    part1, part2   "En el aula hay tres ventanas."
    part3         *"Son las diez de la noche"*
    part4, part5  «Lo comparto con dos estudiantes italianos.»

Each was consistent inside its own part, so nobody reading one chapter sees a
problem; a learner working through all twenty meets three notations for the same
thing. Spanish uses the angle quotes and the A2 half already does, so that wins.

Scope is deliberately narrow — block D's questions and its Ex 4 answer key, which
are the only places that quote the passage. Inside those, these stay bare:
  · routing targets — → Unit 8 → Gramática → "G · Prepositions of place"
  · wrong answers   — not "Verdadero", *(not "muchos tráficos" — …)*
because they are not quoting the text, and the plain quotes usefully mark them out
as something other than a proof line.

    python3 normalise_quotes.py            # report what would change
    python3 normalise_quotes.py --write    # change it
"""
import re, sys, os, glob

BUILD = os.path.dirname(os.path.abspath(__file__))
LOOSE = re.compile(r'\*"([^"\n]{8,})"\*|"([^"\n]{8,})"')
# where a key item stops quoting the text and starts annotating the answer
STOP = (r"\s*→\s*(?:A[12]\s+)?Unit\s", r"\*\(", r"(?:^|[·\s])no[t]?\s+[«\"]")


def eligible(seg):
    """How much of one item may quote the passage. Mirrors the reasoning in
    check_verbatim.claims(), which is what proves the two still agree."""
    end = len(seg)
    for pat in STOP:
        m = re.search(pat, seg)
        if m:
            end = min(end, m.start())
    return end


def convert(text):
    """Rewrite quotations inside each lettered item, left of its notes.

    An item is a line of its own on the question page, but a key line holds either
    one item or all six separated by ' · '. So split into lines, then split each
    line on the separator, and judge each piece alone. Splitting only on lines
    converted item a) and left b) to f); splitting only on ' · ' skipped the
    question page, where there is no separator to split on.
    """
    n = 0
    out = []
    for seg in re.split(r"( · |\n)", text):
        # an item starts with its letter; 'also: …' is the same item continuing,
        # and what it holds is a second acceptable quotation of the passage
        if not re.match(r"^\s*(?:-\s+)?[a-z]\)\s", seg) and not re.match(
                r"^\*\*Ex\s*\d+\s*[—:-].*?\*\*\s*-?\s*[a-z]\)\s", seg) and not re.match(
                r"^\s*also:\s", seg):
            out.append(seg)
            continue
        cut = eligible(seg)
        body, k = LOOSE.subn(
            lambda q: "«" + (q.group(1) or q.group(2)) + "»", seg[:cut])
        n += k
        out.append(body + seg[cut:])
    return "".join(out), n


def regions(txt):
    """(start, end) of every block D question section and every Ex 4 key block."""
    spans = []
    for ch in re.finditer(r"^## Unidad .*?(?=^## Unidad |\Z)", txt, re.M | re.S):
        c, off = ch.group(0), ch.start()
        am = re.search(r"^\*\*Answers\.?\*\*", c, re.M)
        body_end = am.start() if am else len(c)
        d = re.search(r"^### D · .*?(?=^###|\Z)", c[:body_end], re.M | re.S)
        if d:
            spans.append((off + d.start(), off + d.end()))
        k = re.search(r"^\*\*Ex\s*4\s*[—:-].*?(?=^\*\*Ex\s|\Z)",
                      c[body_end:], re.M | re.S)
        if k:
            spans.append((off + body_end + k.start(), off + body_end + k.end()))
    return spans


def run(files, write):
    total = 0
    for f in files:
        src = open(f, encoding="utf-8").read()
        pieces, last, n = [], 0, 0
        for st, en in regions(src):
            new, k = convert(src[st:en])
            pieces.append(src[last:st])
            pieces.append(new)
            last = en
            n += k
        pieces.append(src[last:])
        dst = "".join(pieces)
        if n:
            total += n
            print(f"{os.path.basename(f)}: {n} quotation(s)"
                  f"{' rewritten' if write else ' would change'}")
            if write:
                open(f, "w", encoding="utf-8").write(dst)
    print(f"\n{total} quotation(s) total.")
    return 0


if __name__ == "__main__":
    write = "--write" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    sys.exit(run(args or sorted(glob.glob(f"{BUILD}/wb_part*.md")), write))
