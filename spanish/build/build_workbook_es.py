#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the companion exercise book from build/wb_*.md.

It deliberately imports the course book's builder rather than copying it: the
same markdown quirks are already handled there, the same renderer already puts a
ruled line under every item, and the two books have to look like one pair on a
shelf. What differs is the shape of a chapter — the course book teaches then
practises, this one only practises — and the section palette.

    python3 build_workbook_es.py [out.pdf]
    ES_STYLE=style_print_wb_es.css python3 build_workbook_es.py out.pdf
"""
import re, os, sys, html, datetime, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_book_es as B
from weasyprint import HTML

ROOT, BUILD, PHOTOS = B.ROOT, B.BUILD, B.PHOTOS
# one file per writer, concatenated in course order
WB_FILES = [f"wb_part{i}.md" for i in range(1, 6)]

# Which course colour each workbook section borrows, so a learner who has used
# the course book already knows what a heading's colour means before reading it.
SEC_CLASS = {
    # the nine block names from WB_SPEC_ES.md, each borrowing the course book's
    # colour for the kind of work it is
    "reconocimiento": "voc",  "vocabulario": "voc", "vocabulary": "voc",
    "formas":         "gram", "gramatica":   "gram", "grammar":   "gram",
    "huecos":         "gram", "cloze":       "gram",
    "un solo error":  "gram", "error":       "gram",
    "lectura":        "conv", "reading":     "conv",
    "reconstruye":    "conv",
    "escribe":        "conv", "escritura":   "conv", "writing":   "conv",
    "tu":             "conv",
    "vuelve":         "prac", "repaso":      "prac", "traduce":   "prac",
    "mixed":          "prac", "todo":        "prac",
}
UNIT_RE = re.compile(r'^##\s+Unidad\s+(\d+)\s*[—–-]\s*(.+?)\s*\{(.+?)\}\s*$', re.M)
SEC_RE  = re.compile(r'^###\s+(.+?)\s*$', re.M)
TEXT_RE = re.compile(r'^\*\*(?:Texto|Text|Lectura)\.\*\*\s*(.+?)(?=\n\s*\n|\*\*Exercise|\Z)', re.S | re.M)
# "**Espacio.** 12" asks for twelve ruled lines: a 70-word writing task needs a
# page to write on, not the single rule an ordinary item gets.
SPACE_RE = re.compile(r'^\*\*(?:Espacio|Space)\.\*\*\s*(\d+)\s*$', re.M)
# "**Corte.**" prints the halfway rule: a chapter is designed to be splittable
# into two sittings of under twenty minutes, which is the length people finish.
CUT_RE = re.compile(r'^\*\*(?:Corte|Split)\.\*\*\s*$', re.M)


def sec_class(name):
    key = B._fold(name.lower())
    key = re.sub(r'[^a-zñ ]', '', key).strip()
    for k, v in SEC_CLASS.items():
        if k in key:
            return v
    return "prac"


def parse_workbook(path):
    """[(nivel, unidad, title, [(section_name, body)], answers)] in file order."""
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8").read()
    out, hits = [], list(UNIT_RE.finditer(text))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        body = text[m.end():end]
        meta = B.parse_meta(m.group(3))
        nivel = meta.get("nivel", "A1")
        uno = str(int(meta.get("unidad", m.group(1))))
        am = re.search(r'^\*\*Answers\.?\*\*', body, re.M)
        practice, answers = (body[:am.start()], body[am.end():]) if am else (body, "")
        secs, shits = [], list(SEC_RE.finditer(practice))
        for j, s in enumerate(shits):
            se = shits[j + 1].start() if j + 1 < len(shits) else len(practice)
            secs.append((s.group(1).strip(), practice[s.end():se].strip()))
        if not secs and practice.strip():
            secs = [("Repaso", practice.strip())]
        out.append((nivel, uno, m.group(2).strip(), secs, answers.strip()))
    return out


def render_section(name, body):
    """A section heading in the course book's colours, then its exercises.
    A reading passage is lifted out first: it is the thing the exercises ask
    about, so it has to read as a text and not as another instruction."""
    cls = sec_class(name)
    o = [f'<div class="scope {cls}">',
         f'<h3 class="sec sec-{cls}" id="{B.hid(name)}">'
         f'<span class="tag">{html.escape(name)}</span></h3>']
    tm = TEXT_RE.search(body)
    if tm:
        o.append('<div class="wbtext"><span class="h">Lee el texto</span>'
                 + B.md(tm.group(1).strip()) + '</div>')
        body = body[:tm.start()] + body[tm.end():]
    space = 0
    sm = SPACE_RE.search(body)
    if sm:
        space = max(2, min(int(sm.group(1)), 26))
        body = body[:sm.start()] + body[sm.end():]
    inner = B.render_practice(body)
    if space:
        inner += '<div class="wbwrite">' + '<div class="wline"></div>' * space + '</div>'
    o.append('<div class="practice">' + inner + '</div>')
    o.append('</div>')
    return "".join(o)



BLOCK_PTS = [("A", "Reconocimiento", 6), ("B", "Formas", 6), ("C", "Texto con huecos", 8),
             ("D", "Lectura", 6), ("D2", "Lee y reconstruye", 6), ("E", "Vuelve", 16),
             ("F", "Un solo error", 5), ("G", "Traduce", 8), ("H1", "Tú", 3), ("H2", "Escribe", 6)]


def chapter_grid():
    """The end-of-chapter marking grid. There is no pass mark on purpose: this
    book interleaves deliberately, interleaving is supposed to produce errors,
    and a gate would punish the learner for the mechanism working. 60% a block is
    an action threshold — below it, do the corrective — and the number that
    matters is the trend on the chart at the back, not any single chapter."""
    rows = BLOCK_PTS
    total = sum(p for _, _, p in rows)
    head = "".join(f'<th>{k}</th>' for k, _, _ in rows) + '<th class="tot">Total</th>'
    cell = "".join(f'<td><span class="mk"></span><span class="of">/{p}</span></td>'
                   for _, _, p in rows) + \
           f'<td class="tot"><span class="mk"></span><span class="of">/{total}</span></td>'
    return ('<div class="score wbgrid"><span class="h">Cómo ha ido</span>'
            f'<table class="scoregrid"><thead><tr>{head}</tr></thead>'
            f'<tbody><tr>{cell}</tr></tbody></table>'
            '<p class="gate">No pass mark — this book is meant to make you get things wrong, because that '
            'is what makes them stick. Any block under <b>60%</b>, do what the routing table says. '
            'Then put the total on the chart at the back and watch the line, not the number.</p></div>')

# ---------------------------------------------------------------- answer key
# The keys arrive as one run-on paragraph per exercise — answer, reason and page
# reference all in the same grey italic, separated by middots, with the same
# routing string repeated for every item. It is accurate and nearly unusable:
# to mark item (g) you have to read the whole block. Split it into a table so
# the three things are three things: what the answer was, why, and where to look.
EXHEAD = re.compile(r'^\*\*Ex\s*(\d+)\s*[—:-]\s*(.*?)\*\*\s*', re.M)
ROUTE  = re.compile(r'\s*→\s*((?:A[12]\s+)?Unit\s+.*)$', re.S)


def _key_items(s):
    """Both writers' shapes reduce to one string of 'a) … · b) … · c) …'."""
    s = re.sub(r'\n\s*-\s+', ' · ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    marks, want = [], 'a'
    for m in re.finditer(r'(?:(?<=^)|(?<=[·\s]))([a-z])\)\s', s):
        if m.group(1) == want:
            marks.append((m.start(), m.end(), want))
            want = chr(ord(want) + 1)
    out = []
    for i, (st, en, ltr) in enumerate(marks):
        nxt = marks[i + 1][0] if i + 1 < len(marks) else len(s)
        out.append((ltr, s[en:nxt].strip().rstrip('·').strip()))
    return out, (s[:marks[0][0]].strip() if marks else s)


def _key_parts(chunk):
    """-> (answer, also-accept, why, where) for one item."""
    where = ""
    rm = ROUTE.search(chunk)
    if rm:
        where = rm.group(1).strip()
        chunk = chunk[:rm.start()].strip()
    # A spiral item carries two bracketed groups: the ° lane tag that says which
    # unit it came from, and the actual reason. Taking the first one put "A1-6"
    # in the why column and left the explanation stranded in the answer cell.
    lane, why, spans = "", "", list(re.finditer(r'\*\((.+?)\)\*', chunk))
    keep = []
    for m in spans:
        g = m.group(1).strip()
        if re.fullmatch(r'(?:A[12]-\d+|U\d+)', g):
            lane = g
        else:
            keep.append(g)
    if keep:
        why = max(keep, key=len)
    for m in reversed(spans):
        chunk = (chunk[:m.start()] + chunk[m.end():])
    chunk = chunk.strip()
    # the ° means "recycled from an earlier unit"; the lane tag now says which,
    # so the marker itself is noise in the key
    chunk = chunk.replace('°', '').strip()
    alt = ""
    am = re.search(r'·\s*also:\s*(.*?)\s*(?:·|$)', chunk)
    if am:
        alt = am.group(1).strip()
        chunk = (chunk[:am.start()] + chunk[am.end():]).strip()
        if alt in ("—", "-", ""):
            alt = ""
    if not why:
        n2 = re.search(r'·?\s*not\s+(.*)$', chunk)
        if n2:
            why = "not " + n2.group(1).strip()
            chunk = chunk[:n2.start()].strip()
    return chunk.strip(' ·'), alt, why, where, lane


def _short_route(r):
    """'Unit 0 → Gramática → "G · Numbers 0–10", then Práctica Ex 1'
       -> 'Unit 0 · Numbers 0–10 · Ex 1' — the words between are the same on
       every row and are what made the column unreadable."""
    if not r:
        return ""
    unit = re.match(r'((?:A[12]\s+)?Unit\s+\d+)', r)
    unit = unit.group(1) if unit else ""
    tgt = re.search(r'[“"]G\s*·\s*(.+?)[”"]', r)
    if not tgt:
        tgt = re.search(r'→\s*(?:Vocabulario|Gramática|En contexto)\s*→\s*([^,→]+)', r)
    tgt = tgt.group(1).strip() if tgt else ""
    ex = re.search(r'(?:Práctica\s*)?Ex\s*(\d+)', r[r.find("then"):] if "then" in r else "")
    bits = [b for b in (unit, tgt, f"Ex {ex.group(1)}" if ex else "") if b]
    return " · ".join(bits)


def render_answer_key(ans):
    """One table per exercise: letter, answer, then why and where."""
    out, blocks = [], EXHEAD.split(ans)
    if blocks[0].strip():
        out.append(B.md(blocks[0]))
    for i in range(1, len(blocks), 3):
        num, title, body = blocks[i], blocks[i + 1].strip().rstrip('.'), blocks[i + 2]
        items, lead = _key_items(body)
        out.append(f'<p class="akx"><b>Ex {num}</b> · {B.md_inline(title)}</p>')
        if not items:
            # a block with no lettered answers (the reconstruct task, the writing
            # task) is all lead, so printing both would print it twice
            out.append(f'<p class="aklead">{B.md_inline(body.strip())}</p>')
            continue
        if lead:
            out.append(f'<p class="aklead">{B.md_inline(lead)}</p>')
        rows = []
        for ltr, chunk in items:
            a, alt, why, where, lane = _key_parts(chunk)
            ans_cell = f'<b>{B.md_inline(a)}</b>' if a else ""
            if alt:
                ans_cell += f'<span class="alt">also: {B.md_inline(alt)}</span>'
            note = ""
            if why and why.lower() not in ("model", "modelo"):
                note = f'<span class="why">{B.md_inline(why)}</span>'
            elif why:
                note = '<span class="ismodel">worked example</span>'
            sr = _short_route(where)
            if sr:
                note += f'<span class="go">{B.esc_md(sr)}</span>'
            lt = f'{ltr})' + (f'<span class="lane">{B.esc_md(lane)}</span>' if lane else '')
            rows.append(f'<tr><td class="lt">{lt}</td><td class="ans">{ans_cell}</td>'
                        f'<td class="why">{note}</td></tr>')
        out.append('<table class="aktab"><tbody>' + "".join(rows) + '</tbody></table>')
    return "".join(out)


def build():
    B.TOC.clear(); B._IDS.clear()
    chapters = []
    for f in WB_FILES:
        chapters += parse_workbook(f"{BUILD}/{f}")
    if not chapters:
        print("no wb_*.md source files found in build/ — nothing to build"); return 1

    parts, answer_key = [], []
    parts.append(B.h(1, "How to use this book"))
    # md_file hands back raw markdown; the heading is emitted above, so drop the
    # file's own H1 rather than printing the title twice
    intro = B.md_file("wb_intro_es.md")
    if intro:
        parts.append(B.md(re.sub(r'^#\s+.*$', '', intro, count=1, flags=re.M)))

    n_ex = n_items = 0
    for nivel, uno, title, secs, answers in chapters:
        cid = B.hid(f"wb-{nivel}-{uno}")
        ctitle = f"{nivel} Unidad {uno} — {title}"
        # register it: a heading emitted as raw HTML never reaches B.TOC, and the
        # printed contents then lists only the answer-key sections — so looking up
        # a unit sent you to its answers instead of its exercises.
        B.TOC.append((1, cid, ctitle))
        parts.append(f'<h1 id="{cid}">{html.escape(ctitle)}</h1><div class="wbchapter">')
        for name, body in secs:
            if CUT_RE.search(body):
                body = CUT_RE.sub('', body)
                parts.append('<div class="wbcut"><span>Stop here if you are splitting this '
                             'chapter — come back within two days</span></div>')
            parts.append(render_section(name, body))
            n_ex += len(re.findall(r'^\*\*Exercise\s', body, re.M))
        parts.append(chapter_grid())
        parts.append('<p class="ansref"><small>Answers at the back, under '
                     f'<b>{nivel} Unidad {uno}</b>. Do the whole chapter first.</small></p>')
        parts.append('</div>')
        if answers:
            answer_key.append((f"{nivel} Unidad {uno} — {title}", answers))

    # -------- answer key --------
    parts.append(B.h(1, "Answer Key"))
    parts.append('<p class="lead">Mark your own work. Where a note follows an answer, '
                 'it is the rule the item was testing — read it even when you were right.</p>')
    for title, ans in answer_key:
        # level 3 keeps these out of the printed contents, which lists chapters and
        # "Answer Key" itself — the same twenty names twice would be noise. They
        # stay as headings on the page and in the PDF outline.
        aid = B.hid(title)
        B.TOC.append((3, aid, title))
        parts.append(f'<h2 class="akhead" id="{aid}">{html.escape(title)}</h2>')
        parts.append('<div class="answerkey">' + render_answer_key(ans) + '</div>')

    toc = ['<h1 class="toc-title">Contents</h1><ul class="toc">']
    for lvl, i, t in B.TOC:
        if lvl <= 2:
            toc.append(f'<li class="lvl{lvl}"><a href="#{i}">{html.escape(t)}</a></li>')
    toc.append('</ul>')

    cov = f"{PHOTOS}/_cover.jpg"
    covstyle = (f"background-image:linear-gradient(rgba(20,70,95,.42),rgba(10,45,65,.86)),"
                f"url('file://{cov}')" if os.path.exists(cov) else "")
    cover = (f'<div class="cover wbcover" style="{covstyle}">'
             f'<div class="kick">Companion workbook · A1 → A2</div>'
             f'<h1>Spanish for Beginners<br>The Exercise Book</h1>'
             f'<div class="rule"></div>'
             f'<div class="sub">One chapter for every unit of the course — {n_ex} exercises that bring back '
             f'the vocabulary and grammar you met units ago, with room to write and a key that explains</div>'
             f'<div class="meta"><div class="author">Aziz Dardouri</div>'
             f'<div class="badge">Workbook · {datetime.date.today().strftime("%d/%m/%Y")}</div></div></div>')

    sheet = os.environ.get("ES_STYLE", "style_wb_es.css")
    doc = (f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
           f'<title>Español A1–A2 · Cuaderno de Ejercicios — Aziz Dardouri</title>'
           f'<meta name="author" content="Aziz Dardouri">'
           f'<meta name="description" content="The companion exercise book to the Spanish A1-A2 course: '
           f'one chapter per unit, spaced revision of earlier vocabulary and grammar, reading and writing.">'
           f'<link rel="stylesheet" href="file://{BUILD}/{sheet}"></head><body>'
           f'{cover}{"".join(toc)}{"".join(parts)}</body></html>')
    open(f"{BUILD}/_workbook.html", "w", encoding="utf-8").write(doc)

    out = sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/Espanol_A1-A2_Cuaderno_Ejercicios.pdf"
    d = HTML(string=doc, base_url=BUILD)
    try:
        d.write_pdf(out, pdf_variant="pdf/ua-1")
    except Exception as e:
        print(f"  (pdf/ua-1 unavailable: {e}; writing a plain PDF)")
        d.write_pdf(out)
    print(f"PDF -> {out} ({os.path.getsize(out)//1024} KB) | chapters={len(chapters)} "
          f"exercises={n_ex} answer-key sections={len(answer_key)}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
