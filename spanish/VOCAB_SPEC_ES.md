# VOCAB_SPEC_ES.md — Vocabulario elemental A1–A2, chapter by chapter

Working notes for *Vocabulario. Nivel elemental A1–A2* (Baralo, Genís, Santana).
The learner sends the pages of a lesson as screenshots; each lesson produces two things.

## 1. In the conversation: the lesson worked through

Everything as tables, **Spanish on the left, English on the right**:

- every reading text, translated sentence by sentence;
- every exercise solved, each answer as a whole Spanish sentence with its English;
- where an answer is open (a table to fill with your own ideas), say so and give a model answer.

The worked exercises stay in the conversation. The PDF is for revising, not a key to the book.

## 2. In the PDF: a revision chapter

`vocabulario_elemental.md` is the source; `python3 build/build_vocab_es.py` typesets it into
`Vocabulario_Elemental_A1-A2.pdf`. Rebuild and commit both after every lesson.

A chapter is `## Unidad N · <title>`, a subtitle line, then these blocks in this order:

| Block | What it holds | Line format |
|---|---|---|
| `::: aprender` | 4 can-do aims | `- say what the weather is like` |
| `::: cards` | the 8–16 must-knows, with an icon each | `- ☀️ Hace sol. \| It's sunny.` |
| `::: estaciones` | big illustrated cards for a closed set (seasons…) | `- 🌸 la primavera \| spring \| marzo · abril · mayo \| Spanish line \| English line` |
| `::: clave` | the pattern behind the words, one column each (max 4) | `- HEAD \| hint \| es = en ; es = en ; …` |
| `::: termometro` | a scale from one extreme to the other (6 steps) | `- 🥵 Hace mucho calor. \| It's very hot. \| más de 35 °C` |
| `::: caja` | a reference box: any markdown, e.g. a small table | markdown |
| `::: ojo` | the traps a learner will fall into | markdown list |
| `::: dialogo` | a short dialogue using the chapter's words | `- Name: Spanish line \| English line` |
| `::: parte` | the band before the full lists (no body) | — |
| `### n. Name — English` + table | **Todo el vocabulario**: every word, Spanish \| English | markdown table |
| `::: quiz` | Pruébate: questions, `---`, answers (printed upside down) | markdown |
| `::: yase` | Ya sé…: the can-do aims again, as tick boxes | markdown list |

Not every chapter needs every block: `termometro` and `estaciones` only exist where the topic
has a scale or a closed set. The others are in every chapter.

Rules for the content:

- Nouns always carry their article; the PDF colours `el` blue and `la` magenta.
- Adjectives that change show both forms: `rojo / roja`. Stem-changing verbs show infinitive → form: `llover → llueve`.
- Block titles are `emoji Spanish — English`: the Spanish is what to learn, the English sits lighter beside it.
- Any emoji is drawn from `assets/icons/` (Twemoji). The builder stops and names any that are missing.
- Dialogues and quizzes recycle the chapter's own words; anything new gets its English beside it.
