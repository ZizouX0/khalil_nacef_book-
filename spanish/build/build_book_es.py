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
_EMOJI=re.compile('[\U0001F000-\U0001FAFF\U00002600-\U000027BF️]')
def md(t):
    _md.reset(); return _md.convert(_normalize(_EMOJI.sub('',t).strip()))
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

# ---------------- exercises parsing ----------------
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

def bonus_section(title_key):
    bonus=open(f"{BUILD}/bonus_es.md",encoding="utf-8").read()
    for chunk in re.split(r'(?=^# )', bonus, flags=re.M):
        chunk=chunk.strip()
        if not chunk: continue
        mm=re.match(r'^#\s+(.+)', chunk)
        if title_key.lower() in mm.group(1).lower():
            return mm.group(1), chunk[mm.end():]
    return None,None

# ---------------- assemble (learn-from-zero course) ----------------
def build():
    themes=[]
    for f in FILES: themes+=parse_file(f"{SRC}/{f}")
    umeta=json.load(open("/tmp/es/units.json",encoding="utf-8"))
    foto={}
    for lv in ("A1","A2"):
        for u in umeta[lv]: foto[(lv,str(u['unidad']))]=u
    exdict={}
    for f in ["ex_a1p1.md","ex_a1p2.md","ex_a2p1.md","ex_a2p2.md"]:
        exdict.update(parse_exercises(f"{SRC}/{f}"))
    repaso=parse_repaso(f"{SRC}/repaso_es.md")
    parts=[]; answer_key=[]

    # -------- front matter: Welcome + Pronunciation --------
    welcome=open(f"{BUILD}/welcome_es.md",encoding="utf-8").read()
    wt=re.match(r'^#\s+(.+)', welcome);
    parts.append(h(1, wt.group(1))); parts.append(md(welcome[wt.end():]))
    pt,pbody=bonus_section("Pronunciation")
    if pt: parts.append(h(1,pt)); parts.append(md(pbody))
    cog=open(f"{BUILD}/cognates_es.md",encoding="utf-8").read()
    for chunk in re.split(r'(?=^# )', cog, flags=re.M):
        chunk=chunk.strip()
        if not chunk: continue
        cm=re.match(r'^#\s+(.+)', chunk)
        parts.append(h(1,cm.group(1))); parts.append(md(chunk[cm.end():]))

    # -------- the lessons --------
    parts.append(h(1,"The Lessons · Las lecciones"))
    parts.append('<p class="lead">Twenty units in learning order — A1 first, then A2. Work through them one at a time. Each has <b>Vocabulary → Grammar → Conversations → Practice</b>. Answers to every exercise are in the <b>Answer Key</b> at the back.</p>')
    for t in themes:
        mta=t['meta']; nivel=mta.get('nivel','A1'); uno=mta.get('unidad','0'); suj=mta.get('sujeto','')
        u=foto.get((nivel,uno),{})
        fpath=f"{PHOTOS}/{nivel.lower()}_u{int(uno):02d}.jpg"
        tid=slug(f"lesson-{t['name']}-{nivel}-{uno}"); TOC.append((2,tid,f"{t['name']} ({nivel})"))
        sub="You will learn: "+html.escape(u.get('scope',''))
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
        # 1) Vocabulary
        parts.append('<h3>Vocabulary</h3>')
        parts.append(diagram(suj))
        vt=voc_tables(t['voc'])
        for key in ('verbos','sustantivos','adjetivos','otras'):
            if key in vt:
                parts.append(f'<h4>{VOC_TITLE[key]}</h4>')
                parts.append(gender_table(vt[key]) if key=='sustantivos' else plain_table(vt[key]))
        # 2) Grammar (this unit's own points, taught)
        gp=parse_grammar(t['gram'])
        if gp:
            parts.append('<h3>Grammar</h3>')
            for p in gp:
                parts.append(f'<h4>{html.escape(p["name"])}</h4>')
                parts.append(md(p['main']))
                if p['ojo']:
                    parts.append('<div class="box ojo"><span class="h">¡Ojo!</span>'+md_inline(p['ojo'])+'</div>')
        # 3) Conversations
        ctx=parse_ctx(t['ctx'])
        if ctx['dialogues'] or ctx['examples'] or ctx['truco']:
            parts.append('<h3>Conversations</h3>')
            parts.append(render_ctx(ctx))
        # 4) Practice
        ex=exdict.get((nivel,str(int(uno))))
        if ex and ex[0]:
            parts.append('<h3>Practice</h3>')
            parts.append('<div class="practice">'+md(ex[0])+'</div>')
            parts.append('<p class="ansref"><small>→ Check your answers in the <b>Answer Key</b> at the back of the book.</small></p>')
            if ex[1]:
                answer_key.append((f"Unidad {uno} — {t['name']} ({nivel})", ex[1]))
        rk=f"{nivel}-{int(uno)}"
        if rk in repaso:
            rc,ra=repaso[rk]
            rid=slug(f"repaso-{rk}"); TOC.append((2,rid,f"Repaso — after {nivel} unit {uno}"))
            parts.append(f'<div class="repaso" id="{rid}"><h2 style="page-break-before:always">Repaso · Review after {nivel} Unit {uno}</h2>')
            parts.append(md(rc)); parts.append('</div>')
            if ra: answer_key.append((f"Repaso — after {nivel} unit {uno}", ra))

    # ================= REFERENCE =================
    parts.append(h(1,"Reference"))
    parts.append('<p class="lead">Use this section to look things up any time: full grammar tables, a glossary of every verb and adjective, useful phrases, an index, and the answer key.</p>')
    # Grammar reference
    ref=open(f"{BUILD}/annexe_reference_es.md",encoding="utf-8").read()
    ref=re.sub(r'^#\s+Appendix.*$','',ref,count=1,flags=re.M)
    parts.append(h(1,"Grammar Reference"))
    parts.append(md(ref))

    # Useful Expressions (from bonus)
    et,ebody=bonus_section("Useful Expressions")
    if et: parts.append(h(1,et)); parts.append(md(ebody))

    # -------- global recap glossaries (all verbs / all adjectives) --------
    allv={}; alladj={}
    for t in themes:
        vt=voc_tables(t['voc'])
        for r in vt.get('verbos',[])[1:]:
            if len(r)>=3 and r[0].strip() and r[0] not in allv: allv[r[0]]=(r[1],r[2])
        for r in vt.get('adjetivos',[])[1:]:
            if len(r)>=3 and r[0].strip() and r[0] not in alladj: alladj[r[0]]=(r[1],r[2])
    vkey=lambda x: re.sub(r'[^a-záéíóúñü]','',x[0].lower())
    parts.append(h(1,"Verb & Adjective Glossary (A1+A2)"))
    parts.append(f'<p class="lead">Every verb and adjective in the book, gathered in one place for fast look-up — {len(allv)} verbs and {len(alladj)} adjectives &amp; adverbs.</p>')
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

    # -------- answer key --------
    parts.append(h(1,"Answer Key · Soluciones"))
    parts.append('<p class="lead">Answers to every Practice exercise, unit by unit. Check your work here and review anything you missed.</p>')
    parts.append('<div class="answerkey">')
    for title,ans in answer_key:
        parts.append(f'<h3>{html.escape(title)}</h3>')
        parts.append(md(ans))
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
           f'<div class="kick">Learn Spanish from zero · A1 → A2</div>'
           f'<h1>Spanish for Beginners<br>A Complete Course</h1>'
           f'<div class="rule"></div>'
           f'<div class="sub">Lessons, real photos &amp; exercises — no prior Spanish needed<br>based on <em>Aula Internacional 1 &amp; 2</em></div>'
           f'<div class="meta"><div class="author">Aziz Dardouri</div>'
           f'<div class="badge">Beginner\'s course · {datetime.date.today().strftime("%d/%m/%Y")}</div></div></div>')

    doc=(f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
         f'<link rel="stylesheet" href="file://{BUILD}/style_es.css"></head><body>'
         f'{cover}{"".join(toc)}{"".join(parts)}</body></html>')
    open(f"{BUILD}/_book.html","w",encoding="utf-8").write(doc)
    out=sys.argv[1] if len(sys.argv)>1 else f"{ROOT}/Espanol_A1-A2_Curso_Completo.pdf"
    HTML(string=doc, base_url=BUILD).write_pdf(out)
    print(f"PDF -> {out} ({os.path.getsize(out)//1024} KB) | lessons={len(themes)} units_with_exercises={len(answer_key)} indexwords={len(words)}")

if __name__=="__main__":
    build()
