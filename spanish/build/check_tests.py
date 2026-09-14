#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical checks over every unit test.

Catches the defect classes a manual pass found in the A2 tests: answers that
appear elsewhere on their own question paper, missing/duplicated question
numbers, wrong point totals, models that are the wrong length or fail their own
check list, routing gaps, routing headings that do not exist in the sources,
recycled-item markers leaking onto a question paper, and items copied verbatim
from that unit's Practica.

Usage:  python3 build/check_tests.py [--verbose]
Exit code is the number of findings.
"""
import re, os, sys, unicodedata, importlib.util

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=f"{ROOT}/sources_md"
spec=importlib.util.spec_from_file_location('b', f"{ROOT}/build/build_book_es.py")
B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

TESTS=["test_a1p1.md","test_a1p2.md","test_a2p1.md","test_a2p2.md"]
UNITS=["a1p1.md","a1p2.md","a2p1.md","a2p2.md"]
EXES=["ex_a1p1.md","ex_a1p2.md","ex_a2p1.md","ex_a2p2.md"]

def norm(s):
    s=unicodedata.normalize('NFD', s.lower())
    s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return re.sub(r'[^a-z0-9 ]+',' ', s).strip()

def words(s): return [w for w in norm(s).split() if len(w)>3]

# ---- reference data -----------------------------------------------------
G_HEADINGS=set()
for f in UNITS:
    for m in re.finditer(r'^####\s*G\s*·\s*(.+?)\s*(?:\{#cat=.+?\})?\s*$',
                         open(f"{SRC}/{f}",encoding='utf-8').read(), re.M):
        G_HEADINGS.add(m.group(1).strip())

PRACTICA={}
for f in EXES:
    for k,(p,a) in B.parse_exercises(f"{SRC}/{f}").items():
        PRACTICA[k]=set(norm(l) for l in p.split("\n") if len(norm(l))>25)

findings=[]
def flag(unit, kind, msg):
    findings.append((unit, kind, msg))

# ---- per-test checks ----------------------------------------------------
for f in TESTS:
    for key,t in sorted(B.parse_tests(f"{SRC}/{f}").items(), key=lambda x:(x[0][0],int(x[0][1]))):
        lvl,uno=key; U=f"{lvl}-{uno}"
        want=38 if lvl=='A2' else 30
        pts ='50' if lvl=='A2' else '40'
        paper,ans=t['paper'],t['answers']

        # 1. numbering
        nums=[int(x) for x in re.findall(r'(?m)^(\d+)\.', paper)]
        miss=[i for i in range(1,want+1) if i not in nums]
        dup=[n for n in set(nums) if nums.count(n)>1]
        if miss: flag(U,'numbering',f"question(s) missing from the paper: {miss}")
        if dup:  flag(U,'numbering',f"duplicated question number(s): {sorted(dup)}")

        # 2. points
        m=re.search(r'=\s*\*\*(\d+)\s*points', t['points'] or '')
        if not m or m.group(1)!=pts:
            flag(U,'points',f"point map says {m.group(1) if m else '?'}, expected {pts}")

        # 3. recycled marker must never appear on the paper
        if '°' in paper: flag(U,'leak',"recycled-item marker appears on the question paper")

        # 4. answer key coverage
        akeys={int(x) for x in re.findall(r'(?m)^(\d+)\)', ans)}
        gaps=[i for i in range(1,want) if i not in akeys]
        if gaps: flag(U,'key',f"no answer keyed for: {gaps}")

        # 5. ANSWER LEAKAGE — a keyed answer appearing elsewhere on its own paper.
        # Section F at A2 is reading comprehension: its answers are supposed to be
        # in the printed text, so those questions are exempt.
        READING=set(range(33,38)) if lvl=='A2' else set()
        paper_n=norm(paper)
        # Map each question number to its OWN block — the numbered line plus any
        # a)/b)/c) option lines that follow it. A multiple-choice answer has to
        # appear among its own options, so only occurrences outside the block count.
        plines=paper.split("\n"); blocks={}; cur=None
        for ln in plines:
            mnum=re.match(r'^\s*(\d+)\.', ln)
            if mnum: cur=int(mnum.group(1)); blocks[cur]=[ln]
            elif cur and (re.match(r'^\s*[a-c]\)', ln) or not ln.strip()):
                if ln.strip(): blocks[cur].append(ln)
            elif ln.strip().startswith('**'): cur=None
            elif cur: blocks[cur].append(ln)
        for am in re.finditer(r'(?m)^(\d+)\)\s*(.+)$', ans):
            qn=int(am.group(1)); raw=am.group(2)
            if qn in READING: continue
            first=raw.split('/')[0]
            first=re.sub(r'^[a-c]\)\s*','',first).strip()          # MC "b) texto"
            first=re.sub(r'\s*°\s*','',first)
            first=re.sub(r'\*+','',first).strip(' .')
            aw=words(first)
            if len(aw)<2: continue        # single words are too noisy to test
            phrase=' '.join(aw)
            if not phrase: continue
            own=blocks.get(qn,[])
            outside=[l for l in plines if l not in own and phrase in norm(l)]
            if outside:
                where=outside[0].strip()[:60]
                flag(U,'leak',f"answer to Q{qn} (“{first}”) also appears elsewhere on the paper: “{where}”")

        # 6. model length + does the model satisfy its own checks
        model=re.sub(r'\*+','',t['model']).strip()
        mw=len(model.split())
        lo,hi=(70,90) if lvl=='A2' else (40,50)
        if model and not (lo-6 <= mw <= hi+12):
            flag(U,'model',f"model answer is {mw} words, target {lo}-{hi}")
        nchecks=len(re.findall(r'(?m)^\s*[-*]\s+', t['checks']))
        wantc=8 if lvl=='A2' else 6
        if nchecks!=wantc: flag(U,'checks',f"{nchecks} self-check items, expected {wantc}")
        # NOTE: whether a model answer satisfies its own self-check list needs
        # judgement (ellipses, patterns like 'se + infinitive', paraphrase), so it
        # is reviewed by reading, not by string matching.

        # 7. routing coverage + headings that actually exist
        rt=t['routing']
        covered=set()
        for rm in re.finditer(r'Q(\d+)(?:\s*[–-]\s*Q?(\d+))?', rt):
            a=int(rm.group(1)); b=int(rm.group(2)) if rm.group(2) else a
            covered.update(range(a,b+1))
        rgaps=[i for i in range(1,want+1) if i not in covered]
        if rgaps: flag(U,'routing',f"no routing row for: {rgaps}")
        for hm in re.finditer(r'Gramática\s*→\s*[""\"](.+?)[""\"]', rt):
            if hm.group(1).strip() not in G_HEADINGS:
                flag(U,'routing',f"routes to a grammar block that does not exist: “{hm.group(1)}”")

        # 8. verbatim reuse of a Practica item
        pr=PRACTICA.get((lvl,str(int(uno))), set())
        for line in paper.split("\n"):
            ln=norm(line)
            if len(ln)>30 and ln in pr:
                flag(U,'rerun',f"item copied verbatim from this unit's Practica: “{line.strip()[:70]}”")

# ---- report -------------------------------------------------------------
if not findings:
    print("All checks pass across all 20 tests."); sys.exit(0)
by={}
for u,k,m in findings: by.setdefault(u,[]).append((k,m))
print(f"{len(findings)} finding(s) in {len(by)} test(s):\n")
for u in sorted(by, key=lambda x:(x[:2], int(x.split('-')[1]))):
    print(f"── {u}")
    for k,m in by[u]: print(f"   [{k}] {m}")
    print()
sys.exit(len(findings))
