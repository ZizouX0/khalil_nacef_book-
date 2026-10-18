#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Destinos exercise book from private/exercises/ex*.yaml.

    python3 destinos/build/build_ejercicios.py [out.pdf]
    python3 destinos/build/build_ejercicios.py --episodes 3,4 [out.pdf]

The best exercises of each lesson, taken word for word from the learner's own
Textbook and Workbook (those that work without the audio), with the answers
from the books' keys at the back. Because the exercises are the books' own
text, the episode files and the PDF live in destinos/private/, which is not
committed: the repository is public.

An episode file holds a list of sets. Each set has a type, a Spanish title, an
English subtitle, an instruction and its items:

    words      [question, answer]                one-word recall, in two columns
    fill       [sentence with ___ , answer]      [cue] in square brackets is printed as a hint
    choose     [sentence with ___ , [options], answer]
    error      [sentence with one mistake, corrected sentence]
    translate  [English sentence, Spanish sentence]
    complete   [the start of a sentence or its cues, the whole sentence]   a line to write it on
    write      a prompt, a number of lines and, optionally, a model answer
               (or a `key`: what the book's key says, printed as it is)
    text       a paragraph with numbered gaps {1}, {2}…; items are the answers in order
    match      items [left, answer]; `options` is the right-hand column, lettered a, b, c…

Any set may also have a `bank` (a list of words to choose from) and a `source`
(where it is in the book: "Workbook p. 13 · Actividad A").

Any item may end with an episode number: it is then a review item from that
episode. The number is printed in the key only, never next to the item, so the
item still tests the rule and not the memory of where it came from.
"""
import glob, os, re, sys
import yaml
from weasyprint import HTML

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_destinos as B

HERE, ROOT = B.HERE, B.ROOT
PRIVATE = os.path.join(ROOT, "private")
EXERCISES = os.path.join(PRIVATE, "exercises")
OUT = os.path.join(PRIVATE, "Destinos_Ejercicios.pdf")
esc, md, sec = B.esc, B.md, B.sec
LETTERS = "ABCDEFGHIJKLMNOP"


def gapped(s):
    """___ becomes a line to write on, [cue] a grey hint."""
    s = md(s)
    s = re.sub(r'_{3,}', '<span class="gap"></span>', s)
    s = re.sub(r'\[(.+?)\]', r'<span class="cue">\1</span>', s)
    return s


def split_item(item, kind):
    """-> (question, options, answer, episode) whatever the item's shape."""
    if not isinstance(item, list):        # a text set's items are just its answers
        return "", None, item, None
    item = list(item)
    ep = item.pop() if isinstance(item[-1], int) else None
    if kind == "choose":
        q, opts, a = item
    else:
        q, a = item
        opts = None
    return q, opts, a, ep


# ---------------------------------------------------------------- one set
def render_set(letter, s):
    kind = s["type"]
    head = f'<span class="setl">{letter}</span>{esc(s["title"])}'
    instr = f'<p class="instr">{md(s["instr"])}</p>' if s.get("instr") else ""
    if s.get("source"):
        instr = f'<p class="source">{esc(s["source"])}</p>' + instr
    if s.get("bank"):
        instr += '<p class="bank">' + "".join(f'<span>{md(w)}</span>' for w in s["bank"]) + '</p>'
    if kind == "text":
        t = md(s["text"])
        t = re.sub(r'\{(\d+)\}', r'<span class="gap ngap"><span class="gn">\1</span></span>', t)
        paras = "".join(f'<p>{p.strip()}</p>' for p in t.split("\n\n") if p.strip())
        return sec_raw(head, s.get("en", ""), instr + f'<div class="ctext">{paras}</div>')
    if kind == "match":
        left = "".join(f'<li><span class="mq">{md(split_item(it, kind)[0])}</span>'
                       f'<span class="mblank"></span></li>' for it in s["items"])
        right = "".join(f'<li><span class="ml">{chr(97 + i)}</span>{md(o)}</li>'
                        for i, o in enumerate(s["options"]))
        return sec_raw(head, s.get("en", ""), instr +
                       f'<div class="match"><ol class="items mleft">{left}</ol><ul class="mright">{right}</ul></div>')
    if kind == "write":
        lines = '<div class="wline"></div>' * int(s.get("lines", 5))
        body = instr + f'<p class="prompt">{md(s["prompt"])}</p><div class="wlines">{lines}</div>'
        # the instructions and the lines to write on stay on one page
        return sec_raw(head, s.get("en", ""), body, "keep")

    li = []
    for it in s["items"]:
        q, opts, a, ep = split_item(it, kind)
        if kind == "words":
            li.append(f'<li><span class="q">{md(q)}</span><span class="blank"></span></li>')
        elif kind == "fill":
            li.append(f'<li>{gapped(q)}</li>')
        elif kind == "choose":
            o = '<span class="or">/</span>'.join(f'<span class="opt">{esc(x)}</span>' for x in opts)
            li.append(f'<li>{gapped(q)} <span class="opts">{o}</span></li>')
        else:  # error, translate, complete: the sentence, then a line to write the answer on
            li.append(f'<li>{gapped(q)}<div class="aline"></div></li>')
    cls = "items words" if kind == "words" else "items"
    return sec_raw(head, s.get("en", ""), instr + f'<ol class="{cls}">{"".join(li)}</ol>')


def sec_raw(head_html, en, body, cls=""):
    """Like B.sec, but the Spanish title may carry the set's letter."""
    return (f'<div class="sec exset {cls}"><div class="sh"><span class="es">{head_html}</span>'
            f'<span class="en">{esc(en)}</span></div>{body}</div>')


# ---------------------------------------------------------------- answers
def key_for(ep):
    out = []
    for i, s in enumerate(ep["sets"]):
        letter = LETTERS[i]
        if s["type"] == "write":
            if s.get("key"):
                ans = f'<span class="k model">{md(s["key"])}</span>'
            elif s.get("model"):
                ans = f'<span class="k model"><i>Model answer:</i> {md(s["model"])}</span>'
            else:
                ans = '<span class="k model"><i>Your own answer.</i></span>'
        else:
            parts = []
            for n, it in enumerate(s["items"], 1):
                _, _, a, src = split_item(it, s["type"])
                tag = f' <span class="src">Ep.&#160;{src}</span>' if src else ""
                parts.append(f'<span class="k"><span class="kn">{n}</span>{md(a)}{tag}</span>')
            ans = " ".join(parts)
        out.append(f'<p class="kset"><span class="setl">{letter}</span>{ans}</p>')
    return (f'<div class="keyep"><h3>Episodio {ep["episode"]} · {esc(ep["title"])}</h3>'
            + "".join(out) + '</div>')


# ---------------------------------------------------------------- the book
def cover(eps):
    first, last = eps[0]["episode"], eps[-1]["episode"]
    return f'''
<div class="cover">
  <div class="top"><span>Ejercicios</span><span>Episodios {first}–{last}</span></div>
  <h1>Destinos</h1>
  <div class="sub">The best exercises of every lesson from the Textbook and the Workbook, the ones you can do without the audio. The answers are at the back.</div>
  <div class="map">{B.route_svg("", width=560, big=True)}</div>
  <div class="owner">
    <div><span class="k">Estos ejercicios son de</span><span class="v"></span></div>
    <div><span class="k">Empezado el</span><span class="v"></span></div>
  </div>
</div>'''


HOWTO = [
    ("After the sheet", "Do an episode's exercises after you have studied its sheet in the notebook, not before."),
    ("Book closed", "Answer from memory. Guessing and getting it wrong teaches you more than looking it up."),
    ("Check at the back", "Mark your answers with the key at the back. Write the correct form next to every mistake."),
    ("Redo in two days", "Two days later, redo only the items you got wrong. Then once more a week later."),
    ("Say it out loud", "Read your corrected sentences aloud. Each exercise shows its page in the book, if you want the full context."),
]


def front(eps):
    rows = "".join(f'<li><a href="#ex{int(e["episode"])}"><span class="n">{int(e["episode"])}</span>'
                   f'{esc(e["title"])} <i>{esc(e.get("title_en", ""))}</i></a></li>' for e in eps)
    rows += '<li><a href="#key"><span class="n"></span>Soluciones <i>Answers</i></a></li>'
    how = "".join(f'<li><b>{esc(t)}.</b> {esc(d)}</li>' for t, d in HOWTO)
    return f'''
<div class="intro newpage">
  <div class="headmark" data-l="" data-r=""></div>
  <h2>Índice</h2>
  <ol class="toc">{rows}</ol>
  <div class="howto"><span class="lbl">How to use it</span><ol>{how}</ol></div>
</div>'''


def episode(ep):
    n = int(ep["episode"])
    o = [f'''
<div class="opener exop" id="ex{n}">
  <div class="headmark" data-l="" data-r=""></div>
  <div class="num"><span class="lbl">Episodio</span><span class="n">{n}</span></div>
  <div class="title"><h1>{esc(ep["title"])}</h1><div class="en">{esc(ep.get("title_en", ""))}</div>
  <div class="where">{esc(ep.get("pages", "Notebook: Episodio " + str(n)))}</div></div>
</div>
<div class="headmark" data-l="Destinos · ejercicios" data-r="Episodio {n} · {esc(ep["title"])}"></div>''']
    for i, s in enumerate(ep["sets"]):
        o.append(render_set(LETTERS[i], s))
    return "".join(o)


def build(out=OUT, only=None):
    """The whole book, or with `only` a set of episode numbers: just those."""
    eps = []
    paths = sorted(glob.glob(os.path.join(EXERCISES, "ex*.yaml")))
    if only:
        paths = [p for p in paths
                 if int(re.search(r"ex(\d+)", os.path.basename(p)).group(1)) in only]
    for path in paths:
        with open(path, encoding="utf-8") as f:
            eps.append(yaml.safe_load(f))
    eps.sort(key=lambda e: int(e["episode"]))
    css = ""
    for name in ("destinos.css", "ejercicios.css"):
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            css += f.read()
    key = ('<div class="keypart newpage" id="key"><div class="headmark" data-l="Destinos · ejercicios" '
           'data-r="Soluciones"></div><h2 class="keyh">Soluciones</h2>'
           + "".join(key_for(e) for e in eps) + '</div>')
    body = cover(eps) + front(eps) + "".join(episode(e) for e in eps) + key
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
           f'<title>Destinos · Ejercicios</title><style>{css}</style></head><body>{body}</body></html>')
    HTML(string=doc, base_url=ROOT).write_pdf(out)
    return out


if __name__ == "__main__":
    # build_ejercicios.py [out.pdf]                  the whole book
    # build_ejercicios.py --episodes 3,4 [out.pdf]   just those episodes
    args, only = sys.argv[1:], None
    if args[:1] == ["--episodes"]:
        only = {int(x) for x in args[1].split(",")}
        args = args[2:]
    print(build(args[0] if args else OUT, only))
