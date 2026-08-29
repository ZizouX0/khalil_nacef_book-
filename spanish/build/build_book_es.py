#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the illustrated Spanish A1-A2 book PDF from the 4 agent files + assets."""
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
def md(t):
    _md.reset(); return _md.convert(_normalize(t.strip()))
def slug(s):
    s=re.sub(r'<[^>]+>','',s); s=re.sub(r'[^a-zA-Z0-9]+','-',s.lower()).strip('-'); return s or 'x'

TOC=[]  # (level, id, title)
def hid(title):
    i=slug(title); return i
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
        # subsections
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
    idx=[i for i,l in enumerate(gram) if GBLK.match(l)]
    pts=[]
    for k,si in enumerate(idx):
        ei=idx[k+1] if k+1<len(idx) else len(gram)
        m=GBLK.match(gram[si]); nm=m.group(1); cat=(m.group(3) or 'divers').strip()
        body=gram[si+1:ei]
        a2=any('[NIVEL A2]' in l for l in body[:3])
        body=[l for l in body if '[NIVEL A2]' not in l]
        txt="\n".join(body).strip()
        # split Ojo
        ojo=""; main=txt
        mo=re.search(r'\*\*Ojo\.\*\*\s*(.+)$', txt, re.S)
        if mo: ojo=mo.group(1).strip(); main=txt[:mo.start()].strip()
        pts.append(dict(name=nm,cat=cat,a2=a2,main=main,ojo=ojo,score=len(txt)))
    return pts

def voc_tables(voc):
    """return dict cat->(headers,rows)"""
    res={}; cur=None; buf=[]
    def flush():
        if cur and buf:
            rows=parse_table(buf);
            if rows: res[cur]=rows
    for l in voc:
        s=l.strip().lower()
        m=re.match(r'^####\s*(verbos|sustantivos|adjetivos|otras)', s)
        if m:
            flush(); buf=[]
            cur={'verbos':'verbos','sustantivos':'sustantivos','adjetivos':'adjetivos','otras':'otras'}[m.group(1)]
        elif l.strip().startswith('|'):
            buf.append(l)
    flush()
    return res

def parse_ctx(ctx):
    """dialogues [{title,lines:[(who,text)],tr}], examples [str], truco str"""
    text="\n".join(ctx)
    dialogues=[]
    for m in re.finditer(r'\*\*Di[aá]logo\s*[—–-]\s*(.+?)\*\*\s*(.*?)(?=\n\s*\n|\*\*More|\*\*Truco|\Z)', text, re.S):
        title=m.group(1).strip(); body=m.group(2)
        lines=[]
        for lm in re.finditer(r'^>\s*\*\*(.+?):\*\*\s*(.+)$', body, re.M):
            lines.append((lm.group(1).strip(), lm.group(2).strip()))
        if not lines:
            for lm in re.finditer(r'^>\s*(.+)$', body, re.M):
                lines.append(("", lm.group(1).strip()))
        # translation just after
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

def gender_table(rows):
    """render sustantivos table with el/la pills"""
    hd=rows[0]; body=rows[1:]
    out=['<table><thead><tr>'+"".join(f'<th>{html.escape(c)}</th>' for c in hd)+'</tr></thead><tbody>']
    for r in body:
        cells=[]
        for j,c in enumerate(r):
            if j==0:
                mt=re.match(r'^(el|la|los|las)\s+(.+)$', c.strip(), re.I)
                if mt:
                    art=mt.group(1).lower(); g='f' if art in ('la','las') else 'm'
                    cells.append(f'<td><span class="gen {g}">{art}</span>{html.escape(mt.group(2))}</td>')
                else: cells.append(f'<td>{html.escape(c)}</td>')
            else: cells.append(f'<td>{html.escape(c)}</td>')
        out.append('<tr>'+"".join(cells)+'</tr>')
    out.append('</tbody></table>'); return "".join(out)

def plain_table(rows):
    if not rows: return ""
    hd=rows[0]
    o=['<table><thead><tr>'+"".join(f'<th>{html.escape(c)}</th>' for c in hd)+'</tr></thead><tbody>']
    for r in rows[1:]:
        o.append('<tr>'+"".join(f'<td>{html.escape(c)}</td>' for c in r)+'</tr>')
    o.append('</tbody></table>'); return "".join(o)

DIAG_MAP={'casa-vivienda':'casa','cuerpo-salud':'cuerpo','familia-caracter':'familia',
          'rutina-hora':'hora','comida':'mesa','comida-recetas':'mesa'}
def diagram(suj):
    d=DIAG_MAP.get(suj)
    if d and os.path.exists(f"{DIAG}/{d}.svg"):
        return f'<div class="diagram">{open(f"{DIAG}/{d}.svg").read()}</div>'
    return ""

VOC_TITLE={'verbos':'Verbs','sustantivos':'Nouns','adjetivos':'Adjectives & adverbs','otras':'Other words'}
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
        o.append('<p><b>More examples:</b></p><ul>'+"".join(f'<li>{md_inline(e)}</li>' for e in ctx['examples'])+'</ul>')
    if ctx['truco']:
        o.append('<div class="box tip"><span class="h">Truco</span>'+md_inline(ctx['truco'])+'</div>')
    return "".join(o)
def md_inline(t):
    h=md(t); h=re.sub(r'^<p>|</p>$','',h.strip()); return h

# ---------------- assemble ----------------
def build():
    themes=[]
    for f in FILES: themes+=parse_file(f"{SRC}/{f}")
    umeta=json.load(open("/tmp/es/units.json",encoding="utf-8"))
    # index of foto by (nivel,unidad)
    foto={}
    for lv in ("A1","A2"):
        for u in umeta[lv]: foto[(lv,str(u['unidad']))]=u
    parts=[]

    # -------- PART 1 : grammar by topic --------
    CATORD=['genero-articulos','pronombres','ser-estar-hay','presente','perifrasis','pasado',
            'imperativo-condicional-gerundio','gustar-similares','comparativos-cuantificadores',
            'preposiciones','interrogativos-conectores','numeros-tiempo','divers']
    CATTL={'genero-articulos':'1 · Gender, articles & nouns','pronombres':'2 · Pronouns',
      'ser-estar-hay':'3 · Ser, estar & hay','presente':'4 · The present tense',
      'perifrasis':'5 · Verb + infinitive (periphrases)','pasado':'6 · The past tenses',
      'imperativo-condicional-gerundio':'7 · Imperative, conditional & gerund','gustar-similares':'8 · Gustar-type verbs',
      'comparativos-cuantificadores':'9 · Comparatives & quantifiers','preposiciones':'10 · Prepositions',
      'interrogativos-conectores':'11 · Questions & connectors','numeros-tiempo':'12 · Numbers, time & dates','divers':'13 · Other points'}
    gindex={}
    for t in themes:
        for p in parse_grammar(t['gram']):
            key=re.sub(r'[^a-z ]','',p['name'].lower()).strip()
            if key not in gindex or p['score']>gindex[key]['score']: gindex[key]=p
    bycat={}
    for p in gindex.values(): bycat.setdefault(p['cat'] if p['cat'] in CATTL else 'divers',[]).append(p)
    parts.append(h(1,"Part 1 — Grammar","nobreak" if False else ""))
    parts.append('<p class="lead">All the A1–A2 grammar, grouped by topic. Each point: a plain-English rule, Spanish examples with translations, a complete table, and the key pitfall (¡Ojo!).</p>')
    for cat in CATORD:
        ps=bycat.get(cat)
        if not ps: continue
        ps.sort(key=lambda x:(0 if not x['a2'] else 1, -x['score']))
        parts.append(h(2,CATTL[cat]))
        for p in ps:
            badge=' <span style="font-size:8pt;background:#e9f6ee;color:#2e9e5b;border:1px solid #b6e0c4;border-radius:8px;padding:1px 6px">A2</span>' if p['a2'] else ''
            parts.append(f'<h3 id="{slug(p["name"])}">{html.escape(p["name"])}{badge}</h3>')
            parts.append(md(p['main']))
            if p['ojo']:
                parts.append('<div class="box ojo"><span class="h">¡Ojo!</span>'+md_inline(p['ojo'])+'</div>')

    # -------- PART 2 : vocab by theme --------
    parts.append(h(1,"Part 2 — Vocabulary by theme"))
    parts.append('<p class="lead">Each unit\'s vocabulary — grouped by type, colour-coded by gender (<span class="gen m">el</span> masculine / <span class="gen f">la</span> feminine) — then brought to life with real photos, diagrams and mini-dialogues.</p>')
    for t in themes:
        mta=t['meta']; nivel=mta.get('nivel','A1'); uno=mta.get('unidad','0'); suj=mta.get('sujeto','')
        u=foto.get((nivel,uno),{})
        fpath=f"{PHOTOS}/{nivel.lower()}_u{int(uno):02d}.jpg"
        tid=slug(f"{t['name']}-{nivel}-{uno}"); TOC.append((2,tid,f"{t['name']} ({nivel})"))
        sub=html.escape(u.get('scope',''))
        if os.path.exists(fpath):
            op=(f'<div class="opener photo" id="{tid}" style="background-image:url(\'file://{fpath}\')"><div class="veil"></div>'
                f'<div class="cap"><span class="badge">UNIDAD {uno} · {nivel}</span>'
                f'<div class="utitle" style="font-size:24pt;font-weight:bold;color:#fff;margin-top:6px;text-shadow:0 2px 10px rgba(0,0,0,.5)">{html.escape(t["name"])}</div>'
                f'<div class="usub">{sub}</div></div></div>')
        else:
            op=(f'<div class="opener nophoto" id="{tid}"><div class="cap"><span class="badge">UNIDAD {uno} · {nivel}</span>'
                f'<div class="utitle" style="font-size:24pt;font-weight:bold;color:#fff;margin-top:4px">{html.escape(t["name"])}</div>'
                f'<div class="usub">{sub}</div></div></div>')
        parts.append(op)
        parts.append(diagram(suj))
        vt=voc_tables(t['voc'])
        for key in ('verbos','sustantivos','adjetivos','otras'):
            if key in vt:
                parts.append(f'<h3>{VOC_TITLE[key]}</h3>')
                parts.append(gender_table(vt[key]) if key=='sustantivos' else plain_table(vt[key]))
        parts.append(render_ctx(parse_ctx(t['ctx'])))

    # -------- extras from md files --------
    def section_from_md(path, splitH1=True):
        raw=open(path,encoding="utf-8").read()
        return raw
    # Pronunciation + Expresiones (bonus file has two H1)
    bonus=open(f"{BUILD}/bonus_es.md",encoding="utf-8").read()
    for chunk in re.split(r'(?=^# )', bonus, flags=re.M):
        chunk=chunk.strip()
        if not chunk: continue
        m=re.match(r'^#\s+(.+)', chunk)
        title=m.group(1); rest=chunk[m.end():]
        parts.append(h(1,title))
        parts.append(md(rest))
    # Appendix reference
    ref=open(f"{BUILD}/annexe_reference_es.md",encoding="utf-8").read()
    ref=re.sub(r'^#\s+Appendix.*$','',ref,count=1,flags=re.M)
    parts.append(h(1,"Appendix — Grammar Reference"))
    parts.append(md(ref))

    # -------- alphabetical index --------
    words={}
    for t in themes:
        vt=voc_tables(t['voc']); nivel=t['meta'].get('nivel','A1'); uno=t['meta'].get('unidad','')
        for key,rows in vt.items():
            for r in rows[1:]:
                w=re.sub(r'^\s*(el|la|los|las)\s+','',r[0].strip(),flags=re.I) if key=='sustantivos' else r[0].strip()
                w=re.sub(r'\s*\(.+?\)','',w).strip()
                if w and w[0].isalpha(): words.setdefault(w.lower(), (w, f"{nivel[-1]}·{uno}"))
    parts.append(h(1,"Alphabetical Index"))
    parts.append('<p class="lead">Every headword, with the level·unit where it appears.</p>')
    letters={}
    for kw,(w,loc) in words.items():
        letters.setdefault(kw[0].upper(),[]).append((w,loc))
    ih=['<div class="indexgrid">']
    for L in sorted(letters):
        ih.append(f'<div class="idx-letter">{L}</div>')
        for w,loc in sorted(letters[L], key=lambda x:x[0].lower()):
            ih.append(f'<div class="ie">{html.escape(w)} <small>{loc}</small></div>')
    ih.append('</div>')
    parts.append("".join(ih))

    # -------- photo credits --------
    cred=[]
    cf=f"{PHOTOS}/credits.json"
    if os.path.exists(cf):
        seen={}
        for c in json.load(open(cf,encoding="utf-8")): seen[c.get('file')]=c
        for c in sorted(seen.values(), key=lambda x:x.get('file','')):
            cred.append(f"<div>{html.escape(c.get('title','') or c['file'])} — {html.escape(c.get('license','') or '')} — {html.escape((c.get('creator') or '')[:40])}</div>")
    parts.append(h(1,"Photo Credits"))
    parts.append('<p class="lead">All photos are openly licensed (CC0 / Public Domain / CC-BY / CC-BY-SA) via Openverse &amp; Wikimedia Commons. Diagrams and layout are original.</p>')
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
           f'<div class="kick">Español · Nivel A1 &amp; A2</div>'
           f'<h1>Spanish A1–A2<br>Complete Revision Manual</h1>'
           f'<div class="rule"></div>'
           f'<div class="sub">Grammar, vocabulary in context &amp; real photos<br>based on <em>Aula Internacional 1 &amp; 2</em></div>'
           f'<div class="meta"><div class="author">Aziz Dardouri</div>'
           f'<div class="badge">Revision edition · {datetime.date.today().strftime("%d/%m/%Y")}</div></div></div>')

    doc=(f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
         f'<link rel="stylesheet" href="file://{BUILD}/style_es.css"></head><body>'
         f'{cover}{"".join(toc)}{"".join(parts)}</body></html>')
    open(f"{BUILD}/_book.html","w",encoding="utf-8").write(doc)
    out=sys.argv[1] if len(sys.argv)>1 else f"{ROOT}/Espanol_A1-A2_Revision_Completa.pdf"
    HTML(string=doc, base_url=BUILD).write_pdf(out)
    print(f"PDF -> {out} ({os.path.getsize(out)//1024} KB) | themes={len(themes)} grammar={len(gindex)} indexwords={len(words)}")

if __name__=="__main__":
    build()
