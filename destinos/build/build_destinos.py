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
def episode(ep):
    n = int(ep["episode"])
    head_r = f'Episodio {n} · {ep["title"]}'
    o = []

    # opener
    o.append(f'''
<div class="opener" id="ep{n}">
  <div class="headmark" data-l="" data-r=""></div>
  <div class="num"><span class="lbl">Episodio</span><span class="n">{n}</span><span class="w">{spell(n)}</span></div>
  <div class="title">
    <h1>{esc(ep["title"])}</h1>
    <div class="en">{esc(ep["title_en"])}</div>
    <div class="where">Where <b>{esc(ep["setting"])}</b></div>
  </div>
</div>
<div class="headmark" data-l="Destinos · cuaderno" data-r="{esc(head_r)}"></div>
<div class="route">{route_svg(ep.get("stop", ""))}</div>''')

    rows = "".join(f'<tr><td class="es">{md(s["es"])}</td><td class="en">{md(s["en"])}</td></tr>'
                   for s in ep["story"])
    o.append(sec("La historia", "What happens", f'<table class="story">{rows}</table>', "keep"))

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

    # words
    groups = "".join(
        f'<div class="vgroup"><span class="lbl">{esc(g["group"])}</span><table class="words">'
        + "".join(f'<tr><td class="es">{with_articles(es)}</td><td class="en">{esc(en)}</td></tr>'
                  for es, en in g["words"])
        + '</table></div>' for g in ep["vocab"])
    o.append(sec("Vocabulario", "Words to keep", f'<div class="vocab">{groups}</div>'))

    v = ep["verbs"]
    t = v["table"]
    pron = ["yo", "tú", "él · ella · usted", "nosotros/as", "vosotros/as", "ellos · ellas · ustedes"]
    cj = "".join(f'<tr><td class="p">{p}</td><td class="f">{esc(f)}</td></tr>' for p, f in zip(pron, t["forms"]))
    irr = '<span class="lbl">irregular</span>' if t.get("irregular") else ""
    met = "".join(f'<tr><td class="inf">{esc(a)}</td><td class="form">{esc(b)}</td><td class="en">{esc(c)}</td></tr>'
                  for a, b, c in v["met"])
    o.append(sec("Verbos", "Verbs", f'''
<div class="verbs">
  <div class="conj"><div class="head">{esc(t["verb"])}{irr}</div><div class="mean">{esc(t["meaning"])}</div>
    <table class="cj">{cj}</table></div>
  <div class="met"><span class="lbl">Also in this episode</span><table class="met">{met}</table></div>
</div>''', "keep"))

    # grammar
    g = ""
    for i, p in enumerate(ep["grammar"], 1):
        ex = "".join(f'<tr><td class="es">{md(a)}</td><td class="en">{md(b)}</td></tr>' for a, b in p["examples"])
        g += (f'<div class="gpoint"><h3><span class="k">{n}.{i}</span>{md(p["title"])}</h3>'
              f'<p>{md(p["rule"])}</p><table class="ex">{ex}</table>'
              f'<div class="trap"><span class="lbl">Watch out</span>{md(p["trap"])}</div></div>')
    o.append(sec("Gramática", "Grammar", g))

    ph = "".join(f'<tr><td class="es">{md(a)}</td><td class="en">{md(b)}</td></tr>' for a, b in ep["phrases"])
    o.append(sec("Frases útiles", "Ready to use", f'<table class="phr">{ph}</table>', "keep"))

    s, c = ep["sound"], ep["culture"]
    o.append(sec("Bueno saber", "Good to know", f'''
<div class="pair">
  <div><span class="lbl">Pronunciación</span><h4>{md(s["title"])}</h4><p>{md(s["body"])}</p></div>
  <div><span class="lbl">Cultura</span><h4>{md(c["title"])}</h4><p>{md(c["body"])}</p></div>
</div>''', "keep"))

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
