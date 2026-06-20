#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble le markdown final -> HTML (couverture + sommaire) -> PDF (WeasyPrint).
Usage: python3 build_pdf.py <input.md> <output.pdf>
"""
import sys, re, html, datetime, os
import markdown
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = os.path.join(HERE, "style.css")

COVER = """
<div class="cover">
  <div class="kicker">Deutsch · Niveau A1 &amp; A2</div>
  <h1>Allemand A1–A2<br>Manuel de révision complet</h1>
  <div class="rule"></div>
  <div class="sub">Grammaire détaillée &amp; Vocabulaire en contexte<br>d'après <em>Studio 21 – Das Deutschbuch</em></div>
  <div class="meta">
    <div class="author">Khalil Nacef</div>
    <div class="badge">Édition révision · {date}</div>
  </div>
</div>
"""

def build_toc(toc_tokens, max_level=3):
    """Construit un <ul class='toc'> à partir des tokens markdown (avec n° de page via CSS)."""
    out = ['<div class="toc-title">Sommaire</div>', '<ul class="toc">']
    def walk(tokens):
        for t in tokens:
            lvl = t['level']
            if lvl <= max_level:
                out.append(f'<li class="lvl{lvl}"><a href="#{t["id"]}">{html.escape(t["name"])}</a></li>')
            if t.get('children'):
                walk(t['children'])
    walk(toc_tokens)
    out.append('</ul>')
    return "\n".join(out)

LIST_RE = re.compile(r'^(\s*([-*+]|\d+[.)])\s+)')
def normalize_md(text):
    """Assure une ligne vide avant listes et tableaux (robustesse vs sorties d'agents)."""
    lines = text.split("\n")
    out = []
    def is_list(l): return bool(LIST_RE.match(l))
    def is_table(l): return l.lstrip().startswith("|")
    for i, l in enumerate(lines):
        prev = out[-1] if out else ""
        if (is_list(l) and prev.strip() and not is_list(prev) and not is_table(prev)):
            out.append("")
        if (is_table(l) and prev.strip() and not is_table(prev)):
            out.append("")
        out.append(l)
    return "\n".join(out)

def fix_emoji(t):
    # ⚠️ (+ espace) -> rien, pour ne pas casser le gras **⚠️ Pièges.**
    t = re.sub(r'⚠️?\s*', '', t)
    # 🔺 -> triangle DejaVu-safe ; 📖 💬 🔤 -> retirés (les titres restent clairs)
    for k, v in {'\U0001F53A': '▲ ', '\U0001F4D6': '', '\U0001F4AC': '',
                 '\U0001F524': '', '️': ''}.items():
        t = t.replace(k, v)
    # nettoie les espaces surnuméraires laissés dans les titres
    t = re.sub(r'^(#{1,6})[ \t]+', r'\1 ', t, flags=re.M)
    return t

def main():
    inp, outp = sys.argv[1], sys.argv[2]
    text = open(inp, encoding="utf-8").read()
    text = fix_emoji(text)
    text = normalize_md(text)

    md = markdown.Markdown(extensions=['tables', 'attr_list', 'toc', 'sane_lists', 'fenced_code', 'md_in_html'],
                           extension_configs={'toc': {'toc_depth': '1-2'}})
    body = md.convert(text)
    toc = build_toc(md.toc_tokens, max_level=2)

    doc = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{CSS}"></head>
<body>
{COVER.format(date=datetime.date.today().strftime('%d/%m/%Y'))}
{toc}
{body}
</body></html>"""

    # sauvegarde le HTML pour debug
    open(os.path.join(HERE, "tmp", "final.html") if os.path.isdir(os.path.join(HERE,'tmp')) else os.path.join(HERE,"_final_debug.html"), "w", encoding="utf-8").write(doc)

    HTML(string=doc, base_url=HERE).write_pdf(outp)
    print(f"PDF généré : {outp}  ({os.path.getsize(outp)//1024} Ko)")

if __name__ == "__main__":
    main()
