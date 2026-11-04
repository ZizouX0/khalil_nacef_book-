# SIELE booklet — writing guide for chapter files (v2, visual edition)

The booklet is rendered from Markdown plus a small set of **visual blocks**. The goal is a guide that is
**pleasant, easy to understand and easy to remember**. Think "colourful revision cards", not "textbook".

## Voice
- Talk to the student: "you". Short sentences. One idea per line. Simple English (the student is A2 in Spanish and not a native English speaker).
- Spanish for every example, phrase and exercise instruction. Spain Spanish, but SIELE accepts all varieties.
- Every task section should leave the student with **one sentence they will remember** (a `:::remember` note or a `:::big` slogan).
- Prefer a memory trick (acronym, image, rhythm, contrast) over an explanation. Invent good ones.
- Cut anything the student doesn't need for the exam. No long paragraphs (max 3 lines). No walls of bullets (max ~6 bullets in a list).

## Headings
- `# 🎧 Comprensión auditiva · Listening` — chapter title (one per file, first line). It becomes a colourful opener band.
- `## …` — main section. `### …` — sub-section. Don't go deeper.
- Task headings: `## Tarea 3 · B1 · Ocho personas, un tema` — the renderer turns `· A1 ·`, `· A2 ·`, `· B1 ·`, `· B2 ·`, `· C1 ·` (or `· B2–C1 ·`) into a coloured level badge.

## Inline extras
- `==text==` → highlighted (yellow marker). Use for the words that score / the key word in a model answer.
- `[A2]` `[B1]` `[B2]` → small level pill (e.g. after a phrase).
- Source references in parentheses `(Manual p.52)`, `(Guía p.170)`, `(Edelsa p.143)` are shown as small grey tags. Keep them, but **max one per paragraph/card**; don't stack many.
- Normal Markdown: **bold**, *italic*, lists, tables (use tables sparingly — prefer the blocks below).

## Visual blocks
A block starts with a line `:::name optional title` and ends with a line `:::` (nothing else on it). Blocks can be nested one level (e.g. a `:::trap` inside an `:::exam` is NOT needed — keep nesting rare). Lines inside "line-based" blocks use ` | ` as a separator.

| Block | Use it for | Body format |
|---|---|---|
| `:::stats` | The 3–5 big numbers of a test (chapter opener) | one per line: `BIG | small label` e.g. `55 min | to answer 38 questions` |
| `:::golden Title` | 3–5 golden rules (chapter opener, boosters) | a numbered Markdown list (`1.` …). Each item: **bold short rule** + one line why |
| `:::big` | One slogan to remember | one or two short lines, e.g. `Same words = suspicious. Same meaning = correct.` |
| `:::flow Title` | A timeline / sequence of the task (timings) | one per line: `label | detail` e.g. `30 s | read the 11 sentences` |
| `:::steps Title` | "How to do it" step-by-step | a numbered Markdown list, 3–6 steps, each step **bold verb** + short detail |
| `:::trap Title` | A trap (red card) | Markdown. Show the trap with a tiny example (one line of Spanish) and the fix |
| `:::tip Title` | A tip (green card) | Markdown |
| `:::remember` | Sticky note — the one thing to remember | 1–3 short lines |
| `:::levelup Title` | A2 version vs B1 version side by side | left part, a line `---`, right part (Markdown). Left = A2, right = B1. Use `==…==` on the B1 features |
| `:::phrases Title` | Phrase bank as cards | one per line: `Español | English | tag` (tag optional: A2, B1, B2, or a short "when to use") |
| `:::mnemonic WORD` | Acronym / memory trick | one per line: `L | Word | what it means` (L = the letter or emoji). The title WORD is shown big |
| `:::model Title` | A model answer (email, spoken answer) | Markdown. Use `==…==` on the parts that score. Optionally end with a short "Why it scores" list after a line `---` |
| `:::exam Title` | A practice task in exam format | Markdown (instructions in Spanish, texts, numbered questions with options a) b) c) each on its own line as a nested list). Title like `Tarea 2 · A2 · 12 min` |
| `:::transcript Title` | Audio transcript for practice (cover it, listen first) | Markdown |
| `:::answers Title` | Answer key | Markdown list, compact: `1 b — why (trap name)` |
| `:::scale Title` | Score → level bar | one per line: `LEVEL | range | flag` (flag optional: `target` or `safe`) e.g. `B1 | 18–26 correct | target` |
| `:::icons Title` | Grid of rules with an icon (exam day, interface rules) | one per line: `emoji | short text` |
| `:::day Thu 5 Nov | Listening + Reading` | One day of the 7-day plan | Markdown list of tasks (they become tick boxes) with minutes |
| `:::checklist Title` | Things to tick (book plan, night before) | Markdown list |
| `:::flashcards Title` | Fold-in-half revision cards | one per line: `front (Spanish) | back (English / rule)` — 8, 12 or 16 per block |

## Chapter skeleton for a test chapter (Reading / Listening / Writing / Speaking)
```
# <emoji> <Spanish name> · <English name>
:::stats
...4 tiles...
:::
:::golden The 4 golden rules
...
:::
:::big
one slogan
:::
## The map            ← one :::flow or a compact table: each Tarea, level, what you get, items
## Tarea 1 · A1 · …   ← for each A1–B1 task: 2–3 lines "what you get", :::flow (timing), :::steps, 1–3 :::trap, :::tip, :::remember, one "📚 Practise:" line with book pages
## Tarea 2 · A2 · …
## Tarea 3 · B1 · …   ← (Listening: your priority — deepest)
## Tareas 4–6 · B2–C1 · Survival   ← short: what it is + how to grab points
## Phrases that score  ← 2–4 :::phrases blocks (+ :::levelup)
## Practice            ← :::exam blocks (original), :::transcript for listening
## Answers             ← :::answers
## Your book plan      ← :::checklist with page refs and minutes
```

## Rules carried over (still apply)
- Facts about the exam must come from the sources (the existing chapter you are rewriting already has them with page refs). Don't invent exam facts. Don't lose important facts when condensing — move them into cards.
- Practice material must be ORIGINAL. Book texts/transcripts may only be quoted in short fragments (max ~2 sentences) to illustrate a trap, with a page ref.
- No real names of the student; use neutral names (Sam, Lucía, Javi…).
- No raw HTML. No emoji inside `:::stats` numbers. Emojis in headings and icons are welcome but don't overdo them (max one per heading).
