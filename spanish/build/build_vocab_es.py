#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the vocabulary revision guide from ../vocabulario_elemental.md.

One chapter per lesson of Vocabulario. Nivel elemental A1-A2. The markdown is
the source and is written by hand; this only typesets it, in the same face and
palette as the course book, so the guide sits with the rest of the set.

Plain markdown (the Spanish | English tables) is rendered as it is. The
revision pages are written as fenced blocks, one renderer each — the syntax is
in VOCAB_SPEC_ES.md:

    ::: cards ⭐ Lo esencial — The 16 must-knows
    - ☀️ Hace sol. | It's sunny.
    :::

Any emoji in the source is drawn with its Twemoji icon from assets/icons/, so
the markdown reads the same on GitHub as the PDF does on paper.

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
ICONS = os.path.join(ES, "assets", "icons")
TWEMOJI = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@15.1.0/assets/svg"

UNIT_RE  = re.compile(r'^## Unidad (\d+) · (.+?)\s*$', re.M)
TITLE_RE = re.compile(r'^# (.+?)\s*$', re.M)
BLOCK_RE = re.compile(r'^:::[ \t]*(\w+)[ \t]*([^\n]*)\n(.*?)^:::[ \t]*$', re.M | re.S)
EMOJI_RE = re.compile('([\U0001F300-\U0001FAFF☀-➿⭐])️?')
# An article at the start of a Spanish cell is coloured by gender, the same blue
# and magenta the course book uses for its el/la pills. Only lower-case articles
# match, so a sentence that opens with "La Tierra…" is left alone.
ART_RE   = re.compile(r'(<tr>\s*<td>)(el|los|la|las) ')
GENDER   = {"el": "el", "los": "el", "la": "la", "las": "la"}
# "### 4. Nombres — Nouns": the Spanish half of a heading is the one to learn,
# the English half is set lighter beside it
H3_RE    = re.compile(r'<h3>(.+?) — (.+?)</h3>')


def md(text):
    out = markdown.markdown(text, extensions=["tables"])
    out = ART_RE.sub(lambda m: f'{m[1]}<span class="g-{GENDER[m[2]]}">{m[2]}</span> ', out)
    return H3_RE.sub(r'<h3>\1 <span class="en">\2</span></h3>', out)


def inline(s):
    out = markdown.markdown(s.strip())
    return out[3:-4] if out.startswith("<p>") and out.endswith("</p>") else out


def gender(s):
    return re.sub(r'^(el|los|la|las) ',
                  lambda m: f'<span class="g-{GENDER[m[1]]}">{m[1]}</span> ', s.strip())


def icon(s):
    """'☀️ Hace sol.' -> ('☀️', 'Hace sol.')"""
    m = EMOJI_RE.match(s.strip())
    return (m[0], s.strip()[m.end():].strip()) if m else ("", s.strip())


def items(body):
    """'- a | b | c' lines -> [[a, b, c], …]"""
    return [[f.strip() for f in line[2:].split(" | ")]
            for line in body.splitlines() if line.startswith("- ")]


def prose(body):
    """whatever in a block is not an item line, as markdown"""
    return md("\n".join(l for l in body.splitlines() if not l.startswith("- ")))


def heading(title):
    es, _, en = title.partition(" — ")
    return (f'<h3 class="blk-h"><span class="es">{inline(es)}</span>'
            + (f' <span class="en">{inline(en)}</span>' if en else "") + '</h3>')


# ---------- one renderer per block ----------

def r_cards(body):
    cells = []
    for es, en in items(body):
        ic, es = icon(es)
        cells.append(f'<div class="card"><span class="ic">{ic}</span>'
                     f'<b>{inline(gender(es))}</b><span class="en">{inline(en)}</span></div>')
    return f'<div class="cardgrid n{len(cells)}">{"".join(cells)}</div>'


def r_estaciones(body):
    cells = []
    for i, (name, en, months, line_es, line_en) in enumerate(items(body), 1):
        ic, name = icon(name)
        cells.append(f'''<div class="season s{i}">
  <div class="top"><span class="ic">{ic}</span><div><b>{inline(gender(name))}</b>
  <span class="en">{inline(en)}</span></div></div>
  <p class="months">{inline(months)}</p>
  <p class="line">{inline(line_es)}<span class="en">{inline(line_en)}</span></p></div>''')
    return f'<div class="seasons">{"".join(cells)}</div>'


def r_clave(body):
    cols = []
    for head, hint, examples in items(body):
        lis = []
        for ex in examples.split(" ; "):
            es, _, en = ex.partition(" = ")
            lis.append(f'<li><b>{inline(es)}</b><span class="en">{inline(en)}</span></li>')
        cols.append(f'<div class="col"><p class="col-h">{inline(head)}</p>'
                    f'<p class="hint">{inline(hint)}</p><ul>{"".join(lis)}</ul></div>')
    return f'<div class="cols n{len(cols)}">{"".join(cols)}</div>{prose(body)}'


def r_termometro(body):
    rows = items(body)
    cells = "".join(
        f'<div class="step"><span class="ic">{icon(es)[0]}</span><b>{inline(icon(es)[1])}</b>'
        f'<span class="en">{inline(en)}</span><span class="deg">{inline(deg)}</span></div>'
        for es, en, deg in rows)
    return (f'<div class="bar"><span>caliente · hot</span><span>frío · cold</span></div>'
            f'<div class="steps n{len(rows)}">{cells}</div>')


def r_dialogo(body):
    people, rows = [], []
    for es, en in items(body):
        who, _, line = es.partition(": ")
        if who not in people:
            people.append(who)
        rows.append(f'<tr class="p{people.index(who) + 1}"><td class="who">{html.escape(who)}</td>'
                    f'<td class="es">{inline(line)}</td><td class="en">{inline(en)}</td></tr>')
    return f'<table class="dlg">{"".join(rows)}</table>'


def r_quiz(body):
    q, _, a = body.partition("\n---\n")
    return (f'<div class="q">{md(q)}</div>'
            f'<div class="sol"><p class="sol-h">🙃 Soluciones</p>{md(a)}</div>')


def r_box(body):
    return md(body)


RENDER = {"cards": r_cards, "estaciones": r_estaciones, "clave": r_clave,
          "termometro": r_termometro, "dialogo": r_dialogo, "quiz": r_quiz,
          "aprender": r_box, "ojo": r_box, "caja": r_box, "yase": r_box,
          "parte": lambda body: ""}


def render(text):
    """markdown with ::: blocks in it -> html"""
    out, at = [], 0
    for m in BLOCK_RE.finditer(text):
        out.append(md(text[at:m.start()]))
        kind, title, body = m[1], m[2].strip(), m[3]
        if kind not in RENDER:
            sys.exit(f"unknown block ::: {kind}")
        out.append(f'<div class="blk {kind}">{heading(title) if title else ""}{RENDER[kind](body)}</div>')
        at = m.end()
    out.append(md(text[at:]))
    return "".join(out)


def icons(doc):
    """every emoji -> its Twemoji SVG; fails loudly if one has not been fetched"""
    missing = set()
    def img(m):
        name = f"{ord(m[1]):x}"
        if not os.path.exists(os.path.join(ICONS, name + ".svg")):
            missing.add(f"{m[0]}  {TWEMOJI}/{name}.svg")
        return f'<img class="emo" src="../assets/icons/{name}.svg" alt="">'
    doc = EMOJI_RE.sub(img, doc)
    if missing:
        sys.exit("icons not in assets/icons/ — fetch them:\n  " + "\n  ".join(sorted(missing)))
    return doc


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
  <p class="lede">Lo que hay que aprender, capítulo a capítulo · What to learn, chapter by chapter</p>
  <div class="intro">{md(intro)}</div>
  <p class="legend"><span class="g-el">el</span> masculine &nbsp;·&nbsp; <span class="g-la">la</span> feminine</p>
  <h2 class="toc-head">Contenido</h2>
  <ol class="toc">{toc}</ol>
  <p class="credit">Icons: Twemoji, CC-BY 4.0.</p>
</section>''']
    for n, t, sub, body in units:
        run = html.escape(f"Unidad {n} · {t}", quote=True)
        # the chapter's first five content icons go up in its title band; the
        # block headings' own icons (🎯 ⭐ 💡…) are the same in every chapter
        badges = []
        for m in EMOJI_RE.finditer(re.sub(r'^:::[^\n]*$', '', body, flags=re.M)):
            if m[0] not in badges:
                badges.append(m[0])
            if len(badges) == 5:
                break
        parts.append(f'''
<section class="unit" id="u{n}">
  <header class="unit-head" data-run="{run}">
    <span class="num">{n}</span>
    <div class="t"><p class="eyebrow">Unidad {n}</p><h2>{html.escape(t)}</h2><div class="sub">{md(sub)}</div></div>
    <div class="badges">{"".join(badges)}</div>
  </header>
  {render(body)}
</section>''')
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
           f'<title>{html.escape(title)}</title></head><body>{"".join(parts)}</body></html>')
    HTML(string=icons(doc), base_url=BUILD).write_pdf(out, stylesheets=[CSS])
    print(f"{out}: {len(units)} units")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else OUT)
