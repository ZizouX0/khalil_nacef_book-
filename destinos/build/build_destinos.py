#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Destinos notebook from episodes/ep*.yaml.

    python3 destinos/build/build_destinos.py [out.pdf]

One YAML file per episode holds the content; this script only lays it out, so
adding episode 7 never means touching the layout, and fixing the layout never
means touching 52 files.
"""
import glob, html, os, re, sys
import yaml
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EPISODES = os.path.join(ROOT, "episodes")
TREES = os.path.join(ROOT, "assets", "trees")
OUT = os.path.join(ROOT, "Destinos_Cuaderno.pdf")

INK, MUTED, FAINT, RULE, ACCENT = "#1d1b18", "#6d665c", "#9a9286", "#cfc6b8", "#a63d2a"

# Raquel's journey. The story leaves from La Gavia and comes back to it, so the
# strip has Mexico at both ends.
STOPS = [("mexico", "La Gavia", "México"), ("sevilla", "Sevilla", "España"),
         ("madrid", "Madrid", "España"), ("buenosaires", "Buenos Aires", "Argentina"),
         ("sanjuan", "San Juan", "Puerto Rico"), ("mexico-end", "Ciudad de México", "México")]

# Every episode number is also spelled out, so the opener page doubles as
# number practice: by episode 52 you have read every number up to it.
UNITS = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
         "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete",
         "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés",
         "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
TENS = {3: "treinta", 4: "cuarenta", 5: "cincuenta"}


def spell(n):
    if n < 30:
        return UNITS[n]
    t, u = divmod(n, 10)
    return TENS[t] + (f" y {UNITS[u]}" if u else "")


def esc(s):
    return html.escape(str(s), quote=False)


def md(s):
    """The little inline markdown the YAML uses: **bold**, *italic*, ~~wrong~~."""
    s = esc(s)
    s = re.sub(r'~~(.+?)~~', r'<s class="wrong">\1</s>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
    return s


ART = re.compile(r'(^|(?<=[\s·]))(el|la|los|las|un|una)(?=\s)')


def with_articles(s):
    """Grey the article so the noun stands out while the gender stays visible.
    A pair like "el hermano · la hermana" may only break at the middle dot, so
    an article is never left at the end of a line without its noun."""
    parts = [ART.sub(lambda m: m.group(1) + f'<span class="art">{m.group(2)}</span>', esc(p))
             for p in str(s).split(" · ")]
    return " · ".join(f'<span class="nw">{p}</span>' for p in parts)


def sec(es, en, body, cls=""):
    return (f'<div class="sec {cls}"><div class="sh"><span class="es">{esc(es)}</span>'
            f'<span class="en">{esc(en)}</span></div>{body}</div>')


# ---------------------------------------------------------------- route strip
def route_svg(stop, width=500, big=False):
    """A line through the six stops. Where you are is a filled red dot; where you
    have been is filled grey; where the story has not gone yet is an empty ring."""
    keys = [k for k, _, _ in STOPS]
    here = keys.index(stop) if stop in keys else -1
    pad, y = (52 if big else 46), (34 if big else 22)
    step = (width - 2 * pad) / (len(STOPS) - 1)
    h = 84 if big else 56
    fs, fs2 = (12, 7.6) if big else (9.6, 6.6)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {h}" width="{width}" height="{h}">']
    o.append(f'<path d="M{pad} {y} H{width - pad}" stroke="{RULE}" stroke-width="1.2" fill="none"/>')
    if here > 0:
        o.append(f'<path d="M{pad} {y} H{pad + here * step}" stroke="{MUTED}" stroke-width="1.2" fill="none"/>')
    for i, (_, city, country) in enumerate(STOPS):
        x = pad + i * step
        if i == here:
            dot = f'<circle cx="{x}" cy="{y}" r="5.2" fill="{ACCENT}"/>'
            col, wt = ACCENT, 700
        elif here >= 0 and i < here:
            dot = f'<circle cx="{x}" cy="{y}" r="3.4" fill="{MUTED}"/>'
            col, wt = INK, 400
        else:
            dot = f'<circle cx="{x}" cy="{y}" r="3.4" fill="#fff" stroke="{MUTED}" stroke-width="1"/>'
            col, wt = (INK if big else MUTED), 400
        o.append(dot)
        o.append(f'<text x="{x}" y="{y + 20}" text-anchor="middle" font-family="Charis" '
                 f'font-size="{fs}" font-weight="{wt}" fill="{col}">{esc(city)}</text>')
        o.append(f'<text x="{x}" y="{y + 20 + fs2 + 5}" text-anchor="middle" font-family="Plex" '
                 f'font-size="{fs2}" font-weight="500" letter-spacing="0.8" fill="{FAINT}">'
                 f'{esc(country.upper())}</text>')
    o.append('</svg>')
    return "".join(o)


# ---------------------------------------------------------------- front matter
def cover(first, last):
    return f'''
<div class="cover">
  <div class="top"><span>Cuaderno</span><span>Episodios {first}–{last}</span></div>
  <h1>Destinos</h1>
  <div class="sub">What each episode teaches, written down once and kept: the words, the verbs, the grammar and the phrases worth remembering.</div>
  <div class="map">{route_svg("", width=560, big=True)}</div>
  <div class="owner">
    <div><span class="k">Este cuaderno es de</span><span class="v"></span></div>
    <div><span class="k">Empezado el</span><span class="v"></span></div>
  </div>
</div>'''


def index(eps):
    """The contents page. Page numbers come from the layout itself, so the index
    stays right as episodes are added."""
    rows = "".join(f'<li><a href="#ep{int(e["episode"])}"><span class="n">{int(e["episode"])}</span>'
                   f'{esc(e["title"])} <i>{esc(e["title_en"])}</i></a></li>' for e in eps)
    return f'''
<div class="intro newpage">
  <div class="headmark" data-l="" data-r=""></div>
  <h2>Índice</h2>
  <ol class="toc">{rows}</ol>
</div>'''


# ---------------------------------------------------------------- one episode
PRON = ["yo", "tú", "él · ella · usted", "nosotros/as", "vosotros/as", "ellos · ellas · ustedes"]


def pairs(rows, cls="pairs"):
    """Spanish on the left, English on the right: cover one side to revise."""
    return (f'<table class="{cls}">' + "".join(
        f'<tr><td class="es">{md(a)}</td><td class="en">{md(b)}</td></tr>' for a, b in rows) + '</table>')


def word_groups(groups):
    return "".join(
        f'<div class="vgroup"><span class="lbl">{esc(g["group"])}</span><table class="words">'
        + "".join(f'<tr><td class="es">{with_articles(es)}</td><td class="en">{esc(en)}</td></tr>'
                  for es, en in g["words"])
        + '</table></div>' for g in groups)


def episode(ep):
    n = int(ep["episode"])
    head_r = f'Episodio {n} · {ep["title"]}'
    o = []
    pages = f' <span class="pp">{esc(ep["pages"])}</span>' if ep.get("pages") else ""

    o.append(f'''
<div class="opener" id="ep{n}">
  <div class="headmark" data-l="" data-r=""></div>
  <div class="num"><span class="lbl">Episodio</span><span class="n">{n}</span><span class="w">{spell(n)}</span></div>
  <div class="title">
    <h1>{esc(ep["title"])}</h1>
    <div class="en">{esc(ep["title_en"])}</div>
    <div class="where">Where <b>{esc(ep["setting"])}</b>{pages}</div>
  </div>
</div>
<div class="headmark" data-l="Destinos · cuaderno" data-r="{esc(head_r)}"></div>''')

    # the one box to read if you only have a minute
    if ep.get("essentials"):
        items = "".join(f'<li>{md(x)}</li>' for x in ep["essentials"])
        o.append(sec("Lo esencial", "In one minute", f'<ol class="ess">{items}</ol>', "keep"))

    if ep.get("story"):
        o.append(sec("La historia", "What happens",
                     pairs([(s["es"], s["en"]) for s in ep["story"]], "story"), "keep"))

    who = ""
    if ep.get("tree"):
        with open(os.path.join(TREES, ep["tree"]), encoding="utf-8") as f:
            who += f'<div class="tree">{f.read()}</div>'
    if ep.get("cast"):
        who += '<table class="cast">' + "".join(
            f'<tr><td class="who">{esc(a)}</td><td>{md(b)}</td><td class="en">{md(c)}</td></tr>'
            for a, b, c in ep["cast"]) + '</table>'
    if who:
        o.append(sec("Quién es quién", "Who's who", who, "keep"))

    if ep.get("place"):
        p = ep["place"]
        body = pairs(p["facts"], "facts")
        if p.get("timeline"):
            body += '<div class="timeline">' + "".join(
                f'<div><span class="c">{esc(c)}</span><span class="es">{md(es)}</span>'
                f'<span class="en">{md(en)}</span></div>' for c, es, en in p["timeline"]) + '</div>'
        if p.get("note"):
            body += f'<p class="aside">{md(p["note"])}</p>'
        o.append(sec("El lugar", p["name"], body, "keep"))

    # the verb of the lesson, as a table to picture
    if ep.get("verbs"):
        v, t = ep["verbs"], ep["verbs"]["table"]
        half = lambda rows, prons: "".join(
            f'<tr><td class="p">{p}</td><td class="f">{md(f)}</td><td class="m">{md(m)}</td></tr>'
            for p, (f, m) in zip(prons, rows))
        irr = '<span class="lbl">irregular</span>' if t.get("irregular") else ""
        body = (f'<div class="vhead"><span class="v">{esc(t["verb"])}</span>'
                f'<span class="mean">{esc(t["meaning"])}</span>{irr}</div>'
                f'<div class="conj2"><table class="cj"><thead><tr><th colspan="3">singular</th></tr></thead>'
                f'{half(t["forms"][:3], PRON[:3])}</table>'
                f'<table class="cj"><thead><tr><th colspan="3">plural</th></tr></thead>'
                f'{half(t["forms"][3:], PRON[3:])}</table></div>')
        if t.get("hook"):
            body += f'<div class="note"><span class="lbl">Remember</span>{md(t["hook"])}</div>'
        for nt in v.get("notes", []):
            body += f'<div class="note"><span class="lbl">{md(nt["label"])}</span>{md(nt["text"])}</div>'
        if v.get("met"):
            body += ('<div class="met"><span class="lbl">Other verbs in this lesson</span><table class="met">'
                     + "".join(f'<tr><td class="form">{esc(a)}</td><td class="inf">{esc(b)}</td>'
                               f'<td class="en">{esc(c)}</td></tr>' for a, b, c in v["met"])
                     + '</table></div>')
        o.append(sec("El verbo", t["verb"] + " · " + t["meaning"], body, "keep"))

    g = ""
    for p in ep.get("grammar", []):
        g += f'<div class="gpoint"><h3>{md(p["title"])}</h3>'
        if p.get("rule"):
            g += f'<p>{md(p["rule"])}</p>'
        if p.get("uses"):
            g += '<div class="uses">' + "".join(
                f'<div><span class="tag">{md(u["label"])}</span><p>{md(u["text"])}</p>{pairs(u["examples"], "ex")}</div>'
                for u in p["uses"]) + '</div>'
        if p.get("examples"):
            g += pairs(p["examples"], "ex")
        if p.get("trap"):
            g += f'<div class="note"><span class="lbl">Watch out</span>{md(p["trap"])}</div>'
        g += '</div>'
    if ep.get("rules"):
        g += ('<div class="gpoint"><h3>Small rules, big difference</h3><table class="rules">'
              + "".join(f'<tr><td class="r">{md(r)}</td><td class="x">{md(x)}</td></tr>' for r, x in ep["rules"])
              + '</table></div>')
    if g:
        o.append(sec("Gramática", "How it works", g))

    if ep.get("vocab"):
        v = ep["vocab"]
        body = ""
        if v.get("core"):
            body += ('<div class="tier"><b>Learn these first.</b> The lesson\'s own word list.</div>'
                     f'<div class="vocab">{word_groups(v["core"])}</div>')
        if v.get("extra"):
            body += ('<div class="tier"><b>Recognise these.</b> Also met in the episode, the textbook and the workbook.</div>'
                     f'<div class="vocab">{word_groups(v["extra"])}</div>')
        if v.get("course"):
            body += ('<div class="tier"><b>The book\'s own words.</b> Headings and instructions you will see in every lesson.</div>'
                     '<p class="course">' + "".join(f'<span><b>{esc(a)}</b> {esc(b)}</span>' for a, b in v["course"]) + '</p>')
        o.append(sec("Vocabulario", "Words", body))

    if ep.get("cognates"):
        c = ep["cognates"]
        body = f'<p>{md(c["rule"])}</p>'
        if c.get("patterns"):
            body += ('<div class="lbl sub">Spot the pattern</div><table class="pat">'
                     '<thead><tr><th>Spanish</th><th>English</th><th>Examples</th><th></th></tr></thead>'
                     + "".join(f'<tr><td class="s">{esc(a)}</td><td class="e">{esc(b)}</td>'
                               f'<td class="es">{esc(x)}</td><td class="en">{esc(y)}</td></tr>' for a, b, x, y in c["patterns"])
                     + '</table>')
        if c.get("false_friends"):
            body += ('<div class="lbl sub">False friends · ¡OJO!</div><table class="ff">'
                     + "".join(f'<tr><td class="es">{with_articles(a)}</td><td>= <b>{esc(b)}</b></td>'
                               f'<td class="not">not {esc(c2)}, which is <b>{with_articles(d)}</b></td></tr>'
                               for a, b, c2, d in c["false_friends"])
                     + '</table>')
        if c.get("harder"):
            body += ('<div class="lbl sub">Harder to spot, still guessable</div><table class="pairs">'
                     + "".join(f'<tr><td class="es">{with_articles(a)}</td><td><b>{esc(b)}</b></td>'
                               f'<td class="en">{md(h)}</td></tr>' for a, b, h in c["harder"])
                     + '</table>')
        if c.get("borrowed"):
            body += f'<p class="aside">{md(c["borrowed"])}</p>'
        o.append(sec("Cognados", "Words you already know", body, "keep"))

    if ep.get("sounds"):
        body = '<div class="tips">' + "".join(
            f'<div><h4>{md(s["title"])}</h4><p>{md(s["body"])}</p></div>' for s in ep["sounds"]) + '</div>'
        o.append(sec("Pronunciación", "How it sounds", body, "keep"))

    if ep.get("phrases"):
        o.append(sec("Frases útiles", "Ready to use", pairs(ep["phrases"], "phr"), "keep"))

    if ep.get("culture"):
        body = '<div class="tips">' + "".join(
            f'<div><h4>{md(s["title"])}</h4><p>{md(s["body"])}</p></div>' for s in ep["culture"]) + '</div>'
        o.append(sec("Cultura", "Good to know", body, "keep"))

    # a few ruled lines for whatever else the episode taught you
    lines = '<div class="l"></div>' * int(ep.get("note_lines", 6))
    o.append(sec("Mis notas", "Your own", f'<div class="lines">{lines}</div>', "keep"))
    return "".join(o)


def build(out=OUT):
    eps = []
    for path in sorted(glob.glob(os.path.join(EPISODES, "ep*.yaml"))):
        with open(path, encoding="utf-8") as f:
            eps.append(yaml.safe_load(f))
    eps.sort(key=lambda e: int(e["episode"]))
    with open(os.path.join(HERE, "destinos.css"), encoding="utf-8") as f:
        css = f.read()
    body = cover(eps[0]["episode"], 52) + index(eps) + "".join(episode(e) for e in eps)
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
           f'<title>Destinos · Cuaderno</title><style>{css}</style></head><body>{body}</body></html>')
    HTML(string=doc, base_url=ROOT).write_pdf(out)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else OUT))
