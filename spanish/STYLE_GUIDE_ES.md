# STYLE_GUIDE — Spanish A1+A2 Revision Manual (Aula Internacional 1 & 2)

Mandatory shared format for the 4 extractor agents. Goal: 4 perfectly consistent files the orchestrator can merge mechanically and render as an **illustrated** English-medium book. **Follow this exactly.**

## 0. Golden rules
- **Explanations, instructions and labels: in ENGLISH.** Spanish is the target language: every Spanish example, word, and dialogue gets an **English translation**.
- Teach vocabulary **in context** (chunks, collocations) — never bare word lists only. Nouns ALWAYS with their article (**el/la**) + plural.
- Content must be **original** (your own explanations, examples and dialogues). Use the source only to know *which* grammar and vocabulary the unit covers. Do **not** copy the book's texts.
- Tone: friendly, clear, confidence-building — for a true beginner revising alone.

## 1. File & section format
- One markdown file per agent in `spanish/sources_md/` named `a1p1.md`, `a1p2.md`, `a2p1.md`, `a2p2.md`.
- One `##` section per unit, EXACT format:
  ```
  ## Tema: <Unit title> {#nivel=A1|A2 #unidad=<n> #sujeto=<keyword>}
  ```
  Use the `#sujeto` given in your bundle header for each unit (it drives merging).
- Each unit section contains, in this order, these EXACT `###` headings:
  1. `### Gramática`
  2. `### Vocabulario`
  3. `### En contexto`

## 2. GRAMMAR part
For every grammar point in the unit's SCOPE, one `####` block, EXACT format:
```
#### G · <Canonical name> {#cat=<category>}

**Rule.** <clear explanation in English>

**Examples.**
- <Spanish sentence> — *<English translation>*
- <Spanish sentence> — *<English translation>*  (3–5 examples)

**Table.**
<a COMPLETE markdown table — full conjugation / full paradigm; no empty cells>

**Ojo.** <the #1 pitfall / false-friend / common error, in English. If none: "—">
```
- `#cat` — pick ONE from this closed list (used to regroup grammar by topic):
  `genero-articulos, pronombres, ser-estar-hay, presente, perifrasis, pasado, imperativo-condicional-gerundio, gustar-similares, comparativos-cuantificadores, preposiciones, interrogativos-conectores, numeros-tiempo`
- Canonical names must be **stable** (so A1 & A2 versions of the same rule merge). Examples:
  `Ser vs Estar`, `The verb hay`, `Regular present tense (-ar/-er/-ir)`, `Stem-changing & irregular present`, `Reflexive (pronominal) verbs`, `The verb gustar`, `Direct object pronouns (lo/la/los/las)`, `Possessives`, `Demonstratives (este/ese/aquel)`, `Pretérito perfecto`, `Pretérito indefinido`, `Pretérito imperfecto`, `Indefinido vs imperfecto`, `The gerundio and estar + gerundio`, `The affirmative imperative`, `The conditional`, `Comparatives and superlatives`, `Por vs Para`, `Prepositions of place`, `ir a / tener que / hay que + infinitive`, `Interrogatives (qué, cuál, dónde…)`.
- Conjugation tables: give ALL 6 persons (yo, tú, él/ella/usted, nosotros/as, vosotros/as, ellos/ellas/ustedes).
- If a point is a level-up of an A1 rule (A2 agents), start the block with:
  `> [NIVEL A2] extends the A1 rule.`

## 3. VOCABULARY part
> Collect **all the key vocabulary of the unit** from its SCOPE and text (and, for A1, you may cross-check the book's Glosario). Aim for thorough coverage, grouped by type. 4 tables, EXACT headings, sorted alphabetically:

```
#### Verbos
| Verb (infinitive) | Notes (irregularity / regime) | English |
|---|---|---|
| desayunar | regular | to have breakfast |
| dormir | o→ue (duermo) | to sleep |
| gustar | + indirect obj. (me gusta) | to like |

#### Sustantivos
| Noun | Plural | English |
|---|---|---|
| el libro | los libros | book |
| la casa | las casas | house |
| la ciudad | las ciudades | city |

#### Adjetivos y adverbios
| Word | Notes | English |
|---|---|---|
| bueno/a | irreg. compar. mejor | good |
| rápido/a | — | fast |

#### Otras palabras (preposiciones, conectores, expresiones)
| Word / Expression | Type | English |
|---|---|---|
| al lado de | preposition | next to |
| por eso | connector | that's why |
```
- **Nouns**: ALWAYS start with `el` or `la` (this drives the colour-coded gender pill). Use `el/la` for common-gender; plural-only or feminine-el (el agua) → add a note.
- **Verbs**: infinitive; note the irregularity/stem-change and the regime (e.g. `gustar` → `+ indirect obj.`).
- **Adjectives**: masculine/feminine form `-o/-a`; note irregular comparatives.
- Keep English translations concise.

## 4. EN CONTEXTO part (this becomes the coloured dialogue boxes)
```
### En contexto

**Diálogo — <short situation title>**
> **Ana:** <Spanish line>
> **Luis:** <Spanish line>
> … (6–12 natural lines that reuse the unit's vocabulary & grammar)

*Translation:* <full English translation of the dialogue, run together or line by line>

**More examples:**
- <Spanish sentence> — *<English>*
- <Spanish sentence> — *<English>*  (5–8 sentences)
```
- 1–2 dialogues per unit. Make them a real, coherent exchange (not disguised sentence lists).
- Optionally add one **`**Truco.** <a memory tip in English>`** per unit (renders as a yellow TIP box).

## 5. End of file
Finish each file with:
```
<!-- END agent=<a1p1|a1p2|a2p1|a2p2> ; units=<n> ; vocab≈<N> -->
```

## 6. Not your job (handled by the renderer)
Real photos, diagrams (house/body/etc.), colour-coded el/la pills, the coloured boxes, cover, table of contents, footer "Aziz Dardouri", pagination — all added automatically later. Just produce clean markdown in the format above.
