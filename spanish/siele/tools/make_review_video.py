#!/usr/bin/env python3
"""Build the SIELE full review video (all four tests, about 12 minutes).

An English narrator explains the strategy for each test; Spanish voices read
the key phrases, each followed by a pause for the student to repeat it.
Slides are HTML rendered with Playwright; segments are encoded with ffmpeg
and concatenated.

    python3 make_review_video.py VOICES_DIR WORK_DIR OUT.mp4
    (VOICES_DIR holds the Spanish Piper voices and en_US-lessac-medium)
"""
import html
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np
from piper import PiperVoice, SynthesisConfig

VOICES, WORK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "assets", "fonts")
SR = 22050
W, H, FPS = 1280, 720, 10
for d in ("slides", "seg"):
    os.makedirs(os.path.join(WORK, d), exist_ok=True)

EN = ("en_US-lessac-medium", None)        # English narrator: explanations
ES_NARR = ("es_ES-sharvard-medium", 1)    # Spanish woman: "escucha y repite"
ES = ("es_ES-davefx-medium", None)        # Spanish man: the student's phrases
_cache = {}


def voice(name):
    if name not in _cache:
        _cache[name] = PiperVoice.load(os.path.join(VOICES, name + ".onnx"))
    return _cache[name]


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.int16)


def plain(t):
    t = re.sub(r"\*\*|__", "", t)
    return re.sub(r"\s+", " ", t.replace("«", "").replace("»", "")).strip()


def say(text, who=EN, scale=1.0, pause=0.4):
    model, spk = who
    cfg = SynthesisConfig(speaker_id=spk, length_scale=scale)
    out = []
    for c in voice(model).synthesize(plain(text), cfg):
        out += [c.audio_int16_array, silence(pause)]
    return np.concatenate([silence(0.3)] + out[:-1] + [silence(0.5)])


# ---------------------------------------------------------------- slides
COLORS = {"intro": "#1F3A5F", "read": "#2563EB", "listen": "#0891B2", "write": "#EA580C",
          "speak": "#059669", "traps": "#DC2626", "end": "#1F3A5F"}
NAMES = {"intro": "SIELE · repaso final", "read": "📖 Comprensión de lectura",
         "listen": "🎧 Comprensión auditiva", "write": "✍️ Expresión escrita",
         "speak": "🗣️ Expresión oral", "traps": "⚠️ Tus trampas", "end": "💪 Mañana"}
CSS = f"""
@font-face{{font-family:Nunito;font-weight:800;src:url('file://{FONTS}/Nunito-800.ttf')}}
@font-face{{font-family:Nunito;font-weight:900;src:url('file://{FONTS}/Nunito-900.ttf')}}
@font-face{{font-family:Atk;font-weight:400;src:url('file://{FONTS}/AtkinsonHyperlegible-Regular.ttf')}}
@font-face{{font-family:Atk;font-weight:700;src:url('file://{FONTS}/AtkinsonHyperlegible-Bold.ttf')}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;background:#FFFBF2;font-family:Atk,sans-serif;color:#1E293B;overflow:hidden}}
.bar{{height:84px;background:var(--c);color:#fff;display:flex;align-items:center;padding:0 40px;
     font-family:Nunito;font-weight:900;font-size:32px}}
.main{{padding:22px 60px 0}}
h1{{font-family:Nunito;font-weight:900;font-size:58px;color:var(--c);margin:56px 0 10px}}
h2{{font-family:Nunito;font-weight:900;font-size:40px;color:var(--c);margin:8px 0 20px}}
.sub{{font-size:28px;color:#475569;margin-bottom:30px}}
.chips{{display:flex;flex-direction:column;gap:13px}}
.chip{{font-size:27px;background:#fff;border-left:10px solid var(--c);border-radius:12px;padding:11px 20px;
      box-shadow:0 2px 6px rgba(0,0,0,.08)}}
.pts{{list-style:none;display:flex;flex-direction:column;gap:14px}}
.pts li{{font-size:28px;line-height:1.3;background:#fff;border-radius:12px;padding:12px 20px;
        box-shadow:0 2px 6px rgba(0,0,0,.07)}}
.pts.dense{{gap:9px}}
.pts.dense li{{font-size:24px;padding:9px 18px}}
.pts b,.chip b,.card b{{color:var(--c)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.grid.three{{grid-template-columns:1fr 1fr 1fr}}
.card{{background:#fff;border-radius:14px;padding:14px 18px;border-top:8px solid var(--c);
      box-shadow:0 2px 8px rgba(0,0,0,.08);font-size:23px;line-height:1.3}}
.card .t{{font-family:Nunito;font-weight:900;font-size:27px;color:var(--c);margin-bottom:4px}}
.pill{{display:inline-block;margin:24px 40px 0;padding:8px 22px;border-radius:999px;background:var(--c);
      color:#fff;font-family:Nunito;font-weight:900;font-size:26px}}
.pill.soft{{background:#E2E8F0;color:#334155}}
.es{{font-family:Nunito;font-weight:800;font-size:48px;line-height:1.25;margin-top:36px}}
.en{{font-size:28px;color:#64748B;margin-top:20px}}
.tip{{margin-top:26px;font-size:26px;background:#FEF3C7;border-radius:12px;padding:12px 20px;display:inline-block}}
.count{{position:absolute;right:60px;bottom:28px;font-size:22px;color:#94A3B8;font-family:Nunito;font-weight:800}}
"""


def md(t):
    t = html.escape(t)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)


SEGS, _n = [], [0]


def seg(sec, body, audio, chapter=None):
    _n[0] += 1
    name = f"r{_n[0]:03d}"
    with open(os.path.join(WORK, "slides", name + ".html"), "w") as f:
        f.write(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
                f"<body style='--c:{COLORS[sec]}'><div class='bar'>{NAMES[sec]}</div>{body}</body></html>")
    SEGS.append(dict(name=name, audio=audio, chapter=chapter))


def title(sec, heading, sub, chips, narration, chapter=None):
    body = (f"<div class='main'><h1>{md(heading)}</h1><div class='sub'>{md(sub)}</div><div class='chips'>"
            + "".join(f"<div class='chip'>{md(c)}</div>" for c in chips) + "</div></div>")
    seg(sec, body, np.concatenate([say(narration), silence(1.0)]), chapter=chapter or heading)


def points(sec, heading, items, narration, chapter=None):
    dense = " dense" if len(items) > 5 else ""
    body = (f"<div class='main'><h2>{md(heading)}</h2><ul class='pts{dense}'>"
            + "".join(f"<li>{md(i)}</li>" for i in items) + "</ul></div>")
    seg(sec, body, np.concatenate([say(narration), silence(1.0)]), chapter=chapter)


def grid(sec, heading, cards, narration, cols=2):
    body = (f"<div class='main'><h2>{md(heading)}</h2><div class='grid{' three' if cols == 3 else ''}'>"
            + "".join(f"<div class='card'><div class='t'>{md(t)}</div>{md(x)}</div>" for t, x in cards)
            + "</div></div>")
    seg(sec, body, np.concatenate([say(narration), silence(1.0)]))


def phrases(sec, items, intro_en):
    seg(sec, "<span class='pill'>🔊 Escucha y repite</span><div class='main'><div class='es'>"
        "Escucha cada frase.<br>Luego, repítela en voz alta.</div></div>",
        np.concatenate([say(intro_en), say("Escucha y repite.", ES_NARR, 1.05)]))
    for i, (es, en, tip) in enumerate(items, 1):
        a = say(es, ES, 1.12)

        def body(mode):
            pill = ("<span class='pill'>🔊 Escucha</span>" if mode == "listen"
                    else "<span class='pill soft'>🎙️ Repite en voz alta</span>")
            return (pill + f"<div class='main'><div class='es'>{md(es)}</div><div class='en'>{md(en)}</div>"
                    + (f"<div class='tip'>💡 {md(tip)}</div>" if tip else "")
                    + f"</div><div class='count'>{i} / {len(items)}</div>")
        seg(sec, body("listen"), a)
        seg(sec, body("repeat"), silence(max(3.0, len(a) / SR * 1.2 + 0.8)))


# ================================================================ CONTENT
title("intro", "Tu SIELE en 10 minutos", "Reading · Listening · Writing · Speaking · tomorrow: B1",
      ["🎯 B1 code: **18 · 18 · 3 · 125**",
       "📖 Reading **18/38** · you have 23 ✅ · 🎧 Listening **18/38** · you have 28 ✅",
       "✍️ Writing: Tarea 1 at **band 3** + always write Tarea 2",
       "🗣️ Speaking: **125/250** · you have about 140 ✅"],
      "Welcome to your final review for the see-EH-leh exam. Tomorrow your goal is B1. Remember the code: eighteen, eighteen, "
      "three, one hundred twenty five. Eighteen correct answers in reading, eighteen in listening, band three "
      "in writing task one, and one hundred and twenty five points in speaking. Your practice tests already "
      "show these levels. Now let's review everything, test by test.", chapter="Intro")
points("intro", "The 3 golden rules", [
    "📝 **Never leave a blank** in reading and listening. A guess can't lose points.",
    "✅ **Tick every point** in writing and speaking. Task completion is about a third of the mark.",
    "⏱️ **Use all the time** and keep going when it gets hard. The tasks go from A1 to C1."],
    "Three golden rules for the whole exam. One: never leave a blank in reading and listening. A guess can "
    "never lose points. Two: in writing and speaking, cover every point of the task. Task completion is about "
    "a third of your mark. Three: use all the time, and keep going when it gets hard. The last tasks are meant "
    "to be difficult.")

# ---- Reading
title("read", "Lectura · 60 min · 5 tareas", "38 questions · 18 = B1",
      ["🐢 **Tareas 1 to 3 = your B1** → go slowly, read every option",
       "⏳ **Tareas 4 and 5 = bonus** → 10 minutes maximum, then guess",
       "🔎 Find the answer **in the text** before you look at the options"],
      "Reading. Sixty minutes, five tasks. Tasks one to three give you your B1, so take your time there and "
      "read every option carefully. Tasks four and five are bonus points: give them ten minutes maximum, then "
      "guess. A good habit: find the answer in the text first, then look at the options.", chapter="Reading")
grid("read", "The 6 suspects · how wrong answers trick you", [
    ("🦜 Loro", "repeats the text's **words**, but the meaning is different"),
    ("🎭 Impostor", "it's true, but it **doesn't answer** the question"),
    ("🧳 Viajero", "it comes from **another part** of the text or another person"),
    ("🔍 Zoom", "**too general** or **too specific**"),
    ("🙃 Don Contrario", "says the **opposite**: *no, nunca, sin, ya no*"),
    ("👯 Gemelo", "two options look the same: find the **small difference**")],
    "Wrong answers hide in six ways. The Parrot repeats words from the text, but the meaning is different. "
    "The Impostor is true, but it does not answer the question. The Traveller comes from another part of the "
    "text. Zoom is too general or too specific. Mister Opposite says the contrary, with words like no, never "
    "or without. And the Twins are two options that look the same: look for the small difference.")
points("read", "Tarea 4 · GANCHO · the hooks around the gap", [
    "👀 Read the words **before and after** the gap, not the topic",
    "👉 Pointing words: *esto · este · **esta medida** · allí · él* → what do they point to?",
    "🔗 Connectors: *también · además · sin embargo · por eso*",
    "💬 Quotes «…» or *opina* → the fragment must be an **opinion**",
    "🧩 The fragment left over is **el Colado**, the decoy"],
    "Task four, the missing fragments. Do not place fragments by topic. Look at the words just before and "
    "after the gap. Pointing words like this, this measure, there or he must point to something. Connectors "
    "like also, however or that's why must make sense. If you see quotation marks or the verb opina, the "
    "fragment must be an opinion. And one fragment is always left over: that's the decoy.")

# ---- Listening
title("listen", "Auditiva · 55 min · 6 tareas", "38 questions · 18 = B1 · you have 28 = B2 ✅",
      ["👀 Read the options **before** the audio starts",
       "1️⃣ First play: answer · 2️⃣ second play: **confirm**",
       "📝 Never leave a blank"],
      "Listening. Fifty five minutes, six tasks. You are already at B2 here, so just stay calm. Always read the "
      "options before the audio starts. On the first play, answer. On the second play, confirm or change. "
      "And never leave a blank.", chapter="Listening")
points("listen", "Tarea 3 · the hard one · 3 questions in your head", [
    "🙋 **¿Quién?** Who says it? Match the **person**, not the topic",
    "⚠️ **¿Pero…?** The real answer often comes **after pero / sin embargo**",
    "😊 **¿Qué tal?** Listen to the **tone**: happy, angry, surprised",
    "🦜 A word you hear is **not automatically** the answer"],
    "Task three is the hardest. Keep three questions in your head. Who says it? Match the person, not the "
    "topic. But? The real answer often comes after pero or sin embargo. And how does it sound? Listen to the "
    "tone: happy, angry or surprised. Remember: a word you hear in the audio is not automatically the answer.")

# ---- Writing
title("write", "Escrita · 50 min · 2 tareas", "Tarea 1 = your B1 · Tarea 2 = +25 points",
      ["⏱️ Tarea 1: **25 min** · Tarea 2: **20 min** · proofread: **5 min**",
       "✉️ Tarea 1: **100–150 words** · Tarea 2: **250+ words**",
       "🚫 **Never skip Tarea 2**: even simple, it adds about 25 points"],
      "Writing. Fifty minutes for two tasks. Twenty five minutes for task one, twenty for task two, and five "
      "minutes to check. Task one gives you your B1. Never skip task two: even a simple text with your template "
      "adds about twenty five points.", chapter="Writing")
points("write", "Tarea 1 · 5 steps", [
    "1️⃣ **Count the *y*:** number the 9–10 things and tick each one",
    "2️⃣ **tú or usted?** Check the **name** in the task",
    "3️⃣ Hello → why → **one paragraph per point** → goodbye",
    "4️⃣ Past: ***fui, vi, tuve*** (events) + ***era, tenía, hacía*** (descriptions)",
    "5️⃣ Last 3 minutes: **capitals · accents · your words** (*señor, anuncio, muy, mensaje*)"],
    "Task one in five steps. One: count every y in the instructions and number the things you must write. "
    "Missing points cost you up to twenty points. Two: decide tú or usted, and check the name. Three: hello, "
    "why you are writing, one paragraph per point, goodbye. Four: in the past, use fui, vi, tuve for events, "
    "and era, tenía, hacía for descriptions. Five: in the last three minutes, check capitals, accents and the "
    "words you often misspell.")
phrases("write", [
    ("He leído tu mensaje y ¡qué buena noticia!", "I've read your message, what great news!", "Tarea 1 · tú"),
    ("Le escribo porque he visto su anuncio.", "I'm writing because I saw your ad.", "Tarea 1 · usted"),
    ("Lo que más me gusta es la playa, porque es muy tranquila.",
     "What I like most is the beach, because it's very quiet.", "likes + porque"),
    ("El verano pasado fui a Madrid. Hacía sol y fue genial.",
     "Last summer I went to Madrid. It was sunny and it was great.", "past: fui + hacía"),
    ("Espero que te guste. ¡Escríbeme pronto! Un abrazo.", "I hope you like it. Write soon! Hugs.", "goodbye"),
], "Now repeat the key phrases for writing task one. Listen, then say each phrase aloud.")
points("write", "Tarea 2 · your template · any topic", [
    "📰 *Hoy en día se habla mucho de… · Es un tema muy importante porque nos afecta a todos.*",
    "💭 *En mi opinión, es algo positivo, pero solo si… · El problema no es…, sino…*",
    "⚖️ *Por un lado, es verdad que… Por otro lado, el problema principal es que… Por ejemplo, en mi país…*",
    "🛠️ *La solución no es fácil, pero hay cosas que podemos hacer. … deberían… Además, habría que…*",
    "🏁 *En conclusión, creo que… Es importante que todos hagamos algo.*",
    "✉️ Letter? Start ***Señor director: Le escribo en relación con…*** · end ***Atentamente,***"],
    "Task two: your template works for any topic. Start with: nowadays people talk a lot about. Give your "
    "opinion. Then on one hand, on the other hand, and an example from your country. Then the solution: "
    "should, and it would be necessary to. Finish with in conclusion. If it's a letter, start with Señor "
    "director, and end with Atentamente.")
phrases("write", [
    ("Hoy en día se habla mucho de este tema.", "Nowadays people talk a lot about this topic.", "start"),
    ("Es un tema muy importante porque nos afecta a todos.", "It's very important because it affects us all.",
     "start"),
    ("Por un lado, es verdad que es útil. Por otro lado, el problema principal es que es caro.",
     "On one hand it's useful. On the other hand, the main problem is that it's expensive.", "both sides"),
    ("La solución no es fácil, pero hay cosas que podemos hacer.",
     "The solution isn't easy, but there are things we can do.", "solutions"),
    ("En conclusión, creo que es importante que todos hagamos algo.",
     "In conclusion, I think it's important that we all do something.", "never forget the conclusion"),
], "Now repeat your task two template.")

# ---- Speaking
title("speak", "Oral · 5 tareas · 125 = B1", "about 20 minutes · all recorded",
      ["⏱️ Use the **preparation time** · start speaking when the recording starts",
       "🖐️ Finger trick: 15 s = **2 sentences** · 30 s = **4 sentences**",
       "🤫 Never silent: *Pues… A ver… La verdad es que…*"],
      "Speaking. Five tasks, about twenty minutes, all recorded. Use the preparation time. Use the finger "
      "trick: fifteen seconds means two sentences, thirty seconds means four. And never stay silent: say pues, "
      "a ver, la verdad es que.", chapter="Speaking")
grid("speak", "The 5 tareas · 5 formulas", [
    ("1 · Preguntas", "**HOY · HOY · AYER · MAÑANA** · copy the question's verb · end with a feeling"),
    ("2 · La foto", "**PASEO** · clothes 40 s max · say **where** they are · *Me encanta esta foto porque…*"),
    ("3 · Mensajes", "**SÁNDWICH** · *Te dejo este mensaje porque…* · find your situation box · bye by **1:15**"),
    ("4 · Texto", "**sí / no → porque → por ejemplo → por eso** · answer **all 3** questions"),
    ("5 · Opinión", "*Estoy de acuerdo solo en parte* · reasons · example · **conclusion**"),
    ("🎯 Your scores", "T1 ≈ 33 · T2 ≈ 34 · T3 ≈ 35 · T4 ≈ 28 · T5 ≈ 25 → **≈ 150 = B1** ✅")],
    "Five tasks, five formulas. Task one: today, today, yesterday, tomorrow, and copy the verb of the question. "
    "Task two: PASEO, people, appearance, what's happening, where, and objects, then your ending sentence. "
    "Task three: the sandwich. Start with te dejo este mensaje porque, find your situation, and say goodbye "
    "before one minute fifteen. Task four: yes or no, because, for example, that's why. Answer all three "
    "questions. Task five: I only partly agree, then reasons, an example, and a conclusion. Your practice "
    "scores add up to about one hundred and fifty. That's B1.", cols=3)
phrases("speak", [
    ("Te dejo este mensaje porque necesito tu ayuda.", "I'm leaving you this message because I need your help.",
     "Tarea 3 · safe opening"),
    ("¿Me podrías ayudar? ¿Qué te parece si quedamos el sábado?", "Could you help me? How about Saturday?",
     "**ME** first"),
    ("En la foto se ven tres personas. Me parece que son una familia.",
     "In the photo you can see three people. I think they're a family.", "Tarea 2"),
    ("Me encanta esta foto porque me recuerda a mi familia.", "I love this photo because it reminds me of my family.",
     "Tarea 2 · ending"),
    ("Es una buena pregunta. En mi opinión, sí, porque es muy útil.",
     "That's a good question. In my opinion, yes, because it's very useful.", "Tarea 4"),
    ("Yo estoy de acuerdo solo en parte.", "I only partly agree.", "Tarea 5"),
], "Now repeat the key phrases for speaking.")

# ---- Traps
points("traps", "Your 5 traps · from your own texts and recordings", [
    "📍 WHERE → **está** · what it's like → **es / era** · weather → **hacía**",
    "👉 ***¿ME podrías…?*** · ***te LLAMO***, not *te amo*",
    "♂️ **el** planeta · **el** problema · **el** tema · agreement: camiseta blanc**a**",
    "👥 **tú OR usted**, never both · reuse **the task's words** and **the name**",
    "⏱️ **Use all the time:** 13 s · 28 s · 1:15 · 1:50"],
    "Finally, your five personal traps. One: for places, use está. For what something is like, es or era. "
    "For the weather, hacía. Two: the pronoun goes first: me podrías. And say te llamo clearly. Three: planeta, "
    "problema and tema are masculine, and check your adjectives. Four: tú or usted, never both, and reuse the "
    "words of the task. Five: use all the time you have.", chapter="Your traps")
phrases("traps", [
    ("El restaurante está muy cerca de mi casa.", "The restaurant is very close to my house.", "WHERE → **está**"),
    ("Cuando era pequeño, mi casa era grande y en invierno hacía frío.",
     "When I was little, my house was big and in winter it was cold.", "**era** · **hacía**"),
    ("¿Me podrías preparar una tarta?", "Could you make me a cake?", "**ME** first"),
    ("Te llamo porque tengo un problema.", "I'm calling because I have a problem.", "te **YA**-mo · **un** problema"),
    ("Lleva una camiseta blanca y unos pantalones negros.", "He's wearing a white T-shirt and black trousers.",
     "agreement"),
], "Repeat the correct forms.")

# ---- Exam day
title("end", "Mañana · el examen", "Nothing new today. Trust your practice.",
      ["☀️ Breakfast · water · **ID / passport** · arrive **30 min early**",
       "📖🎧 No blanks · Tareas 4–5: 10 min max, then guess",
       "✍️ Number the points · **always write Tarea 2** · 3-minute proofread",
       "🗣️ Prep time · 2 or 4 sentences · goodbye by 1:15 · *te llamo*",
       "💪 **You are ready for B1.** ¡Mucha suerte!"],
      "Tomorrow. Have breakfast, bring water and your ID, and arrive thirty minutes early. In reading and "
      "listening, no blanks. In writing, number the points, always write task two, and proofread. In speaking, "
      "use the preparation time and fill the clock. Your practice tests say B1. You are ready. Good luck!",
      chapter="Exam day")

# ================================================================ RENDER
listing = [[os.path.join(WORK, "slides", s["name"] + ".html"),
            os.path.join(WORK, "slides", s["name"] + ".png")] for s in SEGS]
with open(os.path.join(WORK, "slides.json"), "w") as f:
    json.dump(listing, f)
js = os.path.join(WORK, "shot.js")
with open(js, "w") as f:
    f.write("""const { chromium } = require('playwright');
const list = require(process.argv[2]);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: %d, height: %d }, deviceScaleFactor: 1 });
  for (const [h, o] of list) {
    await p.goto('file://' + h);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: o });
  }
  await b.close();
})();
""" % (W, H))
subprocess.run(["node", js, os.path.join(WORK, "slides.json")], check=True)

chapters, t = [], 0.0
lst = os.path.join(WORK, "concat.txt")
with open(lst, "w") as L:
    for s in SEGS:
        wav = os.path.join(WORK, "seg", s["name"] + ".wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(s["audio"].tobytes())
        dur = len(s["audio"]) / SR
        if s["chapter"]:
            chapters.append((t, s["chapter"]))
        t += dur
        mp4 = os.path.join(WORK, "seg", s["name"] + ".mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS),
                        "-i", os.path.join(WORK, "slides", s["name"] + ".png"), "-i", wav,
                        "-c:v", "libx264", "-tune", "stillimage", "-crf", "26", "-pix_fmt", "yuv420p",
                        "-r", str(FPS), "-g", "50", "-c:a", "aac", "-b:a", "64k", "-ar", str(SR), "-ac", "1",
                        "-t", f"{dur:.3f}", mp4], check=True)
        L.write(f"file '{mp4}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                "-movflags", "+faststart", OUT], check=True)
for c, name in chapters:
    print(f"{int(c // 60)}:{int(c % 60):02d}  {name}")
print(f"total {int(t // 60)}:{int(t % 60):02d}  segments {len(SEGS)}")
