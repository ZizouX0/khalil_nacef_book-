#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the two-player conversation game from build/game_*.md.

Third in the set. It imports the course book's builder for the same reason the
workbook does: the markdown quirks are handled there once, and the three books
have to look like one family on a shelf.

The one structural thing this book needs that the others do not: a scene's model
dialogue must not be visible while you are playing it. So the models go to the back
as their own section, exactly where the workbook puts its answer key, and the scene
page carries only what both players may see plus the two role boxes.

    python3 build_game_es.py [out.pdf]
    ES_STYLE=style_print_game_es.css python3 build_game_es.py out.pdf
"""
import re, os, sys, html, datetime, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_book_es as B
from weasyprint import HTML

ROOT, BUILD, PHOTOS = B.ROOT, B.BUILD, B.PHOTOS
# ES_GAME_SRC overrides the source list, so the whole pipeline — cover, contents,
# scene cards, the models at the back — can be smoke-tested against one unit
# while the chapters themselves are still being written.
GAME_FILES = (os.environ["ES_GAME_SRC"].split(",") if os.environ.get("ES_GAME_SRC")
              else [f"game_part{i}.md" for i in range(1, 5)])

UNIT_RE = re.compile(r'^##\s+Unidad\s+(\d+)\s*[—–-]\s*(.+?)\s*\{(.+?)\}\s*$', re.M)
SCENE_RE = re.compile(r'^###\s+(\d+)\s*·\s*([TNS])\s*·\s*(.+?)\s*$', re.M)
FIELDS = ["Situación", "Papel A", "Papel B", "Termina", "Reto", "Hablar",
          "Modelo", "Después"]
SHAPE = {"T": ("Transacción", "t"), "N": ("Negociación", "n"), "S": ("Social", "s")}


def field(body, name):
    m = re.search(r'^\*\*' + re.escape(name) + r'\.\*\*\s*(.*?)'
                  r'(?=^\*\*(?:' + '|'.join(re.escape(f) for f in FIELDS) + r')\.\*\*|^###|\Z)',
                  body, re.M | re.S)
    return m.group(1).strip() if m else ""


def parse_games(path):
    """[(nivel, unidad, title, [scene])] in file order; scene is a dict of fields."""
    if not os.path.exists(path):
        return []
    txt = open(path, encoding="utf-8").read()
    out = []
    for chunk in re.split(r'^##\s+Unidad\s+', txt, flags=re.M)[1:]:
        head = chunk.split("\n")[0]
        m = re.match(r'(\d+)\s*[—–-]\s*(.+?)\s*\{(.+?)\}', head)
        if not m:
            continue
        meta = dict(re.findall(r'#(\w+)=([^\s}]+)', m.group(3)))
        scenes = []
        for s in re.split(r'^###\s+', chunk, flags=re.M)[1:]:
            sm = re.match(r'(\d+)\s*·\s*([TNS])\s*·\s*(.+?)\s*$', s.split("\n")[0])
            if not sm:
                continue
            scenes.append({"n": int(sm.group(1)), "shape": sm.group(2),
                           "title": sm.group(3).strip(),
                           **{f: field(s, f) for f in FIELDS}})
        out.append((meta.get("nivel", "A1"), int(m.group(1)), m.group(2).strip(), scenes))
    return out


def render_scene(nivel, uno, sc):
    """One scene. Everything on this page is visible to both players except the two
    role boxes, which sit either side of a fold line."""
    name, cls = SHAPE[sc["shape"]]
    sid = B.hid(f"scene-{nivel}-{uno}-{sc['n']}")
    o = [f'<div class="scene" id="{sid}">']
    o.append(f'<h3 class="sh"><span class="sn">{uno}.{sc["n"]}</span>'
             f'<span class="tag {cls}">{name}</span>'
             f'{B.md_inline(sc["title"])}</h3>')
    if sc["Situación"]:
        o.append(f'<p class="situ">{B.md_inline(sc["Situación"])}</p>')
    o.append('<div class="roles">'
             f'<div class="role ra"><div class="rh">Papel A</div>'
             f'<div class="rtext">{B.md_inline(sc["Papel A"])}</div></div>'
             '<div class="fold f1"></div><div class="fold f2"></div>'
             f'<div class="role rb"><div class="rh">Papel B</div>'
             f'<div class="rtext">{B.md_inline(sc["Papel B"])}</div></div>'
             '</div>')
    if sc["Termina"]:
        o.append(f'<div class="ends"><span class="h">Termina cuando</span>'
                 f'{B.md_inline(sc["Termina"])}</div>')
    if sc["Reto"]:
        o.append(f'<div class="reto"><span class="h">Reto extra</span>'
                 f'{B.md_inline(sc["Reto"])}</div>')
    if sc["Hablar"]:
        items = [x.strip() for x in sc["Hablar"].split("·") if x.strip()]
        o.append('<div class="hablar"><span class="h">Para hablar</span><ul>'
                 + "".join(f'<li>{B.md_inline(i)}</li>' for i in items) + '</ul></div>')
    if sc["Después"]:
        o.append(f'<div class="desp"><span class="h">Después</span>'
                 f'{B.md_inline(sc["Después"])}</div>')
    o.append('</div>')
    return "".join(o)


def render_modelo(sc):
    """A model dialogue, as turns. A and B get different indents so you can see at a
    glance who is carrying the scene — usually a surprise, and usually useful."""
    o = [f'<p class="mk"><b>{sc["n"]}</b> · {B.md_inline(sc["title"])}</p>']
    rows = []
    for line in sc["Modelo"].split("\n"):
        lm = re.match(r'^\s*[—-]\s*([AB])\s*:\s*(.+)$', line.strip())
        if lm:
            who = "ma" if lm.group(1) == "A" else "mb"
            rows.append(f'<div class="turn {who}"><span class="w">{lm.group(1)}</span>'
                        f'{B.md_inline(lm.group(2))}</div>')
    o.append('<div class="modelo">' + "".join(rows) + '</div>')
    return "".join(o)


def build():
    B.TOC.clear(); B._IDS.clear()
    units = []
    for f in GAME_FILES:
        units += parse_games(f"{BUILD}/{f}")
    if not units:
        print("no game_part*.md source files found in build/ — nothing to build")
        return 1
    # course order: all of A1, then all of A2
    units.sort(key=lambda u: (u[0], u[1]))

    parts, models = [], []
    parts.append(B.h(1, "How to play"))
    intro = B.md_file("game_intro_es.md")
    if intro:
        parts.append(B.md(re.sub(r'^#\s+.*$', '', intro, count=1, flags=re.M)))

    n_sc = 0
    for nivel, uno, title, scenes in units:
        cid = B.hid(f"game-{nivel}-{uno}")
        ctitle = f"{nivel} Unidad {uno} — {title}"
        B.TOC.append((1, cid, ctitle))
        parts.append(f'<h1 id="{cid}">{html.escape(ctitle)}</h1><div class="gchapter">')
        for sc in scenes:
            parts.append(render_scene(nivel, uno, sc))
            n_sc += 1
        parts.append('<p class="modref"><small>The model conversations are at the back, '
                     f'under <b>{nivel} Unidad {uno}</b>. Play the scene first — a model '
                     f'read beforehand becomes a script.</small></p>')
        parts.append('</div>')
        if any(s["Modelo"] for s in scenes):
            models.append((f"{nivel} Unidad {uno} — {title}", scenes))

    # -------- the models, at the back --------
    parts.append(B.h(1, "Model conversations"))
    parts.append('<p class="lead">One way each scene could go — not the right answer. '
                 'Read the model <b>after</b> you have played, and look for what it says '
                 'that you wanted to say and could not. That gap is the next thing to learn.</p>')
    for title, scenes in models:
        mid = B.hid(f"mod-{title}")
        B.TOC.append((3, mid, title))
        parts.append(f'<h2 class="mhead" id="{mid}">{html.escape(title)}</h2>')
        for sc in scenes:
            if sc["Modelo"]:
                parts.append(render_modelo(sc))

    toc = ['<h1 class="toc-title">Contents</h1><ul class="toc">']
    for lvl, i, t in B.TOC:
        if lvl <= 2:
            toc.append(f'<li class="lvl{lvl}"><a href="#{i}">{html.escape(t)}</a></li>')
    toc.append('</ul>')

    cov = f"{PHOTOS}/_cover.jpg"
    covstyle = (f"background-image:linear-gradient(rgba(96,40,20,.40),rgba(60,22,10,.86)),"
                f"url('file://{cov}')" if os.path.exists(cov) else "")
    cover = (f'<div class="cover gcover" style="{covstyle}">'
             f'<div class="kick">Two players · A1 → A2</div>'
             f'<h1>Spanish for Beginners<br>The Talking Game</h1>'
             f'<div class="rule"></div>'
             f'<div class="sub">{n_sc} scenes for two learners and no teacher — one for every unit '
             f'of the course, where each of you wants something and the other is in the way</div>'
             f'<div class="meta"><div class="author">Aziz Dardouri</div>'
             f'<div class="badge">Juego · {datetime.date.today().strftime("%d/%m/%Y")}</div></div></div>')

    sheet = os.environ.get("ES_STYLE", "style_game_es.css")
    doc = (f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
           f'<title>Español A1–A2 · Juego de Conversación — Aziz Dardouri</title>'
           f'<meta name="author" content="Aziz Dardouri">'
           f'<meta name="description" content="A two-player speaking game for the Spanish A1-A2 '
           f'course: one scene per unit where each player has a goal and the other is in the way.">'
           f'<link rel="stylesheet" href="file://{BUILD}/{sheet}"></head><body>'
           f'{cover}{"".join(toc)}{"".join(parts)}</body></html>')
    open(f"{BUILD}/_game.html", "w", encoding="utf-8").write(doc)

    out = sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/Espanol_A1-A2_Juego_Conversacion.pdf"
    d = HTML(string=doc, base_url=BUILD)
    try:
        d.write_pdf(out, pdf_variant="pdf/ua-1")
    except Exception as e:
        print(f"  (pdf/ua-1 unavailable: {e}; writing a plain PDF)")
        d.write_pdf(out)
    print(f"PDF -> {out} ({os.path.getsize(out)//1024} KB) | units={len(units)} "
          f"scenes={n_sc} model sections={len(models)}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
