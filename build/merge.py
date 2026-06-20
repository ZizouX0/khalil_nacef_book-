#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fusionne les 4 fichiers d'agents en un document markdown final structuré.
Sortie : build/final_book.md  (à passer ensuite à build_pdf.py)
"""
import re, os, sys

ROOT = "/home/user/khalil_nacef_book-"
SRC = os.path.join(ROOT, "sources_md")
BUILD = os.path.join(ROOT, "build")
FILES = ["a1_partie1.md", "a1_partie2.md", "a2_partie1.md", "a2_partie2.md"]

THEME_RE = re.compile(r'^##\s+Th[èe]me\s*:\s*(.+?)\s*(\{(.+?)\})?\s*$')
GRAM_RE  = re.compile(r'^####\s*G\s*[·.\-]\s*(.+?)\s*(\{#cat=(.+?)\})?\s*$')
SUBSEC_GRAM = re.compile(r'^###\s.*Grammaire', re.I)
SUBSEC_VOC  = re.compile(r'^###\s.*Vocabulaire', re.I)
SUBSEC_CTX  = re.compile(r'^###\s.*(Mise en contexte|contexte)', re.I)
VOC_TABLE_RE = re.compile(r'^####\s*(Verbes|Noms|Adjectifs|Autres)', re.I)

CAT_ORDER = ['groupe-nominal','cas','conjugaison','modaux','verbes-particularites',
             'temps-passe','adjectif','prepositions','syntaxe','divers']
CAT_TITLE = {
 'groupe-nominal':"1. Le groupe nominal — genre, articles, pronoms",
 'cas':"2. Les cas — Nominatif, Accusatif, Datif, Génitif",
 'conjugaison':"3. La conjugaison au présent",
 'modaux':"4. Les verbes de modalité",
 'verbes-particularites':"5. Verbes séparables, réfléchis et régime verbal",
 'temps-passe':"6. Les temps du passé — Perfekt et Präteritum",
 'adjectif':"7. L'adjectif — déclinaison et comparaison",
 'prepositions':"8. Les prépositions et leurs cas",
 'syntaxe':"9. La syntaxe — ordre des mots, négation, subordonnées",
 'divers':"10. Points divers",
}

def parse_meta(s):
    d={}
    if s:
        for m in re.finditer(r'#(\w+)=([^\s}]+)', s):
            d[m.group(1)]=m.group(2)
    return d

def split_lines_sections(lines, start, end):
    return lines[start:end]

def parse_file(path, level_hint):
    text=open(path,encoding="utf-8").read()
    lines=text.split("\n")
    # localiser les thèmes
    theme_idx=[i for i,l in enumerate(lines) if THEME_RE.match(l)]
    themes=[]
    for k,si in enumerate(theme_idx):
        ei = theme_idx[k+1] if k+1<len(theme_idx) else len(lines)
        m=THEME_RE.match(lines[si])
        name=m.group(1).strip()
        meta=parse_meta(m.group(3))
        block=lines[si+1:ei]
        # sous-sections
        g0=v0=c0=None
        for i,l in enumerate(block):
            if SUBSEC_GRAM.match(l): g0=i
            elif SUBSEC_VOC.match(l): v0=i
            elif SUBSEC_CTX.match(l): c0=i
        gram = block[g0:v0] if (g0 is not None and v0 is not None) else (block[g0:c0] if g0 is not None else [])
        voc  = block[v0:c0] if (v0 is not None and c0 is not None) else (block[v0:] if v0 is not None else [])
        ctx  = block[c0:] if c0 is not None else []
        themes.append(dict(name=name, meta=meta, level=meta.get('niveau',level_hint),
                           gram=gram, voc=voc, ctx=ctx, order=(level_hint,k)))
    return themes

def parse_grammar_points(gram_lines):
    """retourne liste de (name, cat, body_lines)"""
    idx=[i for i,l in enumerate(gram_lines) if GRAM_RE.match(l)]
    pts=[]
    for k,si in enumerate(idx):
        ei = idx[k+1] if k+1<len(idx) else len(gram_lines)
        m=GRAM_RE.match(gram_lines[si])
        name=m.group(1).strip()
        cat=(m.group(3) or 'divers').strip()
        body=gram_lines[si+1:ei]
        pts.append((name,cat,body))
    return pts

def norm_key(name):
    n=name.lower()
    n=re.sub(r'\(rappel\)|\(suite\)|\(a2\)|\(a1\)','',n)
    n=re.sub(r'[^a-zàâäéèêëïîôöùûüç ]','',n)
    return re.sub(r'\s+',' ',n).strip()

# Fusionne les doublons réels (mêmes notions) sans écraser les facettes complémentaires
TOPIC_RULES = [
 (r'prät[ée]rit.{0,25}(modal|modalv)|(modal|modalv).{0,25}prät[ée]rit', 'prat_modaux'),
 (r'konjunktiv', 'konjunktiv2'),
 (r'\bsollen\b', 'modal_sollen'),
 (r'\bwollen\b', 'modal_wollen'),
 (r'\bdürfen\b', 'modal_duerfen'),
 (r'\bmögen\b|\bmag\b', 'modal_moegen'),
 (r'können|müssen', 'modal_koennen_muessen'),
 (r'impérat', 'imperatif'),
 (r'prät[ée]rit.{0,30}(sein|haben)|(sein|haben).{0,12}prät[ée]rit', 'prat_sein_haben'),
 (r'prät[ée]rit.{0,20}régul', 'prat_regulier'),
 (r'présent.{0,20}sein|sein et haben', 'praes_sein_haben'),
 (r'présent des verbes régul', 'praes_regulier'),
 (r'indéfini', 'indefinis'),
 (r'relative.{0,30}préposition', 'relative_prep'),
 (r'pronoms relatifs', 'relative_base'),
 (r'\bweil\b', 'sub_weil'),
 (r'\bdass\b', 'sub_dass'),
 (r'\bwenn\b', 'sub_wenn'),
 (r'\bals\b', 'sub_als'),
 (r'\bdamit\b', 'sub_damit'),
 (r'um\s*…?\s*zu|um.{0,4}zu\b', 'sub_um_zu'),
 (r'questions? indirectes? en w|indirectes? en w', 'q_ind_w'),
 (r'\bob\b', 'q_ind_ob'),
 (r'nominalis', 'nominalisation'),
 (r'possessifs?\b.*datif', 'possessif_datif'),
 (r'\bpossessifs?\b', 'possessif'),
 (r'comparatif|superlatif|comparais', 'comparaison'),
 (r"terminaisons de l['’]adjectif", 'adj_endings'),
 (r'pronoms personnels.*datif', 'pp_datif'),
 (r'pronoms personnels.*accusatif', 'pp_akk'),
 (r'pronoms personnels', 'pp_nom'),
]
def topic_key(name):
    n=name.lower()
    for pat,key in TOPIC_RULES:
        if re.search(pat,n): return key
    return 'NAME::'+norm_key(name)

def parse_voc_rows(voc_lines):
    """retourne dict cat-> list de lignes de tableau (str)"""
    cats={}
    cur=None
    for l in voc_lines:
        m=VOC_TABLE_RE.match(l)
        if m:
            key=m.group(1).lower()
            cur='verbes' if key=='verbes' else 'noms' if key=='noms' else 'adj' if key.startswith('adj') else 'autres'
            cats.setdefault(cur,[])
            continue
        if cur and l.strip().startswith('|'):
            cats[cur].append(l.rstrip())
    return cats

def table_data_rows(rows):
    """garde seulement les lignes de données (exclut en-tête + séparateur)"""
    out=[]
    for r in rows:
        cells=[c.strip() for c in r.strip().strip('|').split('|')]
        if not cells or all(set(c)<=set('-: ') for c in cells): continue
        if cells[0].lower() in ('verbe (infinitif)','verbe','nom (avec article)','nom','mot','mot / expression'): continue
        out.append(cells)
    return out

# ---------- chargement ----------
all_themes=[]
for i,f in enumerate(FILES):
    p=os.path.join(SRC,f)
    if os.path.exists(p):
        all_themes += parse_file(p, 'A1' if f.startswith('a1') else 'A2')

# ---------- PARTIE 1 : grammaire regroupée ----------
gram_index={}   # key -> dict(name,cat,body,score,level)
for th in all_themes:
    for (name,cat,body) in parse_grammar_points(th['gram']):
        key=topic_key(name)
        score=len("\n".join(body))
        cur=gram_index.get(key)
        if (cur is None) or (score>cur['score']):
            gram_index[key]=dict(name=name,cat=cat,body=body,score=score,level=th['level'])

# regrouper par catégorie
by_cat={c:[] for c in CAT_ORDER}
for key,g in gram_index.items():
    by_cat.setdefault(g['cat'] if g['cat'] in by_cat else 'divers',[]).append(g)

p1=["# Partie 1 — Grammaire",
    "",
    "Toute la grammaire d'A1 et A2, **regroupée par notion** (et non par thème) selon une progression logique. Chaque règle : explication → exemples traduits → tableau récapitulatif → pièges. Les encarts 🔺 signalent ce qui est approfondi au niveau A2.",
    ""]
for cat in CAT_ORDER:
    pts=by_cat.get(cat,[])
    if not pts: continue
    pts.sort(key=lambda g:(0 if g['level']=='A1' else 1, -g['score']))  # A1 avant A2, puis le plus complet
    p1.append(f"## {CAT_TITLE[cat]}")
    p1.append("")
    for g in pts:
        p1.append(f"### {g['name']}")
        p1.append("")
        p1 += [l for l in g['body']]
        p1.append("")

# ---------- PARTIE 2 : vocabulaire par thème ----------
p2=["# Partie 2 — Vocabulaire par thème",
    "",
    "Le vocabulaire de chaque unité, **classé par nature** (verbes avec régime, noms avec genre+pluriel, adjectifs, mots-outils) puis **mis en contexte** par des mini-dialogues et des phrases d'exemple. Apprends les mots **par l'usage**.",
    ""]
LEVEL_BADGE={'A1':'`A1`','A2':'`A2`'}
for th in all_themes:
    badge=LEVEL_BADGE.get(th['level'],'')
    ein=th['meta'].get('einheit','')
    sub=f" — Einheit {ein}" if (ein.isdigit() and int(ein)>0) else ""
    p2.append(f"## {th['name']}  {badge}{sub}")
    p2.append("")
    # vocabulaire (on saute le titre ### d'origine, on remet propre)
    voc_body=[l for l in th['voc'] if not SUBSEC_VOC.match(l)]
    p2.append("### 📖 Vocabulaire")
    p2 += voc_body
    p2.append("")
    ctx_body=[l for l in th['ctx'] if not SUBSEC_CTX.match(l)]
    if ctx_body:
        p2.append("### 💬 Mise en contexte")
        p2 += ctx_body
        p2.append("")

# ---------- ANNEXE : tables globales ----------
# agréger verbes / adjectifs depuis tous les thèmes
verbs={}; adjs={}
for th in all_themes:
    cats=parse_voc_rows(th['voc'])
    for cells in table_data_rows(cats.get('verbes',[])):
        if len(cells)>=3:
            inf=cells[0]; verbs.setdefault(inf,(cells[1],cells[2]))
    for cells in table_data_rows(cats.get('adj',[])):
        if len(cells)>=3:
            adjs.setdefault(cells[0],(cells[1],cells[2]))

def clean_inf(s): return re.sub(r'\\','',s)
verb_rows=sorted(verbs.items(), key=lambda kv: clean_inf(kv[0]).lower())
adj_rows=sorted(adjs.items(), key=lambda kv: kv[0].lower())

annexe=[]
ref=open(os.path.join(BUILD,"annexe_reference.md"),encoding="utf-8").read()
# on transforme le H1 de l'annexe en H1 de partie
annexe.append(ref.replace("# Annexe — Récapitulatifs grammaticaux",
                          "# Annexe — Récapitulatifs"))
annexe.append("")
annexe.append("## E · Glossaire de tous les verbes rencontrés (A1+A2)")
annexe.append("")
annexe.append(f"*{len(verb_rows)} verbes, classés alphabétiquement. La colonne « formes » donne le régime et, pour les verbes forts/irréguliers, la 3ᵉ pers. + l'auxiliaire + le participe passé.*")
annexe.append("")
annexe.append("| Verbe | Formes / régime | Traduction |")
annexe.append("|---|---|---|")
for inf,(forms,tr) in verb_rows:
    annexe.append(f"| {inf} | {forms} | {tr} |")
annexe.append("")
annexe.append("## F · Glossaire de tous les adjectifs & adverbes (A1+A2)")
annexe.append("")
annexe.append(f"*{len(adj_rows)} entrées, classées alphabétiquement.*")
annexe.append("")
annexe.append("| Adjectif / adverbe | Comparatif/superlatif si irrég. | Traduction |")
annexe.append("|---|---|---|")
for w,(comp,tr) in adj_rows:
    annexe.append(f"| {w} | {comp} | {tr} |")
annexe.append("")

final = "\n".join(p1) + "\n\n" + "\n".join(p2) + "\n\n" + "\n".join(annexe) + "\n"
out=os.path.join(BUILD,"final_book.md")
open(out,"w",encoding="utf-8").write(final)

# stats
print(f"Thèmes: {len(all_themes)}")
print(f"Points de grammaire uniques: {len(gram_index)}")
print(f"Verbes (glossaire global): {len(verb_rows)}")
print(f"Adjectifs/adverbes (glossaire global): {len(adj_rows)}")
print(f"-> {out} ({os.path.getsize(out)//1024} Ko)")
