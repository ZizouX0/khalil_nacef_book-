#!/usr/bin/env python3
"""Build the SIELE A2-B1 revision booklet (visual edition).

src/*.md (Markdown + the ":::block" components described in COMPONENTS.md)
  -> HTML (style_siele.css) -> PDF with Chromium via Playwright.

Two passes: the first PDF is only used to find the page each chapter and
section starts on, so the contents page can print real page numbers.
"""
import html, os, re, subprocess, sys, unicodedata
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.dirname(HERE)
HTML_OUT = os.path.join(HERE, "_siele.html")

# Three books. Each: source folder, output file, chapters (file, css class), cover text.
BOOKS = {
    "guide": dict(
        src="src", out="SIELE_1_Guide.pdf", footer="SIELE in 7 days · 1 Guide",
        kick="Book 1 of 4 · the guide", title="SIELE", sub="in 7 days",
        blurb="What you need to know and remember for the four tests: how each task works, the traps, "
              "the tricks, and a plan for every day until the exam.",
        chapters=[("00_intro.md", "ch-intro"), ("01_general.md", "ch-general"), ("02_CL.md", "ch-CL"),
                  ("03_CA.md", "ch-CA"), ("04_EIE.md", "ch-EIE"), ("05_EIO.md", "ch-EIO"),
                  ("06_memory.md", "ch-memory")]),
    "practice": dict(
        src="src_practice", out="SIELE_2_Practice.pdf", footer="SIELE in 7 days · 2 Practice",
        kick="Book 2 of 4 · practice", title="SIELE", sub="practice",
        blurb="Original exam-style tasks for reading, listening (with audio tracks 01–06) and speaking, "
              "with every answer explained at the end of each chapter.",
        chapters=[("p0_intro.md", "ch-intro"), ("p1_CL.md", "ch-CL"), ("p1b_CL_T45.md", "ch-CL"), ("p2_CA.md", "ch-CA"),
                  ("p4_EIO.md", "ch-EIO")]),
    "writing": dict(
        src="src_writing", out="SIELE_3_Writing_Workbook.pdf", footer="SIELE in 7 days · 3 Writing workbook",
        kick="Book 3 of 4 · writing workbook", title="SIELE", sub="writing, day by day",
        blurb="Six days, one full writing exam a day (Tarea 1 + Tarea 2). Lots of help on the first days, "
              "less each day, exam conditions at the end, and a model answer for every task.",
        chapters=[("w1_workbook.md", "ch-EIE workbook")]),
    "start": dict(
        src="src_start", out="SIELE_0_Start_Here.pdf", footer="SIELE in 7 days · 0 Start here", plain=True,
        kick="", title="", sub="", blurb="", chapters=[("00_materials.md", "ch-intro")]),
    "speaking": dict(
        src="src_speaking", out="SIELE_4_Speaking_Book.pdf", footer="SIELE in 7 days · 4 Speaking book",
        kick="Book 4 of 4 · speaking book", title="SIELE", sub="speaking, task by task",
        blurb="Many exam-style speaking tasks for all five tareas, each followed by a model that shows "
              "how to answer: what to say, in which order, and how long to speak.",
        chapters=[("s0_intro.md", "ch-intro"), ("s1_T1.md", "ch-EIO"), ("s2_T2.md", "ch-EIO"),
                  ("s3_T3.md", "ch-EIO"), ("s4_T45.md", "ch-EIO"), ("s9_credits.md", "ch-intro")]),
}
BOOK = BOOKS["guide"]
SRC = os.path.join(HERE, BOOK["src"])
CHAPTERS = BOOK["chapters"]

# ----------------------------------------------------------------------------
# Markdown with the house extras
# ----------------------------------------------------------------------------
_LI = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
_BLANK = re.compile(r"_{3,}")
_B0, _B1 = "", ""
_LEVELS = r"(?:A1|A2|B1|B2|C1)"


def normalize(t):
    """Make agent Markdown palatable to python-markdown."""
    out = []
    for l in t.split("\n"):
        # python-markdown needs 4-space nesting; agents write 2 or 3 (CommonMark style)
        m = re.match(r"^( +)(?=([-*+]|\d+[.)])\s)", l)
        if m and len(m.group(1)) % 4:
            l = " " * (4 * -(-len(m.group(1)) // 4)) + l[len(m.group(1)):]
        # CommonMark hard break "text\" -> two trailing spaces
        l = re.sub(r"\\$", "  ", l)
        prev = out[-1] if out else ""
        is_li, is_tb = bool(_LI.match(l)), l.lstrip().startswith("|")
        prev_tb, prev_bq = prev.lstrip().startswith("|"), prev.lstrip().startswith(">")
        if is_li and prev.strip() and not _LI.match(prev) and not prev_tb and not prev_bq \
                and not prev.startswith((" ", "\t")):
            out.append("")
        if is_tb and prev.strip() and not prev_tb and not prev_bq:
            out.append("")
        out.append(l)
    return "\n".join(out)


def pre_inline(t):
    t = _BLANK.sub(lambda m: f"{_B0}{len(m.group(0))}{_B1}", t)
    t = re.sub(r"==([^=\n]+?)==", r"<mark>\1</mark>", t)
    t = re.sub(r"\[(" + _LEVELS + r")\](?!\()", lambda m: f'<span class="lv lv-{m.group(1).lower()}">{m.group(1)}</span>', t)
    return t


def post_inline(h):
    h = re.sub(_B0 + r"(\d+)" + _B1,
               lambda m: f'<span class="blank" style="width:{min(int(m.group(1)), 14) * 2.4:.1f}mm"></span>', h)
    h = re.sub(r"~~(.+?)~~", r"<del>\1</del>", h)
    # source references -> small grey tags
    h = re.sub(r"\(((?:Manual|Guía|Guia|Edelsa)\b[^()<>]{0,80})\)", r'<span class="ref">\1</span>', h)
    # checklists written as "[ ]"
    h = re.sub(r"<li>(?:<p>)?\[ \]\s*", "<li>", h)
    return h


def md(t):
    conv = markdown.Markdown(extensions=["tables", "sane_lists", "attr_list"])
    return post_inline(conv.convert(normalize(pre_inline(t.strip()))))


def inline(t):
    h = md(t).strip()
    m = re.fullmatch(r"<p>(.*)</p>", h, flags=re.S)
    return m.group(1) if m else h


# ----------------------------------------------------------------------------
# ::: blocks
# ----------------------------------------------------------------------------
OPEN = re.compile(r"^:::\s*([a-zA-Z]+)\s*(.*)$")
CLOSE = re.compile(r"^:::\s*$")


def parse(lines, i=0, inside=False):
    items, buf = [], []

    def flush():
        if buf:
            items.append(("text", "\n".join(buf)))
            buf.clear()
    while i < len(lines):
        s = lines[i].strip()
        if CLOSE.match(s):
            if inside:
                flush()
                return items, i + 1
            i += 1
            continue
        m = OPEN.match(s)
        if m:
            flush()
            children, i = parse(lines, i + 1, True)
            items.append(("block", m.group(1).lower(), m.group(2).strip(), children))
            continue
        buf.append(lines[i])
        i += 1
    flush()
    return items, i


def text_of(items):
    return "\n".join(it[1] for it in items if it[0] == "text")


def render_items(items):
    parts, ph = [], {}
    for it in items:
        if it[0] == "text":
            parts.append(it[1])
        else:
            key = f"{len(ph)}"
            ph[key] = render_block(*it[1:])
            parts.append(f"\n\n{key}\n\n")
    h = md("\n".join(parts))
    for k, v in ph.items():
        h = h.replace(f"<p>{k}</p>", v).replace(k, v)
    return h


_HEADER_WORDS = {"español", "espanol", "spanish", "front", "label", "letter", "level", "nivel", "emoji",
                 "big", "number", "frase", "phrase", "time", "tiempo", "icon", "step", "l"}


def rows(items, min_cells=1):
    out = []
    for l in text_of(items).split("\n"):
        s = l.strip()
        if not s or re.fullmatch(r"[\s|:\-–]+", s):
            continue
        s = re.sub(r"^[-*]\s+", "", s)          # tolerate bullets
        c = [x.strip() for x in s.strip("|").split("|")]
        if not out and c and c[0].lower().strip("* ") in _HEADER_WORDS:
            continue                             # table header row
        if len(c) >= min_cells:
            out.append(c)
    return out


def cell(c, i):
    return inline(c[i]) if len(c) > i and c[i] else ""


def lvl_pill(tag):
    t = tag.strip()
    if re.fullmatch(_LEVELS + r"(?:[–-]" + _LEVELS + r")?", t):
        return f'<span class="lv lv-{t[:2].lower()}">{html.escape(t)}</span>'
    return f'<span class="tag">{inline(t)}</span>' if t else ""


def split_dash(items):
    """split a block body on a line that is exactly '---'"""
    left, right, cur = [], [], None
    cur = left
    for it in items:
        if it[0] != "text":
            cur.append(it)
            continue
        chunks = re.split(r"(?m)^\s*---\s*$", it[1])
        for j, ch in enumerate(chunks):
            if j > 0:
                cur = right
            cur.append(("text", ch))
    return left, right


def render_block(name, arg, items):
    t = inline(arg) if arg else ""
    if name == "stats":
        tiles = "".join(f'<div class="stat"><div class="n">{cell(c, 0)}</div><div class="l">{cell(c, 1)}</div></div>'
                        for c in rows(items))
        return f'<div class="stats">{tiles}</div>'
    if name == "golden":
        return f'<div class="golden"><div class="gh">★ {t or "Golden rules"}</div>{render_items(items)}</div>'
    if name == "big":
        return f'<div class="big">{render_items(items)}</div>'
    if name == "flow":
        rs = rows(items)
        n = len(rs)
        per = n if n <= 5 else -(-n // 2) if n <= 10 else 5   # items per row, rows as even as possible
        steps = "".join(f'<div class="fs{" end" if (i + 1) % per == 0 or i == n - 1 else ""}">'
                        f'<div class="ft">{cell(c, 0)}</div><div class="fd">{cell(c, 1)}</div></div>'
                        for i, c in enumerate(rs))
        head = f'<div class="fh">{t}</div>' if t else ""
        return f'<div class="flow">{head}<div class="fsteps" style="--per:{max(per, 1)}">{steps}</div></div>'
    if name == "steps":
        return f'<div class="steps"><div class="sh">🪜 {t or "How to do it"}</div>{render_items(items)}</div>'
    if name in ("trap", "tip", "remember", "note", "warning"):
        kind = {"warning": "trap", "note": "tip"}.get(name, name)
        icon = {"trap": "⚠️", "tip": "💡", "remember": "📌"}[kind]
        default = {"trap": "Trap!", "tip": "Tip", "remember": "Remember!"}[kind]
        return (f'<div class="card {kind}"><div class="ch"><span class="ci">{icon}</span>{t or default}</div>'
                f'<div class="cb">{render_items(items)}</div></div>')
    if name == "levelup":
        l, r = split_dash(items)
        return (f'<div class="levelup"><div class="luh">⬆️ {t or "Level up: A2 → B1"}</div><div class="lucols">'
                f'<div class="lu a2"><div class="lutag">A2</div>{render_items(l)}</div>'
                f'<div class="luarrow">➜</div>'
                f'<div class="lu b1"><div class="lutag">B1</div>{render_items(r)}</div></div></div>')
    if name == "phrases":
        cards = "".join(f'<div class="pc"><div class="es">{cell(c, 0)}</div><div class="en">{cell(c, 1)}</div>'
                        f'{lvl_pill(c[2]) if len(c) > 2 else ""}</div>' for c in rows(items))
        head = f'<div class="ph">💬 {t}</div>' if t else ""
        return f'<div class="phrases">{head}<div class="pgrid">{cards}</div></div>'
    if name == "mnemonic":
        rs = "".join(f'<div class="mr"><div class="ml">{cell(c, 0)}</div><div class="mw">{cell(c, 1)}</div>'
                     f'<div class="mm">{cell(c, 2)}</div></div>' for c in rows(items))
        return f'<div class="mnemo"><div class="mword"><span>🧠</span>{t}</div><div class="mrows">{rs}</div></div>'
    if name == "model":
        main, why = split_dash(items)
        w = f'<div class="mwhy">{render_items(why)}</div>' if why else ""
        return f'<div class="model"><div class="mh">✉️ {t or "Model answer"}</div><div class="mb">{render_items(main)}</div>{w}</div>'
    if name == "exam":
        return (f'<div class="exam"><div class="eh"><span class="dots"><i></i><i></i><i></i></span>'
                f'<span>{t or "Práctica"}</span></div><div class="eb">{render_items(items)}</div></div>')
    if name == "transcript":
        return (f'<div class="transcript"><div class="trh">🔊 {t or "Transcript"} '
                f'<span>· cover this and listen first</span></div>{render_items(items)}</div>')
    if name == "answers":
        return f'<div class="answers"><div class="ah">✅ {t or "Answers"}</div>{render_items(items)}</div>'
    if name == "scale":
        segs = ""
        for c in rows(items):
            flag = c[2].strip().lower() if len(c) > 2 else ""
            label = {"target": "🎯 target", "safe": "🛟 safety net"}.get(flag, "")
            segs += (f'<div class="seg {flag}"><b>{cell(c, 0)}</b><span>{cell(c, 1)}</span>'
                     f'{f"<em>{label}</em>" if label else ""}</div>')
        head = f'<div class="sch">{t}</div>' if t else ""
        return f'<div class="scale">{head}<div class="bar">{segs}</div></div>'
    if name == "icons":
        ic = "".join(f'<div class="ic"><div class="ie">{cell(c, 0)}</div><div class="it">{cell(c, 1)}</div></div>'
                     for c in rows(items, 2))
        head = f'<div class="ich">{t}</div>' if t else ""
        return f'<div class="icons">{head}<div class="igrid">{ic}</div></div>'
    if name == "day":
        p = [x.strip() for x in arg.split("|")]
        return (f'<div class="day"><div class="dh"><span class="dd">{inline(p[0]) if p else ""}</span>'
                f'<span class="dt">{inline(p[1]) if len(p) > 1 else ""}</span></div>'
                f'<div class="db checks">{render_items(items)}</div></div>')
    if name == "checklist":
        return f'<div class="checklist"><div class="clh">☑️ {t or "Checklist"}</div><div class="checks">{render_items(items)}</div></div>'
    if name == "flashcards":
        cards = "".join(f'<div class="fc"><div class="front"><span>{cell(c, 0)}</span></div><div class="back"><span>{cell(c, 1)}</span></div></div>'
                        for c in rows(items))
        return (f'<div class="fcwrap"><div class="fch">✂️ {t or "Flashcards"} '
                f'<span>· cut out, fold on the dotted line, test yourself</span></div><div class="fcgrid">{cards}</div></div>')
    if name == "photopair":
        # one exam photo pair: lines "file | caption"; files live in photos_speaking/
        cells = []
        for i, c in enumerate(rows(items, 1), 1):
            cap = cell(c, 1)
            cells.append(f'<figure><div class="ph-opt">Opción {i}</div><img src="photos_speaking/{c[0].strip()}" alt="">'
                         f'{f"<figcaption>{cap}</figcaption>" if cap else ""}</figure>')
        return f'<div class="photopair">{"".join(cells)}</div>'
    if name == "lines":
        n = int(re.sub(r"\D", "", arg) or 12)
        return f'<div class="lines">{"<i></i>" * n}</div>'
    print(f"  ! unknown block :::{name}", file=sys.stderr)
    return f'<div class="box">{render_items(items)}</div>'


# ----------------------------------------------------------------------------
# Headings, chapters, contents
# ----------------------------------------------------------------------------
_EMOJI_LEAD = re.compile(r"^\s*([\U0001F300-\U0001FAFF☀-➿⬀-⯿][️‍\U0001F300-\U0001FAFF]*)\s*")


def slug(s, used):
    s = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", s))
    s = re.sub(r"[^\w\s-]", "", s.encode("ascii", "ignore").decode()).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)[:60] or "s"
    base, i = s, 2
    while s in used:
        s = f"{base}-{i}"
        i += 1
    used.add(s)
    return s


def badge_levels(inner):
    return re.sub(r"\s*·\s*(" + _LEVELS + r"(?:\s*[–-]\s*" + _LEVELS + r")?)\s*(?:·\s*|$)",
                  lambda m: f' <span class="lvbadge lv-{m.group(1)[:2].lower()}">{m.group(1).replace(" ", "")}</span> ',
                  inner)


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def build_chapter(fn, cls, used, toc):
    path = os.path.join(SRC, fn)
    if not os.path.exists(path):
        print("missing", fn, file=sys.stderr)
        return ""
    items, _ = parse(open(path, encoding="utf-8").read().split("\n"))
    h = render_items(items)
    chap = None

    def head(m):
        nonlocal chap
        lvl, inner = m.group(1), m.group(2)
        sid = slug(inner, used)
        if lvl == "1":
            em = _EMOJI_LEAD.match(plain(inner))
            icon = em.group(1) if em else ""
            title = plain(inner)[em.end():] if em else plain(inner)
            es, _, en = title.partition(" · ")
            chap = [title, sid, []]
            toc.append(chap)
            return (f'<header class="opener" id="{sid}"><div class="oi">{icon}</div>'
                    f'<div class="ot"><div class="oes">{html.escape(es)}</div>'
                    f'{f"<div class=oen>{html.escape(en)}</div>" if en else ""}</div></header>')
        if lvl == "2" and chap is not None:
            chap[2].append((plain(re.sub(r"<span class=\"lvbadge[^>]*>([^<]*)</span>", r"· \1 ·", inner)), sid))
        return f'<h{lvl} id="{sid}">{badge_levels(inner)}</h{lvl}>'
    h = re.sub(r"<h([1-3])>(.*?)</h\1>", head, h, flags=re.S)
    return f'<section class="chapter {cls}">{h}</section>'


def build_html(page_map=None):
    used, toc = set(), []
    body = "".join(build_chapter(fn, cls, used, toc) for fn, cls in CHAPTERS)
    pm = page_map or {}
    cards = ""
    classes = [c for f, c in CHAPTERS if os.path.exists(os.path.join(SRC, f))]
    for (title, sid, secs), cls in zip(toc, classes):
        em = ""
        es, _, en = title.partition(" · ")
        lis = "".join(f'<li><a href="#{s}"><span>{html.escape(re.sub(r" ·.*$", "", t) if "Tarea" in t else t)}</span>'
                      f'<b>{pm.get(s, "")}</b></a></li>' for t, s in secs
                      if not re.match(r"(?i)\W*answers?\b", t))
        cards += (f'<div class="tc {cls}"><a class="tct" href="#{sid}"><span>{html.escape(es)}'
                  f'{f"<small>{html.escape(en)}</small>" if en else ""}</span><b>{pm.get(sid, "")}</b></a>'
                  f'<ul>{lis}</ul></div>')
    cover = """
<div class="cover {cls}">
  <div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div><div class="blob b4"></div>
  <div class="cv-in">
    <div class="kick">{kick}</div>
    <h1 class="cvt">{title}<br><span>{sub}</span></h1>
    <p class="cvs">{blurb}</p>
    <div class="cv-tiles">
      <div class="t t1"><i>📖</i><b>Reading</b><span>Comprensión de lectura</span></div>
      <div class="t t2"><i>🎧</i><b>Listening</b><span>Comprensión auditiva</span></div>
      <div class="t t3"><i>✍️</i><b>Writing</b><span>Expresión escrita</span></div>
      <div class="t t4"><i>🗣️</i><b>Speaking</b><span>Expresión oral</span></div>
    </div>
    <div class="cv-goal"><div class="ring"><b>B1</b><span>goal</span></div><div class="ring safe"><b>A2</b><span>safety net</span></div>
      <div class="exam-date"><span>Exam day</span><b>11 November 2026</b></div></div>
    <div class="cv-books"><span class="{b1}">1 · Guide</span><span class="{b2}">2 · Practice</span><span class="{b3}">3 · Writing workbook</span><span class="{b4}">4 · Speaking book</span></div>
    <div class="cv-src">Built from the <i>Manual oficial para la preparación del SIELE</i> (2022), the <i>Guía oficial para
    preparadores del SIELE</i> (2019) and extracts from Edelsa <i>Preparación al SIELE</i> (2021).
    Grey tags like <span class="ref">Manual p.52</span> are PDF page numbers in your copies.</div>
  </div>
</div>""".format(cls=BOOK.get("key", ""), b1="on" if BOOK.get("key") == "guide" else "",
           b2="on" if BOOK.get("key") == "practice" else "", b3="on" if BOOK.get("key") == "writing" else "",
           b4="on" if BOOK.get("key") == "speaking" else "",
           **{k: BOOK[k] for k in ("kick", "title", "sub", "blurb")})
    toc_html = f'<div class="toc"><h2 class="toch">What\'s inside</h2><div class="tcgrid">{cards}</div></div>'
    if BOOK.get("plain"):
        cover = toc_html = ""
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{BOOK["footer"]}</title>
<link rel="stylesheet" href="style_siele.css"></head><body>{cover}{toc_html}{body}</body></html>"""
    return doc, toc


NODE = r"""
const { chromium } = require('playwright');
(async () => {
  const [,, src, out] = process.argv;
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + src, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;font-size:8px;color:#94a3b8;padding:0 16mm;display:flex;justify-content:space-between;font-family:sans-serif"><span>__FOOTER__</span><span class="pageNumber"></span></div>' });
  await b.close();
})();
"""


def render(html_doc, out):
    open(HTML_OUT, "w", encoding="utf-8").write(html_doc)
    js = os.path.join(HERE, "_render.js")
    open(js, "w").write(NODE.replace("__FOOTER__", BOOK["footer"]))
    subprocess.run(["node", js, HTML_OUT, out], check=True)


def find_pages(pdf, toc):
    """Page each heading starts on, searching forward in document order."""
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip().lower()
    pages = [norm(p) for p in txt[:n]]
    pm, cur = {}, 2  # skip cover + contents
    for title, sid, secs in toc:
        key = norm(title.partition(" · ")[0])[:40]
        for i in range(cur, n):
            if key and key in pages[i][:200]:   # a chapter opener starts its page
                pm[sid] = i + 1
                cur = i
                break
        for t, s in secs:
            k = norm(t)[:40]
            for i in range(cur, n):
                if k and k in pages[i]:
                    pm[s] = i + 1
                    cur = i
                    break
    return pm


def build_book(key):
    global BOOK, SRC, CHAPTERS
    BOOK = dict(BOOKS[key], key=key)
    SRC, CHAPTERS = os.path.join(HERE, BOOK["src"]), BOOK["chapters"]
    out = os.path.join(OUT_DIR, BOOK["out"])
    doc, toc = build_html()
    tmp = os.path.join(HERE, "_pass1.pdf")
    render(doc, tmp)
    doc, _ = build_html(find_pages(tmp, toc))
    render(doc, out)
    os.remove(tmp)
    print("wrote", out)


if __name__ == "__main__":
    for key in (sys.argv[1:] or list(BOOKS)):
        build_book(key)
