# Juego de Conversación — the specification

The third book. The course book teaches, the workbook makes it stick, this one makes you **say it out
loud to another person**. It is the only one of the three that cannot be done alone.

Two learners at the same level, no teacher, sitting across a table. One card per scene, read only your
own half of it, talk until the scene ends.

---

## 1. The one rule

**Each player has a goal, and the other player is in the way.**

That is the entire engine. Every scene is a version of it.

The failure this rule exists to prevent is the role-play that dies in thirty seconds. "You are in a
restaurant, order a meal" produces four lines and a silence, because nothing is at stake and nobody
has to work for anything. Give the waiter an empty kitchen and the customer fifteen euros and a
dietary rule, and neither of them can finish quickly.

**The collision test.** If both players could get everything they want, the scene has failed. Rewrite
it. There must be an obstacle on *each* side, not just one.

**The passive-role test.** If one card could be played by someone who simply answers questions, the
scene has failed. A waiter who only serves is not a role. Both players must want something.

**The secret should surface.** The hidden goals are hidden at the start so the scene has surprise in
it — not so it becomes a guessing game. Write them so they come out naturally in the talking. A
secret that can stay concealed to the end is a badly written secret.

---

## 2. Three shapes, one of each per unit

Every unit gets **at least three scenes**, and the first three are one of each shape. This is what
stops a unit from being three shopping scenes in a row.

| Tag | Shape | What it is | Typical settings |
|---|---|---|---|
| **T** | Transacción | One player wants a thing or a service, the other controls it | shop, restaurant, chemist, ticket desk, reception, job interview |
| **N** | Negociación | Both want incompatible things and must reach **one** agreement | flatmates, choosing a holiday, splitting the bill, which film, house rules |
| **S** | Social | Meeting, explaining, telling, apologising. No goods change hands | party, first day, running late, gossip, describing someone, bad news |

A fourth or fifth scene in a unit may repeat a shape.

**N is the one writers get wrong.** A negotiation needs a *single* outcome both must sign up to. "Talk
about your holidays" is not a negotiation. "You have one week and must choose **one** place, and you
hate the cold while your partner gets seasick" is.

---

## 3. What a scene is made of

Nine fields, in this order, exactly these labels. The builder parses them; the checker enforces them.

```
### <n> · <T|N|S> · <Título en español>

**Situación.** One or two sentences, Spanish, present tense. Place, time, who you two are.

**Papel A.** English. Who you are, what you want, what is in your way.

**Papel B.** English. Who you are, what you want, what is in your way.

**Termina.** The ending condition. Objective enough that you both know when you are done.

**Reto.** One extra challenge naming a structure this unit teaches.

**Hablar.** frase · frase · frase   (6–10 items, Spanish, separated by ' · ')

**Modelo.**
— A: …
— B: …

**Después.** Two questions, English.
```

### Why the roles are in English

Because a player who has to decode a paragraph of Spanish to find out who they are has spent their
effort on reading. The Spanish belongs in **Hablar** and **Modelo**, where it is the thing being
practised, and in **Situación**, which is short enough to take in at a glance.

### Termina

Objective, not a feeling. Good: *"B has ordered a primero, a segundo, a postre and a bebida that A
can actually serve."* Bad: *"when you have had a nice chat."* You should never have to ask whether
the scene is over.

### Reto

Names a structure from **this unit**, not a vague instruction. Good: *"Use me / te / le at least three
times."* Bad: *"Speak accurately."* It is what makes a scene worth replaying, and what aims it at the
grammar the unit is for.

### Hablar

6–10 chunks the scene actually needs — the question forms, the fixed phrases, the polite formulas.
Not a vocabulary list: the nouns are in the course book. These are the things a learner freezes for
want of, like *¿Me trae…?* or *Lo siento, no nos queda…*.

Both players see the same Hablar. Neither has to be the teacher.

### Modelo

8–14 turns showing one way the scene could go, **written to be read after playing, never before.**

Its job is not to be the right answer. At A1 the problem is usually not that you said it wrong, it is
that you did not know there was a better thing to say. A model read straight after you have struggled
is worth several read beforehand.

So: the model must show the collision being handled, not a frictionless version. If the waiter's
kitchen is empty, the model shows him saying so and offering something else. A model in which nothing
goes wrong teaches nothing about the scene that was played.

### Después

Two questions. The first asks what happened — *"Who got what they wanted?"*. The second asks about
the language — *"What is one thing you wanted to say and could not?"*. That second one is where the
next study session comes from.

---

## 4. Level

**Every Spanish word in Situación, Hablar and Modelo must already be taught by this unit.** Units 0..N
of the same level, plus all of A1 if the unit is A2. Nothing from a later unit, ever — a scene that
needs a tense the reader has not met is a scene they cannot play.

Check it with `check_level.py`, which builds the set of word forms the course book has actually
printed by that point and lists everything outside it. It is advisory, not a hard gate: it carries
noise in both directions, so **audit every flag and say in your report why each one is fine or how you
fixed it.** A proper noun is fine. A regular inflection of a taught headword is fine. A word from the
next unit is not.

The names may be reused across books — Sara, Pablo, Lucía, Nuria, Marta and the rest already live in
the workbook, and a familiar cast is a small free gift to the reader.

### Unit 0 is different

*En el aula* teaches `hay`, `tengo`, numbers 0–10, classroom objects, greetings and spelling. No
`ser`, no `estar`, no `pero`, no past, no `¿dónde?`. Its three scenes will be short and simple, and
that is correct, not a shortfall. Borrowing a pen, dividing up one desk, and a first day of spelling
your name at each other is the whole available range. Do not reach for grammar to make them richer.

---

## 5. Length and time

A scene should run **4–6 minutes** and be playable from the card with no preparation and no props.
Three scenes make a twenty-minute session, which is the length that actually gets done.

---

## 6. Files

One file per five units, mirroring the workbook's layout:

| File | Units |
|---|---|
| `game_part1.md` | A1 units 0, 1, 2, 3, 4 |
| `game_part2.md` | A1 units 5, 6, 7, 8, 9 |
| `game_part3.md` | A2 units 1, 2, 3, 4, 5 |
| `game_part4.md` | A2 units 6, 7, 8, 9, 10 |

Each unit opens with the heading the builder keys on:

```
## Unidad <n> — <Título del tema> {#nivel=A1 #unidad=<n>}
```

Take the title from `units.json`, so the game book, the course book and the workbook agree.

---

## 7. What the checker enforces

`check_games.py` fails on any of these, and it is the gate for "done":

1. Every unit in `units.json` is present, with at least three scenes.
2. The first three scenes of each unit are one **T**, one **N** and one **S**.
3. All nine fields present, in order, with the exact labels.
4. **Papel A** and **Papel B** both say what the player wants — the passive-role test, checked by
   requiring the word *want* or *need* in each.
5. `Hablar.` has 6–10 items.
6. `Modelo.` has 8–14 turns, and both players speak.
7. `Después.` has exactly two questions.
8. Scene numbers run 1, 2, 3, … inside a unit with no gaps.
9. No scene title is reused within a level.
