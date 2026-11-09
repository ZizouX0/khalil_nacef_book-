#!/usr/bin/env python3
"""Build the SIELE speaking revision video (slides + Piper voices + timers).

For each speaking tarea: a title card, "listen and repeat" phrases, then an
exam simulator (question -> think timer -> beep -> speak timer -> beep) and a
model answer. Slides are HTML rendered with Playwright; the countdown is drawn
by ffmpeg; segments are encoded separately and concatenated.

    python3 make_video.py VOICES_DIR WORK_DIR OUT.mp4
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
SIELE = os.path.dirname(HERE)
FONTS = os.path.join(os.path.dirname(SIELE), "assets", "fonts")
PHOTO = os.path.join(SIELE, "photos_speaking", "p2a.jpg")   # public domain
SR = 22050
W, H, FPS = 1280, 720, 10
os.makedirs(os.path.join(WORK, "slides"), exist_ok=True)
os.makedirs(os.path.join(WORK, "seg"), exist_ok=True)

# ---------------------------------------------------------------- voices
NARR = ("es_ES-sharvard-medium", 1)     # woman, standard Spain: instructions
STUDENT = ("es_ES-davefx-medium", None)  # man: phrases and model answers
ASK = [("es_MX-claude-high", None), ("es_AR-daniela-high", None)]
_cache = {}


def voice(name):
    if name not in _cache:
        _cache[name] = PiperVoice.load(os.path.join(VOICES, name + ".onnx"))
    return _cache[name]


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.int16)


def beep():
    t = np.arange(int(SR * 0.35)) / SR
    env = np.minimum(1, np.minimum(t, t[::-1]) * 40)
    return (np.sin(2 * np.pi * 880 * t) * env * 6000).astype(np.int16)


def plain(t):
    t = re.sub(r"\*\*|__", "", t)
    return re.sub(r"\s+", " ", t.replace("«", "").replace("»", "")).strip()


def say(text, who=NARR, scale=1.05, pause=0.45):
    model, spk = who
    cfg = SynthesisConfig(speaker_id=spk, length_scale=scale)
    out = []
    for c in voice(model).synthesize(plain(text), cfg):
        out += [c.audio_int16_array, silence(pause)]
    return np.concatenate([silence(0.3)] + out[:-1] + [silence(0.4)])


# ---------------------------------------------------------------- slides
COLORS = {"intro": "#1F3A5F", "1": "#2563EB", "2": "#059669", "3": "#EA580C",
          "4": "#7C3AED", "5": "#DC2626", "end": "#1F3A5F"}
NAMES = {"intro": "Expresión oral", "1": "Tarea 1 · Preguntas", "2": "Tarea 2 · La foto",
         "3": "Tarea 3 · Mensajes", "4": "Tarea 4 · Texto y preguntas",
         "5": "Tarea 5 · Tu opinión", "end": "¡Mucha suerte!"}
CSS = f"""
@font-face{{font-family:Nunito;font-weight:800;src:url('file://{FONTS}/Nunito-800.ttf')}}
@font-face{{font-family:Nunito;font-weight:900;src:url('file://{FONTS}/Nunito-900.ttf')}}
@font-face{{font-family:Atk;font-weight:400;src:url('file://{FONTS}/AtkinsonHyperlegible-Regular.ttf')}}
@font-face{{font-family:Atk;font-weight:700;src:url('file://{FONTS}/AtkinsonHyperlegible-Bold.ttf')}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;background:#FFFBF2;font-family:Atk,sans-serif;color:#1E293B;overflow:hidden}}
.bar{{height:90px;background:var(--c);color:#fff;display:flex;align-items:center;padding:0 40px;
     font-family:Nunito;font-weight:900;font-size:34px;gap:18px}}
.bar small{{font-size:18px;font-weight:800;opacity:.85}}
.clock{{position:absolute;right:40px;top:12px;width:200px;height:66px;border-radius:16px;
       background:#0F172A;border:3px solid #fff}}
.pill{{display:inline-block;margin:26px 40px 0;padding:8px 22px;border-radius:999px;background:var(--c);
      color:#fff;font-family:Nunito;font-weight:900;font-size:26px}}
.pill.soft{{background:#E2E8F0;color:#334155}}
.main{{padding:18px 60px 0}}
h1{{font-family:Nunito;font-weight:900;font-size:64px;color:var(--c);margin:70px 0 10px}}
.sub{{font-size:28px;color:#475569;margin-bottom:34px}}
.chips{{display:flex;flex-direction:column;gap:14px}}
.chip{{font-size:27px;background:#fff;border-left:10px solid var(--c);border-radius:12px;padding:12px 20px;
      box-shadow:0 2px 6px rgba(0,0,0,.08)}}
.es{{font-family:Nunito;font-weight:800;font-size:50px;line-height:1.25;margin-top:40px}}
.en{{font-size:28px;color:#64748B;margin-top:22px}}
.tip{{margin-top:30px;font-size:26px;background:#FEF3C7;border-radius:12px;padding:12px 20px;display:inline-block}}
.count{{position:absolute;right:60px;bottom:30px;font-size:22px;color:#94A3B8;font-family:Nunito;font-weight:800}}
.q{{font-family:Nunito;font-weight:900;font-size:52px;line-height:1.25;margin-top:44px}}
.task{{font-size:28px;line-height:1.5;margin-top:26px}}
.task li{{margin-left:36px}}
.model{{font-size:31px;line-height:1.5;margin-top:18px}}
.two .model{{font-size:22px;margin-top:0}}
.model b{{color:var(--c)}}
.two{{display:flex;gap:34px;align-items:flex-start}}
.two img{{width:440px;border-radius:14px;box-shadow:0 4px 14px rgba(0,0,0,.2)}}
.paseo{{font-size:27px;line-height:1.75}}
.paseo b{{color:var(--c);font-family:Nunito;font-weight:900}}
.credit{{position:absolute;left:60px;bottom:24px;font-size:17px;color:#94A3B8}}
"""


def md(t):
    t = html.escape(t)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


def page(sec, body, clock=False):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
            f"<body style='--c:{COLORS[sec]}'><div class='bar'>{NAMES[sec]} <small>· SIELE</small></div>"
            + ("<div class='clock'></div>" if clock else "") + body + "</body></html>")


# ---------------------------------------------------------------- timeline
SEGS = []          # dicts: html, audio(np), countdown(None|secs), chapter
_n = [0]


def seg(sec, body, audio, clock=None, chapter=None):
    _n[0] += 1
    name = f"s{_n[0]:03d}"
    with open(os.path.join(WORK, "slides", name + ".html"), "w") as f:
        f.write(page(sec, body, clock is not None))
    SEGS.append(dict(name=name, audio=audio, clock=clock, chapter=chapter))


def title(sec, heading, sub, chips, narration):
    body = (f"<div class='main'><h1>{md(heading)}</h1><div class='sub'>{md(sub)}</div><div class='chips'>"
            + "".join(f"<div class='chip'>{md(c)}</div>" for c in chips) + "</div></div>")
    seg(sec, body, np.concatenate([say(narration), silence(1.5)]), chapter=heading)


def phrases(sec, items):
    seg(sec, "<span class='pill'>🔊 Escucha y repite</span><div class='main'><div class='es'>"
        "Escucha cada frase.<br>Luego, repítela en voz alta.</div></div>", say("Escucha y repite."))
    for i, (es, en, tip) in enumerate(items, 1):
        a = say(es, STUDENT, 1.15)
        def body(mode):
            pill = ("<span class='pill'>🔊 Escucha</span>" if mode == "listen"
                    else "<span class='pill soft'>🎙️ Repite en voz alta</span>")
            return (pill + f"<div class='main'><div class='es'>{md(es)}</div><div class='en'>{md(en)}</div>"
                    + (f"<div class='tip'>💡 {md(tip)}</div>" if tip else "")
                    + f"</div><div class='count'>{i} / {len(items)}</div>")
        seg(sec, body("listen"), a)
        seg(sec, body("repeat"), silence(max(3.0, len(a) / SR * 1.3 + 0.8)))


def countdown(sec, body_fn, secs, mode):
    """mode: think / prepare (silent) or speak (beep at start and end)."""
    if mode == "speak":
        a = np.concatenate([beep(), silence(secs - 0.7), beep()])
    else:
        a = silence(secs)
    seg(sec, body_fn(mode), a, clock=secs)


PILLS = {"think": "<span class='pill soft'>🧠 Piensa</span>",
         "prepare": "<span class='pill soft'>📝 Prepara</span>",
         "speak": "<span class='pill'>🎙️ ¡Habla ahora!</span>"}


def model(sec, text, intro="Ahora escucha una respuesta modelo.", photo=False):
    a = np.concatenate([say(intro), say(text, STUDENT, 1.08)])
    txt = f"<div class='model'>{md(text)}</div>"
    if photo:
        txt = f"<div class='two'><img src='file://{PHOTO}'>{txt}</div>"
    seg(sec, f"<span class='pill'>✅ Respuesta modelo</span><div class='main'>{txt}</div>", a)


def question(sec, q, think, speak, ans, who):
    qa = say(q, who, 1.05)
    qbody = lambda mode: (PILLS.get(mode, "<span class='pill soft'>🔊 Pregunta</span>")
                          + f"<div class='main'><div class='q'>{md(q)}</div>"
                          + f"<div class='en'>Tienes {speak} segundos.</div></div>")
    seg(sec, qbody("ask"), qa)
    countdown(sec, qbody, think, "think")
    countdown(sec, qbody, speak, "speak")
    model(sec, ans)


# ================================================================ CONTENT
title("intro", "Repaso de la prueba oral",
      "SIELE · speaking revision · all 5 tareas",
      ["🔁 **Repeat** every phrase aloud", "🎙️ **Answer** when the timer runs (record yourself!)",
       "✅ **Compare** with the model answer", "⭐ Bold = phrases you can use in ANY topic"],
      "Vamos a repasar la prueba de expresión oral. Escucha cada frase y repítela en voz alta. "
      "Después, contesta cuando veas el reloj.")

# ---- Tarea 1
title("1", "Tarea 1 · 4 preguntas", "Personal questions · present, past, future",
      ["⏱️ 15 · 15 · 30 · 30 seconds", "📅 HOY · HOY · AYER · MAÑANA",
       "🗣️ 15 s = **2 sentences** · 30 s = **4 sentences**", "❤️ Finish with a feeling: **¡Fue genial!**"],
      "Tarea uno. Cuatro preguntas sobre ti. Quince segundos para las dos primeras, "
      "y treinta segundos para las otras dos.")
phrases("1", [
    ("Vivo en Kelibia, una ciudad pequeña en el norte de Túnez. Está al lado del mar.",
     "I live in Kelibia, a small town in the north of Tunisia. It's by the sea.", "WHERE → **está**"),
    ("Mi comida favorita es la lasaña. Mi madre la hace muy rica.",
     "My favourite food is lasagne. My mother makes it really tasty.", "food is **rica**, not bonita"),
    ("Cuando era pequeño, mi casa era grande y estaba en el campo.",
     "When I was little, my house was big and it was in the countryside.",
     "what it was like → **era** · where → **estaba**"),
    ("En invierno hacía mucho frío y jugaba al fútbol con mis amigos.",
     "In winter it was very cold and I played football with my friends.", "weather → **hacía** · jugar **al**"),
    ("Este fin de semana he ido al cine con mis amigos. ¡Ha sido genial!",
     "This weekend I went to the cinema with my friends. It was great!", "¿Qué **ha** hecho? → **He** ido"),
    ("El año que viene voy a hacer un máster en España. ¡Tengo muchas ganas!",
     "Next year I'm going to do a master's in Spain. I can't wait!", "future → **voy a** + infinitive"),
])
seg("1", "<span class='pill'>🎙️ Ahora tú</span><div class='main'><div class='es'>Escucha la pregunta y piensa.<br>"
    "Después de la señal, contesta.</div><div class='en'>Record yourself on your phone.</div></div>",
    say("Ahora tú. Escucha la pregunta y piensa. Después de la señal, contesta."))
question("1", "¿Qué deporte practica?", 10, 15,
         "**Juego al pádel** desde hace tres meses con mis amigos. Vamos a un club nuevo en el centro "
         "de la ciudad. **¡Me encanta!**", ASK[0])
question("1", "¿Cómo era su casa cuando era pequeño?", 10, 30,
         "**Cuando era pequeño, mi casa era** grande y **estaba en** el campo. **Tenía** una terraza con muchas "
         "plantas y un jardín. **Me encantaba** jugar en el jardín con mis amigos. **¡Era una casa fenomenal!**",
         ASK[1])

# ---- Tarea 2
title("2", "Tarea 2 · Describe una foto", "Up to 2 minutes · follow PASEO",
      ["📸 **P**ersonas · **A**specto y ropa · **S**ucede · **E**n qué lugar · **O**bjetos",
       "⏳ 10 s · **40 s** · 15 s · 15 s · 20 s · ❤️ 5 s",
       "🤔 Guess: **Creo que… · Parece que… · Seguramente…**",
       "❤️ End: **Me encanta esta foto porque me recuerda a…**"],
      "Tarea dos. Describe una foto. Tienes hasta dos minutos. Sigue el orden: personas, aspecto y ropa, "
      "qué sucede, el lugar y los objetos.")
phrases("2", [
    ("En la foto se ven tres personas. Me parece que son una familia.",
     "In the photo you can see three people. I think they are a family.", "se **ven** (plural)"),
    ("A la izquierda hay un hombre joven. Lleva una camiseta blanca.",
     "On the left there is a young man. He's wearing a white T-shirt.", "**hay un…** · camiseta blanc**a**"),
    ("En el centro está la madre. Tiene el pelo largo y moreno.",
     "In the centre is the mother. She has long dark hair.", "**está el / la…**"),
    ("Están en la cocina. Seguramente es por la mañana.",
     "They're in the kitchen. It's probably the morning.", "say WHERE they are"),
    ("En la mesa hay dos vasos y un plato. Al fondo se ve una ventana.",
     "On the table there are two glasses and a plate. In the background there's a window.",
     "la **mesa**, not table · un **vaso**"),
    ("Me encanta esta foto porque me recuerda a mi familia.",
     "I love this photo because it reminds me of my family.", "your ending sentence"),
])


def photo_body(mode):
    return (PILLS[mode] + f"<div class='main'><div class='two'><img src='file://{PHOTO}'><div class='paseo'>"
            "<b>P</b>ersonas · ¿cuántas? ¿relación?<br><b>A</b>specto y ropa (40 s)<br><b>S</b>ucede · ¿qué hacen?"
            "<br><b>E</b>n qué lugar<br><b>O</b>bjetos · ¿dónde están?<br>❤️ Me encanta esta foto porque…</div>"
            "</div></div><div class='credit'>Photo: «Birthday party», public domain, Wikimedia Commons</div>")


seg("2", photo_body("prepare").replace(PILLS["prepare"], "<span class='pill'>🎙️ Ahora tú</span>"),
    say("Mira la foto. Tienes treinta segundos para preparar. En el examen tienes dos minutos y medio."))
countdown("2", photo_body, 30, "prepare")
seg("2", photo_body("speak"), say("Ahora habla. Tienes dos minutos."))
countdown("2", photo_body, 120, "speak")
model("2", "**En la foto se ven** muchas personas: unos doce niños y tres adultos. **Me parece que** es una "
      "fiesta de cumpleaños. **En el centro hay** una niña con un vestido de rayas de colores. **Creo que** es su "
      "cumpleaños, porque está cortando la tarta. **A su lado está** una mujer joven con el pelo largo y moreno. "
      "**Seguramente** es su madre. **A la izquierda**, detrás, hay un señor mayor con una camisa blanca. "
      "Casi todos los niños **llevan** gorros de fiesta de colores. **Están en** una casa, en el salón. Los niños "
      "están aplaudiendo y **parece que** están muy contentos. **En la mesa hay** una tarta grande con velas y "
      "unos regalos. **Al fondo se ven** globos de colores. **Me encanta esta foto porque me recuerda a** los "
      "cumpleaños de mi infancia.", photo=True)

# ---- Tarea 3
title("3", "Tarea 3 · Mensajes de voz", "2 messages · 1:30 each",
      ["🥪 SÁNDWICH: hola → porque → 1 · 2 · 3 → adiós",
       "👥 **tú OR usted**, never both · check the **name**",
       "⏱️ Say goodbye by **1:15**", "🔊 te **LLAMO** (te YA-mo), not te amo"],
      "Tarea tres. Dejas un mensaje de voz. Tienes un minuto y medio. "
      "Di adiós antes de un minuto y quince segundos.")
phrases("3", [
    ("¡Hola, Pablo! Soy Aziz. Te llamo porque tengo un problema.",
     "Hi Pablo! It's Aziz. I'm calling because I have a problem.", "te **YA**-mo · **un** problema"),
    ("Muchas gracias por tu invitación. Es muy amable de tu parte.",
     "Thank you very much for your invitation. That's very kind of you.", "thank"),
    ("Lo siento mucho, de verdad, pero no puedo ir.",
     "I'm really sorry, but I can't go.", "apologize"),
    ("Te explico: es que tengo un examen muy importante.",
     "Let me explain: I have a very important exam.", "give a reason"),
    ("¿Qué te parece si quedamos el domingo?",
     "How about we meet on Sunday?", "propose"),
    ("Buenos días. Me llamo Aziz. Le llamo porque he visto su oferta.",
     "Good morning. My name is Aziz. I'm calling because I saw your offer.", "**usted**: le llamo, su oferta"),
    ("Si quiere, puedo enviarle mi currículum. Muchas gracias por su atención.",
     "If you like, I can send you my CV. Thank you for your attention.", "usted goodbye"),
])
SIT = ("<b>Situación:</b> Su amigo Pablo le invita a su fiesta de cumpleaños el sábado, pero usted no puede ir. "
       "Usted debe:<ul><li>agradecer la invitación y disculparse;</li><li>explicar por qué no puede ir;</li>"
       "<li>proponer otro día para quedar.</li></ul>")


def sit_body(mode):
    return PILLS[mode] + f"<div class='main'><div class='task'>{SIT}</div></div>"


seg("3", "<span class='pill'>🎙️ Ahora tú</span>" + f"<div class='main'><div class='task'>{SIT}</div></div>",
    say("Lee la situación. Tienes veinte segundos para preparar. Después, habla un minuto y medio."))
countdown("3", sit_body, 20, "prepare")
countdown("3", sit_body, 90, "speak")
model("3", "**¡Hola, Pablo! ¿Qué tal? Soy Aziz. Te llamo por** tu fiesta de cumpleaños. **Muchas gracias por tu "
      "invitación, es muy amable de tu parte. Pero lo siento mucho, de verdad: no puedo ir. Te explico: es que** "
      "el sábado tengo un examen muy importante y tengo que estudiar. **Pero no te preocupes: ¿qué te parece si "
      "quedamos** el domingo por la tarde? Te invito a un café y te doy tu regalo. **¡Feliz cumpleaños! Un abrazo "
      "muy fuerte. ¡Hasta pronto!**")

# ---- Tarea 4
title("4", "Tarea 4 · Texto y 3 preguntas", "Read a short text · 1 minute per question",
      ["🔁 **sí / no → porque → por ejemplo → por eso**", "📄 Repeat the **question's words**",
       "✅ Answer **all 3** questions: that's what scores most"],
      "Tarea cuatro. Lees un texto y contestas tres preguntas. Un minuto para cada pregunta.")
phrases("4", [
    ("Es una buena pregunta.", "That's a good question.", "buys you 2 seconds"),
    ("En mi opinión, sí, pero solo si se usa bien.", "In my opinion, yes, but only if it's used well.",
     "a careful opinion"),
    ("Por ejemplo, en mi país, muchos jóvenes usan el móvil todo el día.",
     "For example, in my country, many young people use their phone all day.", "your example"),
    ("Por eso creo que es importante tener límites.", "That's why I think it's important to have limits.",
     "close the answer"),
    ("La solución no es fácil, pero hay cosas que podemos hacer.",
     "The solution isn't easy, but there are things we can do.", "for any ¿qué solución…?"),
])
seg("4", "<span class='pill'>🎙️ Ahora tú</span><div class='main'><div class='es'>Tema: el uso del móvil</div>"
    "<div class='en'>Listen to the question, think, then answer for 1 minute.</div></div>",
    say("Ahora tú. El tema es el uso del móvil. Escucha la pregunta."))
question("4", "¿Piensa que los jóvenes pasan demasiado tiempo con el móvil?", 10, 60,
         "**Es una buena pregunta. En mi opinión, sí, porque** muchos jóvenes miran el móvil todo el día, incluso "
         "en clase. **Además,** no hacen deporte y duermen poco. **Por ejemplo, en mi caso,** a veces paso tres "
         "horas con el móvil por la noche. **Por eso creo que** es importante tener límites: por ejemplo, no usar "
         "el móvil durante la comida.", ASK[0])

# ---- Tarea 5
title("5", "Tarea 5 · Tu opinión", "2 minutes to prepare · speak 2–3 minutes",
      ["✅ **opinión · razones · ejemplo · conclusión**", "🤝 **Estoy de acuerdo solo en parte**",
       "📄 Tarea 4 and Tarea 5 have the same topic: **use the text!**",
       "⭐ Same phrases as your Writing Tarea 2"],
      "Tarea cinco. Das tu opinión sobre una frase. Prepara cuatro puntos: opinión, razones, ejemplo y conclusión.")
phrases("5", [
    ("Hoy en día se habla mucho de este tema.", "Nowadays people talk a lot about this topic.", "start"),
    ("Yo estoy de acuerdo solo en parte.", "I only partly agree.", "the easiest opinion"),
    ("Por un lado, es verdad que es útil. Por otro lado, el problema principal es que es caro.",
     "On the one hand, it's true that it's useful. On the other hand, the main problem is that it's expensive.",
     "both sides"),
    ("En conclusión, creo que tenemos que buscar un equilibrio.",
     "In conclusion, I think we need to find a balance.", "never forget the conclusion"),
    ("Es importante que todos hagamos algo.", "It's important that we all do something.",
     "subjunctive = B1 booster"),
])
STMT = ("<div class='q'>«Los móviles deberían estar prohibidos en los colegios.»</div><div class='task'>"
        "No olvide: dar su opinión · justificarla · un ejemplo · una conclusión.</div>")


def stmt_body(mode):
    return PILLS[mode] + f"<div class='main'>{STMT}</div>"


seg("5", "<span class='pill'>🎙️ Ahora tú</span>" + f"<div class='main'>{STMT}</div>",
    say("Lee la frase. Tienes treinta segundos para preparar. En el examen tienes dos minutos. "
        "Después, habla dos minutos."))
countdown("5", stmt_body, 30, "prepare")
countdown("5", stmt_body, 120, "speak")
model("5", "**La frase dice que** los móviles deberían estar prohibidos en los colegios. **Yo estoy de acuerdo "
      "solo en parte. Por un lado, es verdad que** el móvil distrae mucho a los alumnos: miran las redes sociales "
      "en clase y no escuchan al profesor. **Por otro lado, el problema principal es que** el móvil también es "
      "útil para aprender: podemos buscar información o usar un diccionario. **Por ejemplo, en mi caso,** uso el "
      "móvil para practicar español todos los días. **En conclusión, creo que** no hay que prohibir el móvil, "
      "pero sí controlar cuándo se usa. **Es importante que todos** hagamos un uso responsable de la tecnología.")

# ---- End
title("end", "Tus 3 trampas", "Your 3 traps · check them in every answer",
      ["📍 WHERE → **está** · WHO / WHAT → **es / era** · weather → **hacía**",
       "♂️ **el** planeta · **el** problema · **el** tema (‑ma words are masculine)",
       "👥 **tú OR usted** · te **LLAMO** · goodbye by **1:15**",
       "💪 ¡Mucha suerte el miércoles! **Tú puedes.**"],
      "Estas son tus tres trampas. Revísalas en cada respuesta. ¡Mucha suerte en el examen! Tú puedes.")

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

FONT_CLOCK = os.path.join(FONTS, "Nunito-900.ttf")


def clock_filter(d):
    rem = f"ceil({d}-t)"
    txt = (r"%{eif\:floor(" + rem + r"/60)\:d}\:%{eif\:mod(" + rem + r"\,60)\:d\:2}")
    return (f"drawtext=fontfile={FONT_CLOCK}:text='{txt}':fontsize=50:fontcolor=white:"
            f"x=1140-text_w/2:y=45-text_h/2")


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
        cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS),
               "-i", os.path.join(WORK, "slides", s["name"] + ".png"), "-i", wav]
        if s["clock"]:
            cmd += ["-vf", clock_filter(s["clock"])]
        cmd += ["-c:v", "libx264", "-tune", "stillimage", "-crf", "26", "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-g", "50", "-c:a", "aac", "-b:a", "64k", "-ar", str(SR), "-ac", "1", "-t", f"{dur:.3f}", mp4]
        subprocess.run(cmd, check=True)
        L.write(f"file '{mp4}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                "-movflags", "+faststart", OUT], check=True)
for c, name in chapters:
    print(f"{int(c // 60)}:{int(c % 60):02d}  {name}")
print(f"total {int(t // 60)}:{int(t % 60):02d}  segments {len(SEGS)}")
