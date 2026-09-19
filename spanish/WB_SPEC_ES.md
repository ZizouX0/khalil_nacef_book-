# Workbook specification — *Cuaderno de Ejercicios A1–A2*

The binding contract for every chapter of the companion exercise book. It exists for the same reason
`TEST_SPEC_ES.md` does: several people write these chapters in parallel, and the only way the result reads as
one book is if the shape is decided once, here, and nobody improvises it.

Read this next to `TEST_SPEC_ES.md`. Where the two overlap — routing format, self-check wording, the `°`
recycling marker — this file follows the test spec rather than inventing a second convention.

---

## 1 · What this book is for

The course book's own audit measured three holes, and this workbook exists to fill them. Nothing in a chapter
is there for any other reason:

| Hole in the course book | What fills it here |
|---|---|
| 46% of headwords are met once, tested once a day later, then never again; only 30% get three spaced returns | Block **E** (16 spiral items) and the Block **D** reading text (20–30 recycled words in context) |
| 66% of recycling looks back one or two units; almost none reaches seven | Block **E** draws from units **N−1, N−3, N−7 and N−12** |
| Not one of the hundred exercises is reading comprehension or free writing — yet a quarter of the A2 test mark is exactly those | Blocks **D, D2** (17% of every chapter) and **H1, H2** (13%) |

A chapter that is merely "more exercises" has failed. Every item is allocated against one of those three.

---

## 2 · The shape of a chapter

Nine blocks, always in this order, always with these Spanish headings. **58 items, 70 points, 32 minutes of
work plus 8 of marking.** The item count is a ceiling, not a target.

| # | Heading | What it is | Items | Pts |
|---|---|---|---|---|
| A | **Reconocimiento** | 6 current-unit words. A1: match Spanish↔English, 8 in the pool for 6 slots. A2: English → Spanish chunk recall, nouns keyed with *el/la*. | 6 | 6 |
| B | **Formas** | Current-unit grammar, **blocked** by point, cued with a bracketed infinitive and person. Small on purpose — the course book already carries five exercises of this shape. | 6 | 6 |
| C | **Texto con huecos** | One connected 70–90-word text. **Rational deletion, never fixed-ratio**: 4 lexical gaps + 4 grammatical. A1 has a word bank, A2 does not. | 8 | 8 |
| D | **Lectura** | One text — email, notice, chat thread, blog post. 90–120 words at A1, 130–160 at A2. 2 true/false **with the Spanish line that proves it**, 2 multiple choice, 2 short answer. | 6 | 6 |
| D2 | **Lee y reconstruye** | 3 sentences lifted verbatim from the Block D text. Read one, cover it, write it from memory, uncover, compare. Scored 2/1/0. | 3 | 6 |
| — | *split point* | **"Stop here if you are splitting this chapter — come back within two days."** | | |
| E | **Vuelve** | The spacing engine. 4 lanes × 4 items, printed in **shuffled lane order**. | 16 | 16 |
| F | **Un solo error** | 5 sentences, **exactly one error each**, the rest well-formed. Rewrite the whole sentence. | 5 | 5 |
| G | **Traduce** | 4 sentences English → Spanish, 2 points each: one for the structure, one for the lexis. | 4 | 8 |
| H1 | **Tú** | 3 stems completed **about the learner's own life**, each forcing two bracketed target words. | 3 | 3 |
| H2 | **Escribe** | One open task. A1 50–70 words, A2 80–100. Six binary self-checks. | 1 | 6 |

### Why that order

Recognition → cued production → uncued production → input → integrative → free. The productive blocks sit
last, after the reading has re-primed the words they need. The spiral sits mid-chapter: retrieving twelve-week-old
material is the hardest thing in the chapter and must not land on a tired learner, but opening with it
would make the chapter feel impossible.

**Item (a) of every block is printed already solved, in grey, as the model.** It costs one item and removes
the "what does this instruction actually want?" tax.

---

## 3 · Block E — the spacing engine

This is the block the workbook exists for. Get it wrong and the rest is decoration.

**Lanes.** Chapter N draws from units **N−1 (L1), N−3 (L2), N−7 (L3), N−12 (L4)** — four items each.
Equivalently a word taught in unit N comes back in chapters N+1, N+3, N+7 and N+12. At roughly a unit a week
that is gaps of 1, 2, 4 and 5 weeks: an expanding ladder whose last gap is about a tenth of a year's retention
interval, which is where the spacing research puts the optimum.

**Lane composition.**

| Lane | Content |
|---|---|
| L1 (N−1) | 4 vocabulary items, English → Spanish cued recall |
| L2 (N−3) | 4 grammar gap-fills — cued at A1, uncued at A2 |
| L3 (N−7) | 2 vocabulary recall + 2 multiple choice with **same-lemma distractors** (*fui / era / he ido*) |
| L4 (N−12) | 2 vocabulary (recognition at A1, recall at A2) + 2 two-word translation fragments |

**Early chapters, where a lane points before the course started.** Its four items move to the oldest lane that
does exist. If none does, they become extra current-unit retrieval.

| Chapter | L1 | L2 | L3 | L4 |
|---|---|---|---|---|
| A1-0 | — (16 → current unit) | — | — | — |
| A1-1 | 16 | — | — | — |
| A1-2 … A1-6 | 4 | 12 | — | — |
| A1-7 … A2-1 | 4 | 4 | 8 | — |
| A2-2 … A2-10 | 4 | 4 | 4 | 4 |

**Printing.** Items appear in **shuffled lane order** — never grouped, never labelled by lane on the page.
The lane and source unit appear **in the answer key only**, using the test spec's `°` marker. A learner who
can see "from Unit 3" above an item has been told which rule to use, and the item stops testing anything.

Exception: chapters A1-0 to A1-4 **do** print the source unit, because a beginner five weeks in needs the
scaffold. From A1-5 it comes off and never goes back on.

**Which words.** Allocate from the coverage ledger (`build/wb_ledger.csv`), always preferring headwords with
fewest retrievals logged. Never pick a word because it is convenient to write a sentence around.

---

## 4 · Block the new, interleave the old

Blocks A, B and C practise the current unit and are **blocked** — grouped by point, one thing at a time.
Block E is **interleaved** — shuffled, mixed, nothing grouped.

This is not a compromise, it is the finding. Interleaved grammar practice produces more errors during
training and beats blocked practice a week later — but only above a prior-knowledge threshold; below it,
interleaving backfires. A learner meeting the *pretérito indefinido* on Tuesday is a novice on Tuesday and an
intermediate on the material from eleven weeks ago. So: block the new, interleave the old.

---

## 5 · What changes between A1 and A2

The course book's exercises are 73% production at A1 and 71% at A2 — flat, when it should rise. Support is
stripped deliberately across the book:

| | A1 chapters | A2 chapters |
|---|---|---|
| Block A | match Spanish ↔ English | English → Spanish chunk recall |
| Block C | word bank printed | no word bank |
| Block E | source unit printed to A1-4, then not | never printed |
| Block E distractors | different lemmas | **same lemma** — recognising the word cannot help, only the rule can |
| Block F errors | morphological (agreement, endings, articles) | **choice** errors (*ser/estar*, *por/para*, indefinido/imperfecto) in longer sentences whose surface looks fine |
| Block G | one clause | two clauses joined by *porque / cuando / aunque / mientras / así que*, at least one past tense |
| Tenses in E | one past tense per item | two or more mixed, in unpredictable order |

Target mix: **A1 ≈ 25% recognition / 40% supported production / 35% free. A2 ≈ 12% / 28% / 60%.**

---

## 6 · The answer key

In a book with no teacher the key *is* the teaching. Elaborated feedback is worth about three times a bare
correct answer and ten times a bare right/wrong. Every entry carries five fields:

1. **Key** — the canonical answer.
2. **Also accept** — every acceptable variant, separated by ` / `. Exhaustive, not illustrative.
3. **Not accepted** — the *one* near-miss a half-knowing learner would actually write, named, with why.
   This is the field the course book lacks and the most valuable one here.
4. **Why** — the rule or the contrast, fifteen words at most.
5. **Route** — `Unit N → Gramática → "G · <exact heading>"`, character for character, plus the corrective
   exercise. Same contract as the test spec, so the whole course routes identically.

Written as one line, the house style is the course book's own:

> `c) una *(nouns in -ción and -dad are always feminine; not "un" — the ending decides, not the sound)* → Unit 2 → Gramática → "G · Noun gender", then Práctica Ex 2`

**Items with more than one right answer.** Design them out first — if a gap would admit two answers, make it
three-option multiple choice, exactly as the test spec requires. Where they survive (translation, cloze), the
"Also accept" field must be complete. Where they cannot be enumerated (D2, H1, H2), score by **binary checks
only**, and print the model labelled *"one possible answer — do not score yourself against it."*

---

## 7 · Marking, and why there is no pass mark

The unit tests gate at 80%. **This book does not gate at all**, and that is deliberate: interleaved practice
is supposed to produce errors, because the errors are the mechanism. A gate would punish the learner for the
thing that is working.

Instead:

- **Tick `✓` (sure) or `?` (unsure) on every item before opening the key.** Four cells result, and
  **sure-and-wrong** is the valuable one — a confidently held error, once corrected, sticks unusually well.
  The routing table is read off sure-and-wrong first, unsure-and-right second.
- **Two pens.** Answers in one colour, marking in another, so later editing is visible to the learner themselves.
- **60% per block is an action threshold, not a pass mark.** Below it, do the corrective the routing names.
- **A running chart at the back** records chapter totals, with the instruction to watch the trend, not the number.

People's sense of what they know is uncorrelated with what they actually know, and learners who look up an
answer genuinely come to believe they knew it. So honesty is built into the page rather than asked for: keys
live in one section at the back with a tinted edge, never on the spread and never overleaf.

---

## 8 · Hard rules

1. **Only Spanish the learner has already met.** Check every word of every chapter against the unit sources up
   to and including that unit. The subjunctive is never taught in this course and must never appear.
2. **Every item is a full sentence** — the same rule the course book now follows. No bare word pairs, no
   `(yo) ___` paradigm drills.
3. **Every item has somewhere to write.** The renderer does this, but write the source so it can:
   one item per line, lettered `a)`.
4. **Never reuse a sentence** from the course book's own exercises, tests or dialogues. A learner who has done
   the unit will have seen it.
5. **Reading texts must be ≥98% words already taught**, plus at most three new ones glossed in the margin.
   Below that coverage, comprehension collapses and the exercise measures guessing.
6. **The Block D text must contain the words Block H needs.** The reading is not only a comprehension check;
   it is lexical priming for the writing task six blocks later.
7. **Error-correction sentences carry exactly one error** and are otherwise perfect. Never print a paragraph
   of errors to hunt through — extended exposure to wrong Spanish is a real risk, not a theoretical one.
8. **Item counts per block are fixed.** A chapter that runs long gets shorter sentences, not fewer items.

---

## 9 · The heavy units

A1-2, A1-3 and A1-4 carry 86, 93 and 87 new vocabulary rows against a course mean of 57 — and the audit found
their practice is the thinnest in the book. They are printed as **two half-chapters each** (2A/2B, 3A/3B,
4A/4B): 39 items and about 19 minutes apiece. That puts 78 items where the load is heaviest, with no sitting
longer than twenty minutes.

---

## 10 · What this book does not claim

780 headwords needing three retrievals each is 2,340 slots. Twenty chapters at this length deliver roughly
1,000–1,100. So a **core 300** — the words carrying the communicative load of A1–A2 — are guaranteed three
spaced retrievals and finish on 7–10 lifetime encounters. The remaining ~480 get one further encounter each,
prioritised from those the audit found are currently met once and abandoned.

That is the honest number and the front matter says so. A workbook that claimed to bring back all 1,200 words
would be lying, and the course book's back matter has already told the reader not to expect it.
