#!/usr/bin/env python3
"""Generate the verb-card chapter (src_words/w3_verbs.md) with verbecc.

Each card: 7 tenses x 6 persons + imperative, gerund, participle. Forms that
differ from the regular -ar/-er/-ir pattern are marked so the student sees
exactly what to memorise.
"""
import html, json, logging, os, re, sys
logging.disable(logging.CRITICAL)
import verbecc

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "src_words", "w3_verbs.md")
cg = verbecc.CompleteConjugator(lang="es")

PERSONS = ["yo", "tú", "él", "nosotros", "vosotros", "ellos"]
PLABEL = ["yo", "tú", "él / ella / usted", "nosotros/as", "vosotros/as", "ellos / ellas / ustedes"]
TENSES = [("indicativo", "presente", "Presente", "now · habits"),
          ("indicativo", "pretérito-perfecto-compuesto", "Pret. perfecto", "HE · hoy, este año, nunca"),
          ("indicativo", "pretérito-perfecto-simple", "Indefinido", "FUI · ayer, en 2020"),
          ("indicativo", "pretérito-imperfecto", "Imperfecto", "ERA · de pequeño, siempre"),
          ("indicativo", "futuro", "Futuro", "mañana, el año que viene"),
          ("condicional", "presente", "Condicional", "advice · wishes · if…"),
          ("subjuntivo", "presente", "Subjuntivo", "WAIT · espero que…")]

GROUPS = [
    ("Regular models: learn these 3 patterns", [("hablar", "to speak"), ("comer", "to eat"), ("vivir", "to live")]),
    ("The big irregulars", [("ser", "to be (identity, description)"), ("estar", "to be (place, state)"), ("ir", "to go"),
                            ("tener", "to have"), ("hacer", "to do, to make"), ("decir", "to say, to tell"),
                            ("poder", "can, to be able"), ("querer", "to want, to love"), ("venir", "to come"),
                            ("poner", "to put"), ("salir", "to go out, to leave"), ("saber", "to know (facts)"),
                            ("dar", "to give"), ("ver", "to see, to watch")]),
    ("Stem-changing verbs (e → ie, o → ue, e → i)", [("pensar", "to think"), ("empezar", "to start"), ("preferir", "to prefer"),
                            ("sentir", "to feel, to be sorry"), ("volver", "to come back"), ("encontrar", "to find"),
                            ("dormir", "to sleep"), ("jugar", "to play (games, sport)"), ("pedir", "to ask for, to order"),
                            ("seguir", "to follow, to continue"), ("elegir", "to choose")]),
    ("Spelling changes and other useful verbs", [("llegar", "to arrive"), ("buscar", "to look for"), ("conocer", "to know (people, places)"),
                            ("conducir", "to drive"), ("traer", "to bring"), ("oír", "to hear"), ("leer", "to read"),
                            ]),
]


NIGHT = {}
for n, vs in {}.items():   # night tags disabled: the bank is organised by task
    for v in vs.split():
        NIGHT[v] = n


def forms(c, mood, tense):
    out = {}
    for item in c["moods"][mood][tense]:
        pr = item["pr"]
        key = {"usted": None, "ella": None, "vos": None, "ellas": None, "ustedes": None}.get(pr, pr)
        if key in PERSONS and key not in out:
            f = item["c"][0]
            f = re.sub(r"^(yo|tú|él|nosotros|vosotros|ellos|que yo|que tú|que él|que nosotros|que vosotros|que ellos)\s+", "", f)
            f = re.sub(r"^que\s+\S+\s+", "", f)
            out[key] = f
    return [out.get(p, "") for p in PERSONS]


REG = {
    "ar": {"Presente": ["o", "as", "a", "amos", "áis", "an"], "Indefinido": ["é", "aste", "ó", "amos", "asteis", "aron"],
           "Imperfecto": ["aba", "abas", "aba", "ábamos", "abais", "aban"], "Subjuntivo": ["e", "es", "e", "emos", "éis", "en"]},
    "er": {"Presente": ["o", "es", "e", "emos", "éis", "en"], "Indefinido": ["í", "iste", "ió", "imos", "isteis", "ieron"],
           "Imperfecto": ["ía", "ías", "ía", "íamos", "íais", "ían"], "Subjuntivo": ["a", "as", "a", "amos", "áis", "an"]},
    "ir": {"Presente": ["o", "es", "e", "imos", "ís", "en"], "Indefinido": ["í", "iste", "ió", "imos", "isteis", "ieron"],
           "Imperfecto": ["ía", "ías", "ía", "íamos", "íais", "ían"], "Subjuntivo": ["a", "as", "a", "amos", "áis", "an"]},
}
FUT = ["é", "ás", "á", "emos", "éis", "án"]
CON = ["ía", "ías", "ía", "íamos", "íais", "ían"]
HE = ["he", "has", "ha", "hemos", "habéis", "han"]


def regular(inf, tname, i):
    stem, end = inf[:-2], inf[-2:]
    end = "ir" if end == "ír" else end
    if tname in REG[end]:
        return stem + REG[end][tname][i]
    if tname == "Futuro":
        return inf.replace("í", "i") + FUT[i]
    if tname == "Condicional":
        return inf.replace("í", "i") + CON[i]
    if tname == "Pret. perfecto":
        return f"{HE[i]} {stem}{'ado' if end == 'ar' else 'ido'}"
    return None


def card(inf, meaning):
    c = json.loads(str(cg.conjugate(inf)))
    ger = c["moods"]["gerundio"]["gerundio"][0]["c"][0] if "gerundio" in c["moods"] else ""
    pk = "participio" if "participio" in c["moods"] else "participo"   # verbecc spells it "participo"
    par = c["moods"][pk][pk][0]["c"][0] if pk in c["moods"] else ""
    # verbecc lists adjective-only participles first for a few verbs (elegir -> "electo");
    # the compound tenses must use the verbal participle.
    PART_FIX = {"elegir": "elegido"}
    if inf in PART_FIX:
        par = PART_FIX[inf]
    cols = [(lab, hint, forms(c, m, t)) for m, t, lab, hint in TENSES]
    cols = [(lab, hint, [f"{HE[i]} {par}" for i in range(6)] if lab == "Pret. perfecto" else fs)
            for lab, hint, fs in cols]
    irregular_any = False
    rows = ""
    for i, pl in enumerate(PLABEL):
        tds = ""
        for lab, hint, fs in cols:
            f = fs[i]
            reg = regular(inf, lab, i)
            irr = reg is not None and f and f != reg
            irregular_any |= irr
            tds += f'<td class="{"irr" if irr else ""}">{html.escape(f)}</td>'
        rows += f'<tr><th>{pl}</th>{tds}</tr>'
    imp = c["moods"].get("imperativo", {}).get("afirmativo", [])
    impd = {}
    for it in imp:
        who = {"tú": "tú", "él": "usted", "usted": "usted", "vosotros": "vosotros"}.get(it["pr"])
        if who and who not in impd:
            impd[who] = re.sub(r"\s*(tú|usted|vosotros)$", "", it["c"][0])
    head = "".join(f'<th>{lab}<small>{hint}</small></th>' for lab, hint, _ in cols)
    tag = "irregular" if irregular_any else "regular"
    imp_line = " · ".join(f"<b>{html.escape(v)}</b> ({k})" for k, v in impd.items())
    return (f'<div class="verb"><div class="vh"><span class="vi">{inf}</span><span class="vm">{meaning}</span>'
            f'<span class="vt {tag}">{tag}</span>'
            f'{f"<span class=vn>🌙 Noche {NIGHT[inf]}</span>" if inf in NIGHT else ""}<span class="vg">gerundio <b>{html.escape(ger)}</b> · participio <b>{html.escape(par)}</b></span></div>'
            f'<table class="vtab"><thead><tr><th></th>{head}</tr></thead><tbody>{rows}</tbody></table>'
            f'<div class="vimp">Imperativo: {imp_line}</div></div>')


def main():
    parts = ["# 🔤 Verbos · The verbs you need, conjugated", "",
             "Red forms are **irregular**: they don't follow the pattern of *hablar / comer / vivir*. Memorise the red ones; the rest you can build yourself.", "",
             "**Fully regular verbs** (*viajar, llevar, quedar, trabajar, estudiar…*) work exactly like *hablar / comer / vivir*.", "",
             ":::tip How to read a card",
             "**usted** uses the *él* form and **ustedes** the *ellos* form. **Pret. perfecto** = *haber* + participle (*he comido*). Column hints tell you **when** to use each tense (HE · FUI · ERA, WAIT).",
             ":::", ""]
    for title, verbs in GROUPS:
        parts += [f"## {title}", ""]
        for inf, meaning in verbs:
            parts += [card(inf, meaning), ""]
            print(inf, file=sys.stderr)
    # special cards written by hand (impersonal / pronoun patterns)
    parts += ["## Special patterns", "",
              '<div class="verb"><div class="vh"><span class="vi">haber → hay</span><span class="vm">there is / there are (one form for singular and plural)</span><span class="vt irregular">irregular</span></div>'
              '<table class="vtab"><thead><tr><th></th><th>Presente</th><th>Pret. perfecto</th><th>Indefinido</th><th>Imperfecto</th><th>Futuro</th><th>Condicional</th><th>Subjuntivo</th></tr></thead>'
              '<tbody><tr><th>there is/are</th><td class="irr">hay</td><td>ha habido</td><td class="irr">hubo</td><td>había</td><td class="irr">habrá</td><td class="irr">habría</td><td class="irr">haya</td></tr></tbody></table>'
              '<div class="vimp">En mi barrio <b>hay</b> dos parques · Ayer <b>hubo</b> un concierto · Antes <b>había</b> un cine · Espero que <b>haya</b> sitio.</div></div>', "",
              '<div class="verb"><div class="vh"><span class="vi">gustar</span><span class="vm">to like: the thing liked is the subject</span><span class="vt regular">pattern</span></div>'
              '<table class="vtab"><thead><tr><th></th><th>one thing / verb</th><th>several things</th><th>past (indefinido)</th><th>past (imperfecto)</th><th>wish (condicional)</th></tr></thead><tbody>'
              '<tr><th>(a mí) me</th><td>me gusta el cine</td><td>me gustan los libros</td><td>me gustó</td><td>me gustaba</td><td>me gustaría</td></tr>'
              '<tr><th>(a ti) te</th><td>te gusta viajar</td><td>te gustan las playas</td><td>te gustó</td><td>te gustaba</td><td>te gustaría</td></tr>'
              '<tr><th>(a él/ella/usted) le</th><td>le gusta</td><td>le gustan</td><td>le gustó</td><td>le gustaba</td><td>le gustaría</td></tr>'
              '<tr><th>(a nosotros) nos</th><td>nos gusta</td><td>nos gustan</td><td>nos gustó</td><td>nos gustaba</td><td>nos gustaría</td></tr>'
              '<tr><th>(a vosotros) os</th><td>os gusta</td><td>os gustan</td><td>os gustó</td><td>os gustaba</td><td>os gustaría</td></tr>'
              '<tr><th>(a ellos/ustedes) les</th><td>les gusta</td><td>les gustan</td><td>les gustó</td><td>les gustaba</td><td>les gustaría</td></tr>'
              '</tbody></table><div class="vimp">Same pattern: <b>encantar, interesar, importar, molestar, doler, parecer</b> → <i>me encantan las fiestas · me duele la cabeza</i></div></div>', "",
              ]
    open(OUT, "w", encoding="utf-8").write("\n".join(parts) + "\n")
    print("wrote", OUT, file=sys.stderr)


if __name__ == "__main__":
    main()
