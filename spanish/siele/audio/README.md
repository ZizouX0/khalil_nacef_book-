# Audio for the SIELE booklet

Exam-style MP3 tracks for the booklet's **original** listening and speaking practice
(`src/03_CA.md` exercises 1–5, `src/05_EIO.md` Tarea 1 questions). Each track has the
exam rhythm built in: instruction, 30 s to read, every audio twice (5 s apart), 10 s to
answer; track 06 asks the speaking questions and marks your answer time with beeps.

| Track | Content | Use with |
|---|---|---|
| 01 | Tarea 1 · conversation | Listening, Ejercicio 1 |
| 02 | Tarea 2 · five radio ads | Listening, Ejercicio 2 |
| 03 | Tarea 3 · Set A, un viaje | Listening, Ejercicio 3 |
| 04 | Tarea 3 · Set B, el primer día | Listening, Ejercicio 4 |
| 05 | Numbers, times, prices | Listening, Ejercicio 5 |
| 06 | Speaking Tarea 1 simulator (15/15/30/30 s) | Speaking, Tarea 1 Series A and B |

Generated with `make_audio.py` and [Piper](https://github.com/rhasspy/piper) voices from
`rhasspy/piper-voices` (es_ES davefx, es_ES sharvard, es_MX ald, es_MX claude, es_AR daniela);
each voice's licence is in its model card there.
