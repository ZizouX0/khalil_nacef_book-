#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure how often each taught word actually comes back.

A word introduced once and never retrieved again is listed, not taught. The
research puts reliable multi-aspect learning at 8-10 encounters with at least
three of them SPACED (in a later unit, a recall strip, a checkpoint or a test),
so this reports, per headword:

  ENC     every occurrence anywhere in the book
  SPACED  occurrences the learner reaches AFTER finishing the teaching unit
  RETR    occurrences where the word is the ANSWER to a prompt, not just read

Usage:  python3 build/check_vocab.py [--list-orphans]
"""
import re, os, sys, unicodedata, importlib.util, collections

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=f"{ROOT}/sources_md"; BUILD=f"{ROOT}/build"
spec=importlib.util.spec_from_file_location('b', f"{BUILD}/build_book_es.py")
B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

ORDER=[('A1',str(i)) for i in range(10)]+[('A2',str(i)) for i in range(1,11)]
def idx(nivel,uni): return ORDER.index((nivel,str(int(uni))))

STOP=set("""el la los las un una unos unas de del a al y o e u que en con por para sin
sobre es son soy eres somos sois está están estoy estás muy mas más no sí se me te le
nos os les lo mi tu su mis tus sus yo tú él ella usted nosotros vosotros ellos ellas
hay ser estar tener hacer ir ver dar qué cómo cuándo dónde quién cuál porque pero
también tampoco ya todavía cuando como donde si""".split())

def norm(s):
    s=unicodedata.normalize('NFD', s.lower())
    s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return re.sub(r'[^a-z0-9ñ ]+',' ', s)

def stem(w):
    """crude Spanish stemmer — enough to match hablar/hablo/hablamos, casa/casas"""
    w=norm(w).strip()
    for suf in ('aciones','ciones','amente','antes','endos','ando','iendo','ados','idos',
                'adas','idas','ares','eres','ires','emos','imos','amos','aste','iste',
                'aron','ieron','aba','ia','ar','er','ir','os','as','es','a','o','e','s'):
        if len(w)-len(suf)>=4 and w.endswith(suf): return w[:-len(suf)]
    return w

# ---- collect headwords -------------------------------------------------
heads=[]   # (stem, display, teaching index, kind)
for f in ['a1p1.md','a1p2.md','a2p1.md','a2p2.md']:
    for t in B.parse_file(f"{SRC}/{f}"):
        n=idx(t['meta']['nivel'], t['meta']['unidad'])
        for kind,rows in B.voc_tables(t['voc']).items():
            for r in rows[1:]:
                w=r[0].strip()
                w=re.sub(r'^\s*(el|la|los|las)\s*/\s*(el|la|los|las)\s+','',w,flags=re.I)
                w=re.sub(r'^\s*(el|la|los|las)\s+','',w,flags=re.I)
                w=re.sub(r'\s*\(.*?\)','',w).split('/')[0].strip()
                if not w or not w[0].isalpha(): continue
                st=stem(w)
                if len(st)<3 or st in STOP: continue
                heads.append((st,w,n,kind))

# ---- build the corpus, tagged by when the learner reaches it ------------
# (position, is_retrieval, text)
corpus=[]
for f in ['a1p1.md','a1p2.md','a2p1.md','a2p2.md']:
    for t in B.parse_file(f"{SRC}/{f}"):
        n=idx(t['meta']['nivel'], t['meta']['unidad'])
        corpus.append((n, False, "\n".join(t['gram']+t['ctx'])))
for f in ['ex_a1p1.md','ex_a1p2.md','ex_a2p1.md','ex_a2p2.md']:
    for (lv,u),(prac,ans) in B.parse_exercises(f"{SRC}/{f}").items():
        corpus.append((idx(lv,u), True, prac+"\n"+ans))
for f in ['test_a1p1.md','test_a1p2.md','test_a2p1.md','test_a2p2.md']:
    for (lv,u),d in B.parse_tests(f"{SRC}/{f}").items():
        # a test is taken after its unit is finished
        corpus.append((idx(lv,u)+0.5, True, " ".join(d.values())))
for k,(c,a) in B.parse_repaso(f"{SRC}/repaso_es.md").items():
    lv,u=k.split('-'); corpus.append((idx(lv,u)+0.5, True, c+"\n"+a))
for k,(title,body) in B.parse_keyed("relampago_es.md").items():
    lv,u=k.split('-'); corpus.append((idx(lv,u)-0.5, True, body))

toks=[(pos, retr, set(stem(x) for x in norm(txt).split() if len(x)>2))
      for pos,retr,txt in corpus]

# ---- measure -----------------------------------------------------------
ENC=collections.Counter(); SPACED=collections.Counter(); RETR=collections.Counter()
seen=set()
for st,w,n,kind in heads:
    if st in seen: continue
    seen.add(st)
    for pos,retr,bag in toks:
        if st in bag:
            ENC[st]+=1
            if pos>n: SPACED[st]+=1
            if retr and pos>n: RETR[st]+=1

uniq={}
for st,w,n,kind in heads: uniq.setdefault(st,(w,n,kind))
content=[s for s in uniq if uniq[s][2] in ('verbos','sustantivos','adjetivos')]

def pct(x,tot): return f"{100*x/tot:.1f}%"
tot=len(content)
orph=[s for s in content if SPACED[s]==0]
one =[s for s in content if SPACED[s]<=1]
thin=[s for s in content if ENC[s]<8]
noretr=[s for s in content if RETR[s]==0]
med=lambda xs: sorted(xs)[len(xs)//2] if xs else 0

print(f"content headwords analysed: {tot}\n")
print(f"  median total encounters          {med([ENC[s] for s in content])}")
print(f"  median SPACED encounters         {med([SPACED[s] for s in content])}")
print(f"  never returns after its unit     {len(orph):>4}  {pct(len(orph),tot)}")
print(f"  <=1 spaced encounter             {len(one):>4}  {pct(len(one),tot)}")
print(f"  never a retrieval answer again   {len(noretr):>4}  {pct(len(noretr),tot)}")
print(f"  under the 8-encounter threshold  {len(thin):>4}  {pct(len(thin),tot)}")

if '--list-orphans' in sys.argv:
    print("\norphans by teaching unit:")
    byu=collections.defaultdict(list)
    for s in orph: byu[uniq[s][1]].append(uniq[s][0])
    for n in sorted(byu):
        lv,u=ORDER[n]; print(f"  {lv}-{u}: {len(byu[n])}  {', '.join(sorted(byu[n])[:14])}")
if '--worklist' in sys.argv:
    # For each unit N, the earlier words most in need of a retrieval, drawn from
    # units N-1, N-3 and N-4 as the recycling map prescribes.
    import json
    need=lambda st: (SPACED[st], ENC[st])
    out={}
    for n in range(1,20):
        lv,u=ORDER[n]; pool=[]
        for back in (1,3,4):
            m=n-back
            if m<0: continue
            cand=[st for st in uniq if uniq[st][1]==m and uniq[st][2] in
                  ('verbos','sustantivos','adjetivos')]
            cand.sort(key=need)
            pool += [(uniq[st][0], ORDER[m][0]+'-'+ORDER[m][1], SPACED[st]) for st in cand[:14]]
        out[f"{lv}-{u}"]=pool[:28]
    json.dump(out, open('/tmp/recycle_worklist.json','w',encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"\nwrote /tmp/recycle_worklist.json — {sum(len(v) for v in out.values())} candidate items across 19 units")
sys.exit(0)
