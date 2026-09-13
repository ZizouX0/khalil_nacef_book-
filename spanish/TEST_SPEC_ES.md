# TEST SPEC — end-of-unit "Prueba" for every unit

This is a **mechanical contract**. Writing agents follow it exactly. No variation, no creativity in
the structure — the creativity goes into the items.

Evidence base (summarised): retrieval practice beats restudy (Roediger & Karpicke 2006); *difficult*
successful retrieval beats easy retrieval (Pyc & Rawson 2009); interleaved grammar beats blocked
practice, especially for low-knowledge learners (Nakata & Suzuki 2019); recognition items overstate
knowledge by ~20% vs. cued recall, so productive items must dominate; 80% is the conventional
mastery-learning criterion (Bloom/Guskey); feedback must answer "where to next?" (Hattie & Timperley),
so a bare score is not acceptable — every test routes the learner back to a named section.

---

## 1. Global constants

| Parameter | A1 units (A1-0 … A1-9) | A2 units (A2-1 … A2-10) |
|---|---|---|
| Sections | 6 (A–F) | 7 (A–G) |
| Items | 30 | 38 |
| Total points | **40** | **50** |
| Mastery gate | **32/40 (80%)** | **40/50 (80%)** |
| Recycled (spiral) points | 5 of 40 | 10 of 50 |
| Learner time | 25 minutes | 30 minutes |
| Numbering | continuous **Q1–Q30** | continuous **Q1–Q38** |

## 2. Rules every writing agent obeys mechanically

1. **Continuous numbering** across sections. Never restart at 1 inside a section.
2. **Never test forward.** Every item must be answerable from that unit's own `### Gramática`,
   `### Vocabulario` or `### En contexto`, or from an **earlier** unit. Check the source file.
3. **Recycled items carry `°` in the ANSWER KEY AND ROUTING TABLE ONLY — never on the question paper.**
   The learner meets them cold.
4. Recycled items come only from units *before* this one. In A2, at least 2 recycled points must come
   from an **A1** unit.
5. **No item may be copied from that unit's five Práctica exercises.** Change the lexis, the person, or
   the direction (recognition → production). The test is a harder retrieval, not a rerun.
6. Every MC item has exactly **3 options (a/b/c)**, one key, two *plausible* distractors that a learner
   who half-knows the rule would actually pick. Never "both", "none", or a joke option.
7. Every gap takes **one word** unless the section instruction says otherwise.
8. The answer key lists **every** acceptable variant, separated by ` / `.
9. Nouns in Section A are always keyed with **el/la**.
10. Routing strings must copy the `#### G · <name>` heading **character-for-character** from the source
    file. Never paraphrase a heading.

## 3. File format (the parser depends on this exactly)

```
## Test — Unidad 7: ¡A comer! {#nivel=A1 #unidad=7}

**Before you start.** Do this test at least one day after you finished the unit, in one sitting,
with the book closed and no dictionary. Allow 25 minutes. Write your answers on paper. Mark
yourself with the key at the end — only after you have answered everything. Total: 40 points.

**A · Vocabulary (6 points).** Write the Spanish. For nouns, include **el** or **la** — the article counts. For verbs, write the infinitive.
1. fork
2. spoon
...

**B · Fill the gap (8 points).** Write **one word** in each gap. ...
7. ¿Me ___ (poner) un café, por favor? *(usted)*
...

**F · Write (6 points).** Write **40–50 words** in Spanish. ...

**Points.** A 6 + B 8 + C 6 + D 4 + E 10 + F 6 = **40 points**

**Answers.**
1) el tenedor
2) la cuchara
...
13) gustan °
...

**Model.**
Buenos días. De primero quiero una ensalada mixta. ...

**Checks.**
- I used **de primero** and **de segundo** (or **de postre**).
- I ordered with **¿Me pone…?** or **¿Me trae…?**
- ...

**Routing.**
| Missed | Re-read | Then redo |
|---|---|---|
| Q1–Q6 | Unit 7 → Vocabulario → Sustantivos and Verbos tables | Práctica Exercise 4 |
| Q11, Q12 | Unit 7 → Gramática → "Direct object pronouns (lo/la/los/las)" | Práctica Exercise 2 |
| Q13 | Unit 5 → Gramática → "The verb gustar" | Unit 5, Práctica Exercise 1 |
```

Marker lines `**Points.**`, `**Answers.**`, `**Model.**`, `**Checks.**`, `**Routing.**` are **required**
and must appear in that order. Everything before `**Points.**` is the question paper.

---

## 4. A1 section template (40 points, 30 items)

### A · Vocabulary — 6 items × 1 pt = 6 pts
Cued recall, English → Spanish, single word. **Productive, not matching.** 4 nouns + 2 verbs.
> **A · Vocabulary (6 points).** Write the Spanish. For nouns, include **el** or **la** — the article counts. For verbs, write the infinitive.

### B · Gap-fill — 8 items × 1 pt = 8 pts
Keyword-cued gap-fill (verb forms + pronouns + function words). 2 of the 8 are recycled.
> **B · Fill the gap (8 points).** Write **one word** in each gap. Where there is a word in brackets, use that word in the correct form. The person is shown when it is not obvious.

### C · Multiple choice — 6 items × 1 pt = 6 pts
3-option form contrast. Use **only** where a gap-fill would admit more than one answer.
> **C · Choose the correct option (6 points).** Circle **a**, **b** or **c**. Only one is correct.

### D · Error correction — 4 items × 1 pt = 4 pts
**Exactly one** error per sentence; learner rewrites the whole sentence. A1 errors are morphological.
> **D · One mistake (4 points).** Each sentence contains **exactly one** mistake. Rewrite the whole sentence correctly.

### E · Translation — 5 items × 2 pts = 10 pts
Integrative, English → Spanish. **Every sentence must be a plausible utterance in the unit's situation**,
never a bare word pair. This is the heaviest section by design.
> **E · Translate into Spanish (10 points — 2 points each).** Write the whole sentence. See the marking note in the key before you score this section.

### F · Guided writing — 1 task = 6 pts
Open production, scored by a 6-check binary checklist + model answer. 40–50 words.
> **F · Write (6 points).** Write **40–50 words** in Spanish. <situation + 3 things to do>. When you have finished, read your text against the six checks in the key and give yourself **1 point for each check you can honestly tick**.

**The six checks are always:** (1) a unit *function*, (2) a unit *formula/chunk*, (3) a unit *grammar
point*, (4) a second unit *function*, (5) a third unit *function or closing formula*, (6) the fixed
length-and-reread check. Never write a check the learner cannot verify by looking at their own page.

**A1 point map:** A 6 + B 8 + C 6 + D 4 + E 10 + F 6 = **40**

---

## 5. A2 section template (50 points, 38 items) — genuinely harder

The mastery bar stays 80%. The **test** gets harder. All eleven changes are mandatory:

1. **Size:** 38 items, 50 points, 30 minutes. Gate 40/50.
2. **New Section F — Reading (5 items × 1 pt).** A **90–120-word Spanish text** (email, notice, blog
   post, ad) + 3 MC items + 2 short-answer items **answered in Spanish**. Mirrors DELE A2
   *Comprensión de lectura*.
   > **F · Read and answer (5 points).** Read the text once, then answer. You may read it again. Answer questions 4 and 5 in Spanish — a few words is enough.
3. **Section A: chunks, not words.** Cues are collocations/fixed expressions (*"to be in a hurry" →
   tener prisa*), never bare single nouns.
4. **Section B → 10 items, and 4 of them UNCUED** (no bracketed infinitive — the learner infers both
   lexeme and form). Instruction adds: *"Four of these gaps have no word in brackets — you must decide which word is missing."*
5. **Section B interleaves tenses:** at least two past tenses mixed in unpredictable order.
6. **Section C distractors are same-lemma forms** (*fui / era / he ido*; *por / para / para que*), so
   recognising the word doesn't help — only the rule does.
7. **Section D → 5 items, usage errors.** Sentences run 10–15 words with a subordinate clause; the one
   error is a *choice* error (ser/estar, por/para, indefinido/imperfecto, subjunctive trigger), in a
   sentence that looks well-formed on the surface.
8. **Section E translations are two-clause** — joined by *porque, cuando, aunque, mientras, así que* —
   with at least one past tense. Still 5 × 2 pts.
9. **Section G (writing) → 70–90 words, 8 points, 8 checks.** Two of the eight checks must be
   **discourse-level**, e.g. *"I joined two of my sentences with a connector"*, *"My text has an opening
   and a closing line appropriate to who I am writing to."*
10. **Accents count from A2 on.** A missing/wrong accent costs the point in A–D and counts as a slip in E.
11. **Recycling → 10/50 (20%)**, from any earlier unit, ≥2 points from an **A1** unit.

**A2 point map:** A 6 + B 10 + C 6 + D 5 + E 10 + F 5 + G 8 = **50**

---

## 6. Marking block (printed once in the book, not per unit — do not write it into unit files)

Handled by the build engine. Writing agents only produce `**Model.**` and `**Checks.**`.

## 7. Routing rule

Every item is born from exactly one source block. Build the routing table by **inverting the
item-writing order** — never write it afterwards from memory.

| Section | Routes to |
|---|---|
| A | `### Vocabulario` → the named table |
| B, C, D | `### Gramática` → `#### G · <exact heading>` (C may route to Vocabulario → Otras palabras) |
| E | `### En contexto` **plus** the one `G ·` block that sentence tests |
| F (A1) / G (A2) | `### En contexto` (dialogue) **plus** the `**Truco.**` box |
| any `°` item | the **earlier** unit's `G ·` block or vocabulary table, named with its unit number |

Each routing line also names the **corrective task** — the matching Práctica exercise from `ex_*.md`.
Mastery learning requires re-instruction *plus* a corrective, not just a page reference.
