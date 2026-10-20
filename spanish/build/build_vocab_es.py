#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the vocabulary study sheets from ../vocabulario_elemental.md.

One section per lesson of Vocabulario. Nivel elemental A1-A2, every word in a
Spanish | English table. The markdown is the source and is written by hand; this
only typesets it, in the same face and the same vocabulary blue as the course
book, so the sheets sit with the rest of the set.

    python3 build_vocab_es.py [out.pdf]
"""
import re, os, sys, html
import markdown
from weasyprint import HTML

BUILD = os.path.dirname(os.path.abspath(__file__))
ES    = os.path.dirname(BUILD)
SRC   = os.path.join(ES, "vocabulario_elemental.md")
OUT   = os.path.join(ES, "Vocabulario_Elemental_A1-A2.pdf")
CSS   = os.path.join(BUILD, "style_vocab_es.css")

UNIT_RE  = re.compile(r'^## Unidad (\d+) · (.+?)\s*$', re.M)
TITLE_RE = re.compile(r'^# (.+?)\s*$', re.M)
# An article at the start of a Spanish cell is coloured by gender, the same blue
# and magenta the course book uses for its el/la pills. Only lower-case articles
# match, so a sentence that opens with "La Tierra…" is left alone.
ART_RE   = re.compile(r'(<tr>\s*<td>)(el|los|la|las) ')
GENDER   = {"el": "el", "los": "el", "la": "la", "las": "la"}


def md(text):
    out = markdown.markdown(text, extensions=["tables"])
    return ART_RE.sub(lambda m: f'{m[1]}<span class="g-{GENDER[m[2]]}">{m[2]}</span> ', out)


def parse(src):
    """(title, intro_markdown, [(n, title, subtitle_markdown, body_markdown)])"""
    title = TITLE_RE.search(src)[1]
    # the intro runs from the title to the hand-kept lesson list, which the PDF
    # replaces with a contents page that has page numbers
    intro = src[src.index("\n", src.index(title)):src.index("\n## ")].strip()
    marks = list(UNIT_RE.finditer(src))
    units = []
    for i, m in enumerate(marks):
        chunk = src[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(src)]
        chunk = chunk.strip().rstrip("-").strip()
        sub, _, body = chunk.partition("\n")
        units.append((int(m[1]), m[2], sub.strip(), body.strip()))
    return title, intro, sorted(units)


def build(out=OUT):
    with open(SRC, encoding="utf-8") as f:
        title, intro, units = parse(f.read())
    toc = "".join(
        f'<li><a href="#u{n}"><span class="n">Unidad {n}</span> {html.escape(t)}</a></li>'
        for n, t, _, _ in units)
    parts = [f'''
<section class="front">
  <p class="eyebrow">Español A1–A2</p>
  <h1>{html.escape(title.split(" — ")[0])}</h1>
  <p class="lede">Lo que hay que aprender, lección por lección · What to learn, lesson by lesson</p>
  <div class="intro">{md(intro)}</div>
  <p class="legend"><span class="g-el">el</span> masculine &nbsp;·&nbsp; <span class="g-la">la</span> feminine</p>
  <h2 class="toc-head">Contenido</h2>
  <ol class="toc">{toc}</ol>
</section>''']
    for n, t, sub, body in units:
        run = html.escape(f"Unidad {n} · {t}", quote=True)
        parts.append(f'''
<section class="unit" id="u{n}">
  <header class="unit-head" data-run="{run}">
    <span class="num">{n}</span>
    <div><h2>{html.escape(t)}</h2><div class="sub">{md(sub)}</div></div>
  </header>
  {md(body)}
</section>''')
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
           f'<title>{html.escape(title)}</title></head><body>{"".join(parts)}</body></html>')
    HTML(string=doc, base_url=BUILD).write_pdf(out, stylesheets=[CSS])
    print(f"{out}: {len(units)} units")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else OUT)
