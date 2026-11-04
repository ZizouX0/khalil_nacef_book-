#!/usr/bin/env python3
"""Build the SIELE A2-B1 revision booklet: src/*.md -> HTML -> PDF (Chromium via Playwright).

Two passes: the first PDF is used only to find the page each chapter and section
starts on, so the contents page can print real page numbers.
"""
import html, os, re, subprocess, sys, unicodedata
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT_PDF = os.path.join(os.path.dirname(HERE), "SIELE_Revision_A2-B1.pdf")
HTML_OUT = os.path.join(HERE, "_siele.html")

CHAPTERS = [  # (file, css class, short label for the contents page)
    ("00_intro.md", "ch-intro", "How to use this booklet"),
    ("01_general.md", "ch-general", "The SIELE at a glance"),
    ("02_CL.md", "ch-CL", "Reading"),
    ("03_CA.md", "ch-CA", "Listening"),
    ("04_EIE.md", "ch-EIE", "Writing"),
    ("05_EIO.md", "ch-EIO", "Speaking"),
]

_LI = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
_BLANK = re.compile(r"_{3,}")
_B0, _B1 = "", ""


def normalize(t):
    """Blank line before lists/tables (python-markdown needs one)."""
    out = []
    for l in t.split("\n"):
        # python-markdown needs 4-space nesting; agents write 2 or 3 (CommonMark style)
        m = re.match(r"^( +)(?=([-*+]|\d+[.)])\s)", l)
        if m and len(m.group(1)) % 4:
            l = " " * (4 * -(-len(m.group(1)) // 4)) + l[len(m.group(1)):]
        # CommonMark hard break "text\" -> python-markdown's two trailing spaces
        l = re.sub(r"\\$", "  ", l)
        prev = out[-1] if out else ""
        is_li = bool(_LI.match(l))
        is_tb = l.lstrip().startswith("|")
        prev_tb = prev.lstrip().startswith("|")
        prev_bq = prev.lstrip().startswith(">")
        if is_li and prev.strip() and not _LI.match(prev) and not prev_tb and not prev_bq \
                and not prev.startswith((" ", "\t")):
            out.append("")
        if is_tb and prev.strip() and not prev_tb and not prev_bq:
            out.append("")
        out.append(l)
    return "\n".join(out)


def slug(s, used):
    s = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", s))
    s = re.sub(r"[^\w\s-]", "", s.encode("ascii", "ignore").decode()).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)[:60] or "s"
    base, i = s, 2
    while s in used:
        s = f"{base}-{i}"; i += 1
    used.add(s)
    return s


def md_to_html(t):
    t = _BLANK.sub(lambda m: f"{_B0}{len(m.group(0))}{_B1}", t)
    conv = markdown.Markdown(extensions=["tables", "sane_lists", "attr_list"])
    h = conv.convert(normalize(t.strip()))
    h = re.sub(_B0 + r"(\d+)" + _B1,
               lambda m: f'<span class="blank" style="width:{min(int(m.group(1)), 14) * 2.4:.1f}mm"></span>', h)
    h = re.sub(r"~~(.+?)~~", r"<del>\1</del>", h)
    # callouts
    def bq(m):
        body = m.group(1)
        head = re.search(r"<strong>([^<:]+):?</strong>", body[:200])
        cls = ""
        if head:
            k = head.group(1).strip().lower()
            if k.startswith(("tip", "consejo", "truco")): cls = "tip"
            elif k.startswith(("trap", "ojo", "warning", "careful", "trampa")): cls = "trap"
            elif k.startswith(("remember", "recuerda", "note", "teacher")): cls = "rem"
        return f'<blockquote class="{cls}">{body}</blockquote>'
    h = re.sub(r"<blockquote>(.*?)</blockquote>", bq, h, flags=re.S)
    # checklists "[ ]"
    h = re.sub(r"<li>(?:<p>)?\[ \]\s*", '<li class="todo">', h)
    return h


def build_html(page_map=None):
    used, toc, body = set(), [], []
    for fn, cls, label in CHAPTERS:
        path = os.path.join(SRC, fn)
        if not os.path.exists(path):
            print("missing", fn, file=sys.stderr); continue
        h = md_to_html(open(path, encoding="utf-8").read())

        def add_id(m):
            lvl, inner = m.group(1), m.group(2)
            sid = slug(inner, used)
            if lvl in ("1", "2"):
                toc.append((lvl, re.sub(r"<[^>]+>", "", inner), sid))
            return f'<h{lvl} id="{sid}">{inner}</h{lvl}>'
        h = re.sub(r"<h([1-3])>(.*?)</h\1>", add_id, h)
        body.append(f'<section class="chapter {cls}">{h}</section>')

    def num(sid):
        return str(page_map.get(sid, "")) if page_map else ""
    items = []
    for lvl, text, sid in toc:
        c = "c" if lvl == "1" else "s"
        if c == "s" and not any(k in text for k in ("In 30 seconds", "Task by task", "Words", "Practice exercises",
                                                     "book practice plan", "Answer key", "Top tips",
                                                     "Last 7 days", "Scores", "Final checklist", "Core toolkit")):
            continue
        items.append(f'<li class="{c}"><a href="#{sid}"><span class="t">{html.escape(html.unescape(text))}</span>'
                     f'<span class="dots"></span><span class="p">{num(sid)}</span></a></li>')
    cover = """
<div class="cover">
  <div class="kick">Revision booklet · target A2 → B1</div>
  <h1>SIELE<br>in 7 days</h1>
  <div class="sub">Tips, patterns that repeat, phrases that score, the best exercises in your books and original practice for all four tests.</div>
  <div class="bands"><span class="b1">📖 Reading</span><span class="b2">🎧 Listening</span><span class="b3">✍️ Writing</span><span class="b4">🗣️ Speaking</span></div>
  <div class="meta"><strong>Exam: 11 November 2026</strong><br>
  Built from: <em>Manual oficial para la preparación del SIELE</em> (2022) · <em>Guía oficial para preparadores del SIELE</em> (2019) ·
  extracts from Edelsa <em>Preparación al SIELE A1–C1</em> (2021).<br>
  Page references (“Manual p.23”, “Guía p.41”) are the PDF page numbers of your copies.</div>
</div>"""
    toc_html = f'<div class="toc ch-intro"><h1>Contents</h1><ol>{"".join(items)}</ol></div>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SIELE in 7 days</title>
<link rel="stylesheet" href="style_siele.css"></head><body>{cover}{toc_html}{''.join(body)}</body></html>""", toc


NODE = r"""
const { chromium } = require('playwright');
(async () => {
  const [,, src, out] = process.argv;
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + src, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;font-size:8px;color:#6b7280;padding:0 18mm;display:flex;justify-content:space-between;font-family:sans-serif"><span>SIELE in 7 days · A2–B1</span><span class="pageNumber"></span></div>' });
  await b.close();
})();
"""


def render(html_doc, out):
    open(HTML_OUT, "w", encoding="utf-8").write(html_doc)
    js = os.path.join(HERE, "_render.js")
    open(js, "w").write(NODE)
    subprocess.run(["node", js, HTML_OUT, out], check=True)


def find_pages(pdf, toc):
    """Find the page each heading starts on, searching forward in order."""
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip().lower()
    pages = [norm(p) for p in txt[:n]]
    pm, cur = {}, 2  # skip cover + contents
    for lvl, text, sid in toc:
        key = norm(html.unescape(text))[:40]
        for i in range(cur, n):
            # a chapter title starts its page; elsewhere the same words may be
            # quoted (the intro lists every chapter by name)
            hay = pages[i][:200] if lvl == "1" else pages[i]
            if key and key in hay:
                pm[sid] = i + 1; cur = i; break
    return pm


if __name__ == "__main__":
    doc, toc = build_html()
    tmp = os.path.join(HERE, "_pass1.pdf")
    render(doc, tmp)
    pm = find_pages(tmp, toc)
    doc, _ = build_html(pm)
    render(doc, OUT_PDF)
    os.remove(tmp)
    print("wrote", OUT_PDF)
