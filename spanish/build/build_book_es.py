#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the illustrated Spanish A1-A2 course PDF from the agent source files + assets."""
import re, os, json, html, datetime, sys
import markdown
from weasyprint import HTML

ROOT="/home/user/khalil_nacef_book-/spanish"
SRC=f"{ROOT}/sources_md"; BUILD=f"{ROOT}/build"; PHOTOS=f"{ROOT}/assets/photos"; DIAG=f"{ROOT}/assets/diagrams"
FILES=["a1p1.md","a1p2.md","a2p1.md","a2p2.md"]

_md=markdown.Markdown(extensions=['tables','sane_lists','attr_list'])
_LI=re.compile(r'^\s*([-*+]|\d+[.)])\s+')
def _normalize(t):
    """ensure a blank line before lists and tables (agents omit them)"""
    out=[]
    for l in t.split("\n"):
        prev=out[-1] if out else ""
        is_li=bool(_LI.match(l)); is_tb=l.lstrip().startswith("|")
        if is_li and prev.strip() and not _LI.match(prev) and not prev.lstrip().startswith("|"): out.append("")
        if is_tb and prev.strip() and not prev.lstrip().startswith("|"): out.append("")
        out.append(l)
    return "\n".join(out)
_EMOJI=re.compile('[\U0001F000-\U0001FAFF\U00002600-\U000026FF\U00002B00-\U00002BFF]')
# A gap written as ___ is markdown emphasis: "hacer -> ___, ver -> ___" renders as
# "hacer -> <strong><em>, ver -> </em></strong>" and BOTH blanks disappear. Protect
# them before conversion, then render them as real ruled answer gaps.
_BLANK=re.compile(r'_{3,}')
_B0,_B1='',''
# python-markdown mis-parses bold nested inside italics — "*dice **esto** así*"
# comes out as broken <em> runs with literal asterisks left in the text. It is an
# easy thing to write and it had already slipped into six files, so convert the
# whole pattern to explicit HTML before the converter ever sees it.
_NEST=re.compile(r'(?<![*\w])\*(?!\s)((?:[^*\n]|\*\*[^*\n]+?\*\*)*?\*\*[^*\n]+?\*\*(?:[^*\n]|\*\*[^*\n]+?\*\*)*?)(?<!\s)\*(?!\*)')
def _fix_nested_em(t):
    def rep(m):
        inner=re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', m.group(1))
        return f'<em>{inner}</em>'
    return _NEST.sub(rep, t)

def md(t):
    _md.reset()
    t=_fix_nested_em(t)
    t=_BLANK.sub(lambda m: f'{_B0}{len(m.group(0))}{_B1}', t)
    h=_md.convert(_normalize(_EMOJI.sub('',t).strip()))
    h=re.sub(_B0+r'(\d+)'+_B1,
             lambda m: f'<span class="blank" style="width:{min(int(m.group(1)),14)*2.6:.1f}mm"></span>', h)
    # python-markdown has no strikethrough extension loaded; support ~~x~~ ourselves
    h=re.sub(r'~~(.+?)~~', r'<del>\1</del>', h)
    # WeasyPrint ignores <ol start="N">, which would silently renumber every
    # test back to 1 in each section and break all 20 routing tables.
    h=re.sub(r'<ol start="(\d+)"',
             lambda m: f'<ol style="counter-reset:list-item {int(m.group(1))-1}"', h)
    return h
def md_ol(t):
    """Render markdown but KEEP the author's ordered-list start numbers.
    python-markdown restarts every <ol> at 1, which would renumber the tests
    (Q1-Q30 continuous across sections) and silently break every routing table."""
    starts=[]; prev=False
    for line in _normalize(_EMOJI.sub('',t)).split("\n"):
        m=re.match(r'^\s*(\d+)[.)]\s+', line)
        if m:
            if not prev: starts.append(int(m.group(1)))
            prev=True
        elif line.strip():
            prev=False
    h=md(t); it=iter(starts)
    def rep(_m):
        try: s=next(it)
        except StopIteration: return '<ol>'
        # WeasyPrint ignores the HTML start attribute; the list-item counter works.
        return '<ol>' if s==1 else f'<ol style="counter-reset:list-item {s-1}">'
    return re.sub(r'<ol>', rep, h)

def slug(s):
    s=re.sub(r'<[^>]+>','',s); s=re.sub(r'[^a-zA-Z0-9]+','-',s.lower()).strip('-'); return s or 'x'

TOC=[]  # (level, id, title)
_IDS={}
def hid(title):
    i=slug(title)
    if i in _IDS:
        _IDS[i]+=1; i=f"{i}-{_IDS[i]}"
    else: _IDS[i]=0
    return i
# ---------------- parsing ----------------
THEME=re.compile(r'^##\s+Tema:\s*(.+?)\s*\{(.+?)\}\s*$')
GBLK=re.compile(r'^####\s*G\s*·\s*(.+?)\s*(\{#cat=(.+?)\})?\s*$')
def parse_meta(s):
    return dict(re.findall(r'#(\w+)=([^\s}]+)', s or ""))

def parse_table(lines):
    rows=[]
    for l in lines:
        if l.strip().startswith('|'):
            cells=[c.strip() for c in l.strip().strip('|').split('|')]
            if all(set(c)<=set('-: ') for c in cells): continue
            rows.append(cells)
    return rows  # first row = header

def parse_file(path):
    if not os.path.exists(path): return []
    lines=open(path,encoding="utf-8").read().split("\n")
    idx=[i for i,l in enumerate(lines) if THEME.match(l)]
    out=[]
    for k,si in enumerate(idx):
        ei=idx[k+1] if k+1<len(idx) else len(lines)
        m=THEME.match(lines[si]); name=m.group(1); meta=parse_meta(m.group(2))
        blk=lines[si+1:ei]
        g=v=c=None
        for i,l in enumerate(blk):
            s=l.strip().lower()
            if s.startswith('### gram'): g=i
            elif s.startswith('### vocab'): v=i
            elif s.startswith('### en context') or s=='### en contexto': c=i
        gram=blk[g:v] if g is not None and v is not None else (blk[g:c] if g is not None and c else (blk[g:] if g is not None else []))
        voc=blk[v:c] if v is not None and c is not None else (blk[v:] if v is not None else [])
        ctx=blk[c:] if c is not None else []
        out.append(dict(name=name,meta=meta,gram=gram,voc=voc,ctx=ctx))
    return out

def parse_grammar(gram):
    """Split each G-block into rule / examples / table / ojo so the authoring
    labels ('Rule.', 'Examples.', 'Table.') never reach the printed page."""
    idx=[i for i,l in enumerate(gram) if GBLK.match(l)]
    pts=[]
    for k,si in enumerate(idx):
        ei=idx[k+1] if k+1<len(idx) else len(gram)
        m=GBLK.match(gram[si]); nm=m.group(1); cat=(m.group(3) or 'divers').strip()
        body=[l for l in gram[si+1:ei] if '[NIVEL A2]' not in l]
        txt="\n".join(body).strip()
        ojo=""; main=txt
        mo=re.search(r'\*\*Ojo\.\*\*\s*(.+)$', txt, re.S)
        if mo: ojo=mo.group(1).strip(); main=txt[:mo.start()].strip()
        def grab(label, nxt):
            mm=re.search(r'\*\*'+label+r'\.\*\*[ \t]*(.*?)(?=\n\s*\*\*(?:'+nxt+r')\.\*\*|\Z)', main, re.S)
            return mm.group(1).strip() if mm else ""
        rule=grab('Rule','Examples|Table')
        exs =grab('Examples','Table')
        tbl =grab('Table','')
        # anything that used none of the three labels stays as free prose
        rest=main if not (rule or exs or tbl) else ""
        pts.append(dict(name=nm,cat=cat,rule=rule,exs=exs,tbl=tbl,rest=rest,ojo=ojo))
    return pts

def voc_tables(voc):
    """return dict cat->rows"""
    res={}; cur=None; buf=[]
    def flush():
        if cur and buf:
            rows=parse_table(buf)
            if rows: res[cur]=rows
    for l in voc:
        s=l.strip().lower()
        m=re.match(r'^####\s*(verbos|sustantivos|adjetivos|otras)', s)
        if m:
            flush(); buf=[]
            cur=m.group(1)
        elif l.strip().startswith('|'):
            buf.append(l)
    flush()
    return res

def parse_ctx(ctx):
    """dialogues [{title,lines,tr}], examples [str], truco str"""
    text="\n".join(ctx)
    dialogues=[]
    # '\d*' tolerates 'Diálogo 1 —' / 'Diálogo 2 —' as well as plain 'Diálogo —'
    for m in re.finditer(r'\*\*Di[aá]logo\s*\d*\s*[—–-]\s*(.+?)\*\*\s*(.*?)(?=\n\s*\n|\*\*More|\*\*Truco|\Z)', text, re.S):
        title=m.group(1).strip(); body=m.group(2)
        lines=[]
        for lm in re.finditer(r'^>\s*\*\*(.+?):\*\*\s*(.+)$', body, re.M):
            lines.append((lm.group(1).strip(), lm.group(2).strip()))
        if not lines:
            for lm in re.finditer(r'^>\s*(.+)$', body, re.M):
                lines.append(("", lm.group(1).strip()))
        tr=""
        tm=re.search(r'\*Translation:\*\s*(.+?)(?=\n\s*\n|\*\*|\Z)', text[m.end()-1:], re.S)
        if tm: tr=" ".join(tm.group(1).split())
        dialogues.append(dict(title=title,lines=lines,tr=tr))
    examples=re.findall(r'^\s*[-*]\s+(.+)$', "\n".join(re.findall(r'\*\*More examples:\*\*(.*?)(?=\*\*Truco|\Z)', text, re.S)), re.M)
    tm=re.search(r'\*\*Truco\.?\*\*\s*(.+?)(?=\n\s*\n|\Z)', text, re.S)
    truco=" ".join(tm.group(1).split()) if tm else ""
    return dict(dialogues=dialogues, examples=examples, truco=truco)

# ---------------- rendering ----------------
def h(level,title,cls=""):
    """title is RAW text; escaped once here for display, stored raw for the TOC."""
    i=hid(title); TOC.append((level,i,re.sub(r'<[^>]+>','',title)))
    c=f' class="{cls}"' if cls else ''
    return f'<h{level} id="{i}"{c}>{html.escape(title)}</h{level}>'

# nouns that take 'el' but are grammatically feminine (stressed initial a-/ha-)
FEM_EL={'agua','aula','arte','alma','águila','hambre','área','aula','ala','arma','acta','ave','hacha'}

def ex_cell(c):
    """An 'Ejemplo' cell is 'Spanish sentence. — English gloss.' — set the Spanish
    as the visible line and the gloss underneath it, smaller."""
    m=re.split(r'\s+[—–]\s+', c.strip(), maxsplit=1)
    es=html.escape(m[0].strip())
    en=html.escape(m[1].strip()) if len(m)>1 else ""
    return f'<td class="ex"><span class="es">{es}</span>'+(f'<span class="en">{en}</span>' if en else '')+'</td>'

def _is_ex(hd,j):
    return j<len(hd) and hd[j].strip().lower().startswith('ejemplo')

def gender_table(rows):
    hd=rows[0]; body=rows[1:]
    out=['<table class="voc"><thead><tr>'+"".join(f'<th>{html.escape(c)}</th>' for c in hd)+'</tr></thead><tbody>']
    for r in body:
        cells=[]
        for j,c in enumerate(r):
            if _is_ex(hd,j):
                cells.append(ex_cell(c)); continue
            if j==0:
                mt=re.match(r'^(el|la|los|las)\s+(.+)$', c.strip(), re.I)
                if mt:
                    art=mt.group(1).lower(); rest=mt.group(2)
                    g='f' if art in ('la','las') else 'm'
                    head=re.sub(r'\s*\(.*?\)','',rest).strip().split('/')[0].strip().lower()
                    if art in ('el','los') and head in FEM_EL: g='f'
                    cells.append(f'<td><span class="gen {g}">{art}</span>{html.escape(rest)}</td>')
                else: cells.append(f'<td>{html.escape(c)}</td>')
            else: cells.append(f'<td>{html.escape(c)}</td>')
        out.append('<tr>'+"".join(cells)+'</tr>')
    out.append('</tbody></table>'); return "".join(out)

def plain_table(rows, cls="voc"):
    if not rows: return ""
    hd=rows[0]
    o=[f'<table class="{cls}"><thead><tr>'+"".join(f'<th>{html.escape(c)}</th>' for c in hd)+'</tr></thead><tbody>']
    for r in rows[1:]:
        o.append('<tr>'+"".join(ex_cell(c) if _is_ex(hd,j) else f'<td>{html.escape(c)}</td>'
                                for j,c in enumerate(r))+'</tr>')
    o.append('</tbody></table>'); return "".join(o)

DIAG_MAP={'casa-vivienda':'casa','cuerpo-salud':'cuerpo','familia-caracter':'familia',
          'rutina-hora':'rutina','comida':'mesa','comida-recetas':'mesa',
          'compras-ropa':'ropa','ciudad-barrio':'ciudad','geografia-clima':'clima',
          'ocio-viajes':'viajes'}
# Diagrams for the four grammar points learners reliably fail. A conjugation table
# does not fix a conceptual gap — English has no preterite/imperfect split, so a
# picture is the only thing that gives the learner a reference point.
GRAM_DIAG={'Indefinido vs imperfecto':'pasados',
           'Por, para and porque':'porpara',
           'Direct object pronouns (lo/la/los/las)':'pronombres',
           'Ser vs Estar':'serestar',
           'The verb gustar':'gustar'}
_DIAG_DONE=set()
def diagram(suj):
    d=DIAG_MAP.get(suj)
    if d and os.path.exists(f"{DIAG}/{d}.svg"):
        return f'<div class="diagram">{open(f"{DIAG}/{d}.svg").read()}</div>'
    return ""

VOC_TITLE={'verbos':'Verbs','sustantivos':'Nouns','adjetivos':'Adjectives & adverbs','otras':'Other words'}
def md_inline(t):
    x=md(t); x=re.sub(r'^<p>|</p>$','',x.strip()); return x

def render_ctx(ctx):
    o=[]
    for d in ctx['dialogues']:
        o.append('<div class="box dlg"><span class="h">En contexto — '+html.escape(d['title'])+'</span>')
        for who,tx in d['lines']:
            if who: o.append(f'<div class="line"><span class="who">{html.escape(who)}:</span> {html.escape(tx)}</div>')
            else: o.append(f'<div class="line">{html.escape(tx)}</div>')
        if d['tr']: o.append(f'<div class="tr">{html.escape(d["tr"])}</div>')
        o.append('</div>')
    if ctx['examples']:
        o.append('<p class="exlead"><b>More examples</b></p><ul class="g-ex">'+
                 "".join(f'<li>{md_inline(e)}</li>' for e in ctx['examples'])+'</ul>')
    if ctx['truco']:
        o.append('<div class="box tip"><span class="h">Truco</span>'+md_inline(ctx['truco'])+'</div>')
    return "".join(o)

def render_grammar_point(p, gid):
    o=[f'<div class="gpoint"><h4 id="{gid}">{html.escape(p["name"])}</h4>']
    d=GRAM_DIAG.get(p['name'])
    if d and d not in _DIAG_DONE and os.path.exists(f"{DIAG}/{d}.svg"):
        _DIAG_DONE.add(d)   # only on the first unit that teaches the point
        o.append(f'<div class="diagram gram">{open(f"{DIAG}/{d}.svg").read()}</div>')
    if p['rule']: o.append('<div class="g-rule">'+md(p['rule'])+'</div>')
    if p['exs']:  o.append('<div class="g-exwrap"><span class="lbl">Examples</span>'+md(p['exs'])+'</div>')
    if p['tbl']:  o.append(md(p['tbl']))
    if p['rest']: o.append(md(p['rest']))
    if p['ojo']:  o.append('<div class="box ojo"><span class="h">&iexcl;Ojo!</span>'+md_inline(p['ojo'])+'</div>')
    o.append('</div>')
    return "".join(o)

# ---------------- exercises / repaso / tests ----------------
def parse_exercises(path):
    """{(nivel,unidad): (practica_md, answers_md)}"""
    if not os.path.exists(path): return {}
    text=open(path,encoding="utf-8").read(); out={}
    for m in re.finditer(r'^##\s+Unidad\s+(\d+)\b.*?\{(.+?)\}\s*$(.*?)(?=^##\s+Unidad|\Z)', text, re.S|re.M):
        meta=parse_meta(m.group(2)); nivel=meta.get('nivel','A1'); uni=meta.get('unidad', m.group(1))
        body=m.group(3)
        am=re.search(r'\*\*Answers\.?\*\*', body)
        practica, answers = (body[:am.start()], body[am.end():]) if am else (body, "")
        practica=re.sub(r'^###\s*Práctica\s*$','',practica,flags=re.M)
        out[(nivel,str(int(uni)))]=(practica.strip(), answers.strip())
    return out

def parse_repaso(path):
    if not os.path.exists(path): return {}
    text=open(path,encoding="utf-8").read(); out={}
    for m in re.finditer(r'^##\s+Repaso\b.*?\{#after=([A-Za-z0-9-]+)\}\s*$(.*?)(?=^##\s+Repaso|\Z)', text, re.S|re.M):
        key=m.group(1).strip(); body=m.group(2)
        am=re.search(r'\*\*Answers\.?\*\*', body)
        content, answers = (body[:am.start()], body[am.end():]) if am else (body, "")
        out[key]=(content.strip(), answers.strip())
    return out

def parse_tests(path):
    """{(nivel,unidad): dict(paper, points, answers, model, checks, routing)}"""
    if not os.path.exists(path): return {}
    text=open(path,encoding="utf-8").read(); out={}
    for m in re.finditer(r'^##\s+Test\s*[—–-]\s*Unidad\s+(\d+).*?\{(.+?)\}\s*$(.*?)(?=^##\s+Test\b|\Z)', text, re.S|re.M):
        meta=parse_meta(m.group(2)); nivel=meta.get('nivel','A1'); uni=meta.get('unidad', m.group(1))
        body=m.group(3)
        def cut(label, body):
            mm=re.search(r'\*\*'+label+r'\.?\*\*', body)
            return (body[:mm.start()], body[mm.end():]) if mm else (body, None)
        paper, rest = cut('Points', body)
        points, rest2 = ("", rest)
        if rest is not None:
            points, rest2 = cut('Answers', rest)
        answers=model=checks=routing=""
        if rest2 is not None:
            answers, r3 = cut('Model', rest2)
            if r3 is not None:
                model, r4 = cut('Checks', r3)
                if r4 is not None:
                    checks, r5 = cut('Routing', r4)
                    routing = r5 or ""
                else: checks=""
            else: model=""
        out[(nivel,str(int(uni)))]=dict(paper=paper.strip(), points=(points or "").strip(),
                                        answers=(answers or "").strip(), model=(model or "").strip(),
                                        checks=(checks or "").strip(), routing=(routing or "").strip())
    return out

def md_file(name):
    p=f"{BUILD}/{name}"
    return open(p,encoding="utf-8").read() if os.path.exists(p) else ""

def split_h1(text):
    """yield (title, body) for each '# ' chunk"""
    for chunk in re.split(r'(?=^# )', text, flags=re.M):
        chunk=chunk.strip()
        if not chunk: continue
        mm=re.match(r'^#\s+(.+)', chunk)
        if mm: yield mm.group(1), chunk[mm.end():]

def bonus_section(title_key):
    for t,b in split_h1(md_file("bonus_es.md")):
        if title_key.lower() in t.lower(): return t,b
    return None,None

def parse_keyed(name, pat=r'^##\s+(.+?)\s*\{#u=([A-Za-z0-9-]+)\}\s*$'):
    """generic '## Title {#u=A1-7}' section file -> {key: (title, body)}"""
    text=md_file(name); out={}
    if not text: return out
    for m in re.finditer(pat+r'(.*?)(?=^##\s|\Z)', text, re.S|re.M):
        out[m.group(2).strip()]=(m.group(1).strip(), m.group(3).strip())
    return out

# ---------------- assemble ----------------
def build():
    themes=[]
    for f in FILES: themes+=parse_file(f"{SRC}/{f}")
    umeta=json.load(open(f"{BUILD}/units.json",encoding="utf-8"))
    foto={}
    for lv in ("A1","A2"):
        for u in umeta[lv]: foto[(lv,str(u['unidad']))]=u
    exdict={}
    for f in ["ex_a1p1.md","ex_a1p2.md","ex_a2p1.md","ex_a2p2.md"]:
        exdict.update(parse_exercises(f"{SRC}/{f}"))
    tests={}
    for f in ["test_a1p1.md","test_a1p2.md","test_a2p1.md","test_a2p2.md"]:
        tests.update(parse_tests(f"{SRC}/{f}"))
    repaso=parse_repaso(f"{SRC}/repaso_es.md")
    cando=parse_keyed("cando_es.md")
    cultura=parse_keyed("cultura_es.md")
    variantes=parse_keyed("variantes_es.md")
    relampago=parse_keyed("relampago_es.md")
    frances=parse_keyed("frances_es.md")
    suena=parse_keyed("suena_es.md")
    parts=[]; answer_key=[]; test_key=[]; relamp_key=[]; unit_anchor={}

    # -------- front matter --------
    for name in ("welcome_es.md",):
        for t,b in split_h1(md_file(name)):
            parts.append(h(1,t)); parts.append(md(b))
    for name in ("grammar_words_es.md","aprender_es.md","studyplan_es.md","variedades_es.md","frances_intro_es.md"):
        for t,b in split_h1(md_file(name)):
            parts.append(h(1,t)); parts.append(md(b))
    pt,pbody=bonus_section("Pronunciation")
    if pt: parts.append(h(1,pt)); parts.append(md(pbody))
    for t,b in split_h1(md_file("leer_voz_alta_es.md")):
        parts.append(h(1,t)); parts.append(md(b))
    for t,b in split_h1(md_file("cognates_es.md")):
        parts.append(h(1,t)); parts.append(md(b))

    # -------- the lessons --------
    parts.append(h(1,"The Lessons · Las lecciones"))
    parts.append('<p class="lead">Twenty units in learning order — A1 first, then A2. Work through them one at a '
                 'time. Each unit runs <b>Vocabulary → Grammar → Conversations → Practice → Test</b>, and opens by '
                 'telling you exactly what you will be able to do by the end of it. Answers to every exercise are in '
                 'the <b>Answer Key</b>; the tests are marked from the <b>Test Answer Key</b>, which also tells you '
                 'which page to go back to for anything you missed.</p>')
    for t in themes:
        mta=t['meta']; nivel=mta.get('nivel','A1'); uno=mta.get('unidad','0'); suj=mta.get('sujeto','')
        key=f"{nivel}-{int(uno)}"
        u=foto.get((nivel,uno),{})
        fpath=f"{PHOTOS}/{nivel.lower()}_u{int(uno):02d}.jpg"
        tid=slug(f"lesson-{t['name']}-{nivel}-{uno}"); TOC.append((2,tid,f"{t['name']} ({nivel})"))
        unit_anchor[(nivel,str(int(uno)))]=tid
        sub="You will learn: "+html.escape(u.get('scope',''))
        bmk=f"{nivel} Unidad {uno} — {t['name']}"
        cap=(f'<div class="cap"><span class="badge">UNIDAD {uno} · {nivel}</span>'
             f'<div class="utitle">{html.escape(t["name"])}</div>'
             f'<div class="usub">{sub}</div></div>')
        if os.path.exists(fpath):
            parts.append(f'<div class="opener photo" id="{tid}" data-title="{html.escape(bmk)}" '
                         f'style="background-image:url(\'file://{fpath}\')">'
                         f'<div class="veil"></div>{cap}</div>')
        else:
            parts.append(f'<div class="opener nophoto" id="{tid}" data-title="{html.escape(bmk)}">{cap}</div>')

        # 0) can-do promise
        if key in cando:
            _,body=cando[key]
            parts.append('<div class="cando"><span class="h">By the end of this unit you can</span>'+md(body)+'</div>')

        # 1) Vocabulary
        parts.append('<div class="scope voc"><h3 class="sec sec-voc"><span class="tag">Vocabulary</span></h3>')
        parts.append(diagram(suj))
        vt=voc_tables(t['voc'])
        for k in ('verbos','sustantivos','adjetivos','otras'):
            if k in vt:
                parts.append(f'<h4 class="vh">{VOC_TITLE[k]}</h4>')
                parts.append(gender_table(vt[k]) if k=='sustantivos' else plain_table(vt[k]))
        if key in variantes:
            _,body=variantes[key]
            parts.append('<div class="box var"><span class="h">En España / En América</span>'+md(body)+'</div>')
        parts.append('</div>')

        # 2) Grammar
        gp=parse_grammar(t['gram'])
        if gp:
            parts.append('<div class="scope gram"><h3 class="sec sec-gram"><span class="tag">Grammar</span></h3>')
            for p in gp:
                gid=hid(f"g-{nivel}-{uno}-{p['name']}")
                TOC.append((3,gid,p['name']))
                parts.append(render_grammar_point(p,gid))
            if key in frances:
                ft,body=frances[key]
                parts.append('<div class="box fr"><span class="h">Si tu parles français — '
                             +html.escape(ft)+'</span>'+md(body)+'</div>')
            parts.append('</div>')

        # 3) Conversations
        ctx=parse_ctx(t['ctx'])
        if ctx['dialogues'] or ctx['examples'] or ctx['truco'] or key in cultura:
            parts.append('<div class="scope conv"><h3 class="sec sec-conv"><span class="tag">Conversations</span></h3>')
            parts.append(render_ctx(ctx))
            if key in cultura:
                ct,body=cultura[key]
                parts.append('<div class="box cult"><span class="h">Cultura — '+html.escape(ct)+'</span>'+md(body)+'</div>')
            if key in suena:
                st,body=suena[key]
                parts.append('<div class="box suena"><span class="h">Suena así — '+html.escape(st)+'</span>'+md(body)+'</div>')
            parts.append('</div>')

        # 4) Practice
        ex=exdict.get((nivel,str(int(uno))))
        if ex and ex[0]:
            parts.append('<div class="scope prac"><h3 class="sec sec-prac"><span class="tag">Practice</span></h3>')
            if key in relampago:
                _,body=relampago[key]
                # optional cumulative recall grid, appended after the answers
                cum=cumans=""
                cm=re.search(r'\*\*Cumulative\.?\*\*(.*?)(?=\*\*Cumulative answers|\Z)', body, re.S)
                ca=re.search(r'\*\*Cumulative answers\.?\*\*(.*)$', body, re.S)
                if cm: cum=cm.group(1).strip()
                if ca: cumans=ca.group(1).strip()
                if cm: body=body[:cm.start()]
                am=re.search(r'\*\*Answers\.?\*\*', body)
                items, rans = (body[:am.start()], body[am.end():]) if am else (body, "")
                blk=('<div class="relampago"><span class="h">Repaso relámpago · 2 minutes · don\'t look back</span>'
                     +md_ol(items))
                if cum:
                    blk+=('<div class="cumul"><span class="h2">Y estas palabras de antes — write the Spanish</span>'
                          +md_inline(cum)+'</div>')
                tail=" · ".join(x for x in (rans.strip(), cumans.strip()) if x)
                if tail:
                    blk+=('<p class="ansref"><small>Answers at the back, under '
                          '<b>Repaso relámpago — Answers</b>. Don\'t look until you have tried all of them.</small></p>')
                    relamp_key.append((f"{nivel} Unidad {uno}", tail))
                parts.append(blk+'</div>')
            parts.append('<div class="practice">'+md_ol(ex[0])+'</div>')
            parts.append('<p class="ansref"><small>Check your answers in the <b>Answer Key</b> at the back of the book.</small></p>')
            parts.append('</div>')
            if ex[1]:
                answer_key.append((f"Unidad {uno} — {t['name']} ({nivel})", ex[1]))

        # 5) Test
        ts=tests.get((nivel,str(int(uno))))
        if ts and ts['paper']:
            tsid=slug(f"test-{nivel}-{uno}"); TOC.append((2,tsid,f"Test — {nivel} Unit {uno}"))
            parts.append(f'<h2 id="{tsid}" class="testhead">Test · Unidad {uno} — {html.escape(t["name"])} <span class="lv">{nivel}</span></h2>')
            # The final writing task is numbered but has no printed content
            # ("30." / "38. *(Your text.)*"). Lift it out of the list and give
            # the learner real ruled space — the commonest complaint about
            # self-study workbooks is having nowhere to write the answer.
            paper=ts['paper']; wq=None
            mw=None
            for mm in re.finditer(r'(?m)^(\d+)\.[ \t]*(?:\*\([^)]*\)\*)?[ \t]*$', paper): mw=mm
            if mw:
                wq=mw.group(1); paper=paper[:mw.start()]+paper[mw.end():]
            parts.append('<div class="test">'+md_ol(paper))
            if wq:
                n=12 if nivel=='A2' else 8
                parts.append(f'<div class="writebox"><span class="wq">{wq}.</span>'
                             +'<div class="wline"></div>'*n+'</div>')
            if ts['points']: parts.append('<p class="pointmap">'+md_inline(ts['points'])+'</p>')
            parts.append('<p class="ansref"><small>Mark yourself from the <b>Test Answer Key</b> at the back — '
                         'only after you have answered everything.</small></p></div>')
            test_key.append((f"Test — Unidad {uno}: {t['name']} ({nivel})", ts))

        # Repaso checkpoint
        if key in repaso:
            rc,ra=repaso[key]
            rid=slug(f"repaso-{key}"); TOC.append((2,rid,f"Repaso — after {nivel} unit {uno}"))
            parts.append(f'<div class="repaso" id="{rid}"><h2 class="repasohead">Repaso · Review after {nivel} Unit {uno}</h2>')
            parts.append(md_ol(rc)); parts.append('</div>')
            if ra: answer_key.append((f"Repaso — after {nivel} unit {uno}", ra))

    # ================= REFERENCE =================
    parts.append(h(1,"Reference"))
    parts.append('<p class="lead">Use this section to look things up any time: full grammar tables, a glossary of '
                 'every verb and adjective, useful phrases, an index, and the answer keys.</p>')
    ref=md_file("annexe_reference_es.md")
    ref=re.sub(r'^#\s+Appendix.*$','',ref,count=1,flags=re.M)
    parts.append(h(1,"Grammar Reference")); parts.append(md(ref))

    et,ebody=bonus_section("Useful Expressions")
    if et: parts.append(h(1,et)); parts.append(md(ebody))

    for name in ("nextsteps_es.md",):
        for t,b in split_h1(md_file(name)):
            parts.append(h(1,t)); parts.append(md(b))

    # -------- glossaries --------
    allv={}; alladj={}
    for t in themes:
        vt=voc_tables(t['voc'])
        for r in vt.get('verbos',[])[1:]:
            if len(r)>=3 and r[0].strip() and r[0] not in allv: allv[r[0]]=(r[1],r[2])
        for r in vt.get('adjetivos',[])[1:]:
            if len(r)>=3 and r[0].strip() and r[0] not in alladj: alladj[r[0]]=(r[1],r[2])
    vkey=lambda x: re.sub(r'[^a-záéíóúñü]','',x[0].lower())
    parts.append(h(1,"Verb & Adjective Glossary (A1+A2)"))
    parts.append(f'<p class="lead">Every verb and adjective in the book, gathered in one place for fast look-up — '
                 f'{len(allv)} verbs and {len(alladj)} adjectives &amp; adverbs.</p>')
    parts.append('<h2>All verbs</h2>')
    parts.append(plain_table([["Verb (infinitive)","Notes (irregularity / regime)","English"]]+
                             [[k,v[0],v[1]] for k,v in sorted(allv.items(), key=vkey)]))
    parts.append('<h2>All adjectives &amp; adverbs</h2>')
    parts.append(plain_table([["Word","Notes","English"]]+
                             [[k,v[0],v[1]] for k,v in sorted(alladj.items(), key=vkey)]))

    # -------- alphabetical index --------
    words={}
    for t in themes:
        vt=voc_tables(t['voc']); nivel=t['meta'].get('nivel','A1'); uno=t['meta'].get('unidad','')
        for k,rows in vt.items():
            for r in rows[1:]:
                w=r[0].strip()
                if k=='sustantivos':
                    # strip a leading article, and any further ' / la x' alternate form
                    w=re.sub(r'^\s*(el|la|los|las)\s*/\s*(el|la|los|las)\s+','',w,flags=re.I)
                    w=re.sub(r'^\s*(el|la|los|las)\s+','',w,flags=re.I)
                    w=re.sub(r'\s*/\s*(el|la|los|las)\s+',' / ',w,flags=re.I)
                w=re.sub(r'\s*\(.+?\)','',w).strip()
                if w and w[0].isalpha():
                    e=words.setdefault(w.lower(), [w, []])
                    loc=(nivel,str(int(uno)))
                    if loc not in e[1]: e[1].append(loc)
    parts.append(h(1,"Alphabetical Index"))
    parts.append('<p class="lead">Every headword, with the level·unit where it appears.</p>')
    letters={}
    for kw,(w,locs) in words.items():
        letters.setdefault(kw[0].upper(),[]).append((w,locs))
    ih=['<div class="indexgrid">']
    for L in sorted(letters):
        ih.append(f'<div class="idx-letter">{L}</div>')
        for w,locs in sorted(letters[L], key=lambda x:x[0].lower()):
            refs=[]
            for lv,u in locs:
                a=unit_anchor.get((lv,u))
                refs.append(f'<a class="pref" href="#{a}">{lv[-1]}·{u}</a>' if a else f'{lv[-1]}·{u}')
            ih.append(f'<div class="ie">{html.escape(w)} <small>{" ".join(refs)}</small></div>')
    ih.append('</div>')
    parts.append("".join(ih))

    # -------- answer key --------
    parts.append(h(1,"Answer Key · Soluciones"))
    parts.append('<p class="lead">Answers to every Practice exercise and every Repaso, unit by unit. Check your work '
                 'here and go back over anything you missed.</p>')
    parts.append('<div class="answerkey">')
    for title,ans in answer_key:
        parts.append(f'<h3>{html.escape(title)}</h3>'); parts.append(md(ans))
    parts.append('</div>')

    if relamp_key:
        parts.append(h(1,"Repaso relámpago — Answers"))
        parts.append('<p class="lead">Answers to the two-minute recall strips. They live here, at the back, '
                     'on purpose: a strip whose answers sat on the same page would not be a recall exercise '
                     'at all — you would read them before you had tried to remember anything.</p>')
        parts.append('<div class="answerkey">')
        for title,ans in relamp_key:
            parts.append(f'<h3>{html.escape(title)}</h3>'); parts.append(md_inline(ans))
        parts.append('</div>')

    # -------- test answer key --------
    if test_key:
        parts.append(h(1,"Test Answer Key · Soluciones de los tests"))
        parts.append(md(md_file("marking_es.md")))
        parts.append('<div class="answerkey testkey">')
        for title,ts in test_key:
            parts.append(f'<h3>{html.escape(title)}</h3>')
            if ts['answers']: parts.append(md_ol(ts['answers']))
            if ts['model']:
                parts.append('<div class="box tip"><span class="h">Model answer</span>'+md(ts['model'])+'</div>')
            if ts['checks']:
                parts.append('<div class="checks"><span class="h">Give yourself 1 point for each you can honestly tick</span>'+md(ts['checks'])+'</div>')
            if ts['routing']:
                parts.append('<div class="routing"><span class="h">Where to go back to</span>'+md(ts['routing'])+'</div>')
        parts.append('</div>')

    # -------- photo credits --------
    cred=[]
    cf=f"{PHOTOS}/credits.json"
    if os.path.exists(cf):
        seen={}
        for c in json.load(open(cf,encoding="utf-8")): seen[c.get('file')]=c
        for c in sorted(seen.values(), key=lambda x:x.get('file','')):
            cred.append(f"<div>{html.escape(c.get('title','') or c['file'])} — {html.escape(c.get('license','') or '')} — {html.escape((c.get('creator') or '')[:40])}</div>")
    parts.append(h(1,"Photo Credits"))
    parts.append('<p class="lead">All photos are openly licensed (CC0 / Public Domain / CC-BY / CC-BY-SA) via Openverse '
                 '&amp; Wikimedia Commons. Diagrams, layout and all written content are original.</p>')
    parts.append('<div class="credits">'+"".join(cred)+'</div>')

    # -------- TOC --------
    toc=['<div class="toc-title">Contents</div><ul class="toc">']
    for lvl,i,title in TOC:
        if lvl<=2:
            toc.append(f'<li class="lvl{lvl}"><a href="#{i}">{html.escape(title)}</a></li>')
    toc.append('</ul>')

    # -------- cover --------
    cov=f"{PHOTOS}/_cover.jpg"
    covstyle=(f"background-image:linear-gradient(rgba(150,25,20,.35),rgba(120,20,15,.82)),url('file://{cov}')"
              if os.path.exists(cov) else "")
    cover=(f'<div class="cover" style="{covstyle}">'
           f'<div class="kick">Learn Spanish from zero · A1 → A2</div>'
           f'<h1>Spanish for Beginners<br>A Complete Course</h1>'
           f'<div class="rule"></div>'
           f'<div class="sub">Lessons, real photos, exercises &amp; a test in every unit — no prior Spanish needed<br>'
           f'based on <em>Aula Internacional 1 &amp; 2</em></div>'
           f'<div class="meta"><div class="author">Aziz Dardouri</div>'
           f'<div class="badge">Beginner\'s course · {datetime.date.today().strftime("%d/%m/%Y")}</div></div></div>')

    sheet=os.environ.get("ES_STYLE","style_es.css")
    doc=(f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
         f'<link rel="stylesheet" href="file://{BUILD}/{sheet}"></head><body>'
         f'{cover}{"".join(toc)}{"".join(parts)}</body></html>')
    open(f"{BUILD}/_book.html","w",encoding="utf-8").write(doc)
    out=sys.argv[1] if len(sys.argv)>1 else f"{ROOT}/Espanol_A1-A2_Curso_Completo.pdf"
    html_doc=HTML(string=doc, base_url=BUILD)
    # PDF/UA: tagged structure, document language and an outline, so the file is
    # navigable and readable by assistive technology rather than a flat page image.
    try:
        html_doc.write_pdf(out, pdf_variant="pdf/ua-1")
    except Exception as e:
        print(f"  (pdf/ua-1 unavailable: {e}; writing a plain PDF)")
        html_doc.write_pdf(out)
    print(f"PDF -> {out} ({os.path.getsize(out)//1024} KB) | lessons={len(themes)} "
          f"exercises={len(answer_key)} tests={len(test_key)} indexwords={len(words)} "
          f"cando={len(cando)} suena={len(suena)} cultura={len(cultura)} variantes={len(variantes)} relampago={len(relampago)}")

if __name__=="__main__":
    build()
