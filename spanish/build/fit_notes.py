#!/usr/bin/env python3
"""Fit the "Notas" area at the end of each test to the space actually left on the page.

A test runs to about a page and a half, and the next unit always opens on a fresh
page, so the bottom of that second page cannot be filled by whatever comes next.
Left alone it prints as a third to two-thirds of a blank page, twenty times over.

There is no way to ask CSS for "as many ruled lines as will fit" — the answer
depends on where the page break lands, which is only known after the page is laid
out. So this does what a typesetter does with cross-references: lays the book out,
measures, writes the answer down, and lays it out again. Two or three passes and
every test page is full.

    python3 fit_notes.py            # fit, then leave notes_fill.json for the build

The result is committed, so an ordinary build reproduces the fitted layout without
re-running this.
"""
import json, os, subprocess, sys
import pymupdf

BUILD = os.path.dirname(os.path.abspath(__file__))
OUT   = os.environ.get("FIT_SCRATCH", "/tmp/fit_probe.pdf")
LINE  = 7 * 72 / 25.4          # .nline is 7mm tall
BAND_BOTTOM = 842 - 58         # last usable y before the footer
SLACK = 10                     # leave a hair of air rather than crowd the footer
MAXL  = 24                     # a full page of ruled lines; never more than that
MINL  = 4                      # below this it stops looking like somewhere to write


def measure(pdf):
    """{test-key: points of empty space under the score panel} for every test."""
    d = pymupdf.open(pdf)
    gaps, order = {}, []
    for p in d:
        t = p.get_text()
        if "MI RESULTADO" not in t:
            continue
        # the panel's notes lines may run onto the next page; measure the last one
        last = p.number
        while last + 1 < d.page_count and "NOTAS" in d[last + 1].get_text() \
                and "MI RESULTADO" not in d[last + 1].get_text():
            last += 1
        # the ruled lines carry no text, so measuring text blocks alone would
        # report the page as empty below the last word. Take the lowest ink of
        # any kind: text, rules, borders, tints.
        pg = d[last]
        low = max([b[3] for b in pg.get_text("blocks")
                   if b[4].strip() and 60 < b[1] < BAND_BOTTOM] +
                  [dr["rect"].y1 for dr in pg.get_drawings()
                   if 60 < dr["rect"].y1 < BAND_BOTTOM + 2])
        gaps[p.number + 1] = BAND_BOTTOM - low
        order.append(p.number + 1)
    d.close()
    return gaps, order


def test_keys():
    """The test keys in the order the tests appear in the book."""
    sys.path.insert(0, BUILD)
    import build_book_es as B
    keys = []
    for src in ("test_a1p1.md", "test_a1p2.md", "test_a2p1.md", "test_a2p2.md"):
        for (nivel, uno) in B.parse_tests(f"{B.SRC}/{src}"):
            keys.append((nivel, uno))
    # document order: A1 units 0-9, then A2 units 1-10
    keys.sort(key=lambda k: (k[0], int(k[1])))
    return [f"{n}-{u}" for n, u in keys]


def build(path):
    subprocess.run([sys.executable, f"{BUILD}/build_book_es.py", path],
                   check=True, capture_output=True)


def main():
    fill_path = f"{BUILD}/notes_fill.json"
    fill = json.load(open(fill_path)) if os.path.exists(fill_path) else {}
    keys = test_keys()

    for it in range(4):
        build(OUT)
        gaps, order = measure(OUT)
        if len(order) != len(keys):
            print(f"! found {len(order)} score panels but {len(keys)} tests — aborting")
            return 1
        changed = 0
        for key, pg in zip(keys, order):
            gap = gaps[pg]
            cur = int(fill.get(key, 7))
            # gap is what is still empty; convert it to whole lines and add them on
            new = max(MINL, min(MAXL, cur + int((gap - SLACK) // LINE)))
            if new != cur:
                fill[key] = new
                changed += 1
        worst = max(gaps.values())
        print(f"pass {it+1}: worst leftover {worst:.0f}pt, "
              f"mean {sum(gaps.values())/len(gaps):.0f}pt, {changed} tests adjusted")
        json.dump(fill, open(fill_path, "w"), indent=1, sort_keys=True)
        if not changed:
            break

    build(OUT)
    gaps, _ = measure(OUT)
    print("\nfinal leftover per test (pt):", sorted(round(v) for v in gaps.values()))
    print("lines per test:", json.dumps(fill, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
