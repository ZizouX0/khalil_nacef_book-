#!/usr/bin/env python3
"""Make exam-style MP3 tracks for the booklet's ORIGINAL listening practice.

Reads the :::exam instructions and :::transcript blocks of src/03_CA.md and
voices them with Piper (open-source neural TTS), using Spain, Mexico and
Argentina voices so the student hears several varieties, as in SIELE.
Each track reproduces the exam rhythm: instruction, 30 s to read, every
audio played twice (5 s between plays), 10 s to answer, 30 s at the end.

    python3 make_audio.py /path/to/piper/voices

Voices (from huggingface.co/rhasspy/piper-voices): es_ES-davefx-medium,
es_ES-sharvard-medium (speakers M/F), es_MX-ald-medium, es_MX-claude-high,
es_AR-daniela-high.
"""
import os, re, subprocess, sys, wave
import numpy as np
from piper import PiperVoice, SynthesisConfig

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src_practice", "p2_CA.md")
OUT = os.path.join(HERE, "audio")
SR = 22050
# Speed calibrated on the 7 Edelsa exam recordings (Pistas 1-3), measured with an
# energy VAD against the printed transcripts:
#   Tarea 1 conversation  ~128 words/min, ~3.7 syllables/s, ~0.8-1 s between turns
#   Tarea 3 monologues    ~151 words/min, ~4.6 syllables/s, ~25 s per person
# Piper's default pace is ~170+ wpm, so every task is slowed to match.
RATE = {"t1": 1.25, "t2": 1.20, "t3": 1.24, "num": 1.10, "q": 1.05, "narrator": 1.05}
SENT_PAUSE = 0.45   # between sentences of one speaker
TURN_PAUSE = 0.85   # between speakers in a conversation
SLOW = RATE["narrator"]

VOICES_DIR = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PIPER_VOICES", "voices")
_cache = {}


def voice(name):
    if name not in _cache:
        _cache[name] = PiperVoice.load(os.path.join(VOICES_DIR, name + ".onnx"))
    return _cache[name]


# who speaks: (model, speaker id)
# The exam narrator is a woman (f0 ~185-205 Hz in all 7 Edelsa exams).
NARRATOR = ("es_ES-sharvard-medium", 1)
MEN = [("es_ES-davefx-medium", None), ("es_MX-ald-medium", None), ("es_ES-sharvard-medium", 0)]
WOMEN = [("es_MX-claude-high", None), ("es_AR-daniela-high", None), ("es_ES-sharvard-medium", 1)]
ADS = [WOMEN[0], MEN[1], WOMEN[1], MEN[0], MEN[2]]
CAST = {"ANDRÉS": MEN[0], "MARTA": WOMEN[0]}
END = "La tarea ha terminado. Ahora va a pasar a la siguiente tarea."


def clean(t):
    t = re.sub(r"\*\*[^*]*\*\*", lambda m: m.group(0).strip("*"), t)
    t = re.sub(r"[*_`]", "", t)
    t = re.sub(r"\[[^\]]*\]", "", t)              # stage directions like [30 s]
    t = t.replace("«", "").replace("»", "").replace("…", "...")
    return re.sub(r"\s+", " ", t).strip()


def say(text, who=NARRATOR, scale=SLOW, pause=SENT_PAUSE):
    """Speak text; Piper yields one chunk per sentence, so pause between them."""
    model, spk = who
    cfg = SynthesisConfig(speaker_id=spk, length_scale=scale)
    out = []
    for c in voice(model).synthesize(clean(text), cfg):
        out += [c.audio_int16_array, silence(pause)]
    return np.concatenate(out[:-1] + [silence(0.25)])


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.int16)


def beep():
    t = np.arange(int(SR * 0.35)) / SR
    env = np.minimum(1, np.minimum(t, t[::-1]) * 40)
    return (np.sin(2 * np.pi * 880 * t) * env * 6000).astype(np.int16)


NUM = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez"]


def blocks(md, kind):
    """{title: body} for every :::kind block"""
    out, cur, buf = {}, None, []
    for line in md.split("\n"):
        m = re.match(rf"^:::{kind}\s+(.*)$", line.strip())
        if m:
            cur, buf = m.group(1).strip(), []
            continue
        if cur is not None and line.strip() == ":::":
            out[cur] = "\n".join(buf)
            cur = None
            continue
        if cur is not None:
            buf.append(line)
    return out


def instruction(exam_body):
    for para in re.split(r"\n\s*\n", exam_body.strip()):
        if para.strip().startswith(("Usted", "Escuche", "*Usted", "_Usted")):
            return clean(para)
    return clean(exam_body.strip().split("\n")[0])


def twice(parts, label, who, scale, gap_between=5, after=10, answer_prompt=None):
    # In the exam the screen shows "Persona 1"; here the narrator says it, since
    # you are practising from paper.
    seg = [silence(0.4), say(label), silence(0.6)]
    body = say(parts, who, scale)
    seg += [body, silence(gap_between), body]
    if answer_prompt:
        seg += [silence(0.5), say(answer_prompt)]
    seg += [silence(after)]
    return seg


def track_dialogue(instr, transcript):
    lines = [l for l in transcript.split("\n") if re.match(r"^[A-ZÁÉÍÓÚÑ]+:", l.strip())]
    convo = []
    for l in lines:
        name, text = l.split(":", 1)
        convo += [say(text, CAST.get(name.strip(), MEN[0]), RATE["t1"]), silence(TURN_PAUSE)]
    convo = np.concatenate(convo)
    # real exam: no announcement before the second play, just 10 s of silence
    return [say("Prueba de comprensión auditiva. Tarea uno."), silence(0.8), say(instr), silence(30),
            convo, silence(10), convo, silence(30), say(END)]


def track_items(instr, transcript, pattern, label_word, voices_for, task, scale):
    items = re.findall(pattern, transcript, flags=re.S)
    seg = [say(f"Prueba de comprensión auditiva. Tarea {task}."), silence(0.8), say(instr), silence(30)]
    for i, it in enumerate(items, 1):
        n, extra, text = it
        who = voices_for(i, extra)
        prompt = f"Conteste a la pregunta número {NUM[i] if i <= 10 else i}." if label_word == "Anuncio" else None
        seg += twice(text, f"{label_word} {NUM[int(n)]}.", who, scale, answer_prompt=prompt)
    seg += [silence(20), say(END)]
    return seg


def track_numbers(instr, transcript):
    sents = re.findall(r"^\s*(\d+)\.\s+(.+)$", transcript, flags=re.M)
    seg = [say(instr), beep(), silence(3)]
    pool = MEN + WOMEN
    for i, (n, s) in enumerate(sents):
        who = pool[i % len(pool)]
        body = say(s, who, RATE["num"])
        seg += [silence(0.4), say(f"Número {NUM[int(n)]}."), silence(0.5), body, silence(3), body, silence(8)]
    seg += [say("Fin del ejercicio.")]
    return seg


def track_speaking_t1(eio_md):
    """Speaking Tarea 1 simulator, official rhythm: question once, 10 s to think,
    then 15 s (Q1-2) or 30 s (Q3-4) to answer between beeps, then 5 s."""
    body = next(v for k, v in blocks(eio_md, "exam").items() if k.startswith("Tarea 1"))
    series = re.findall(r"\*\*(Serie \w)\*\*\s*\n((?:\s*\d+\..+\n?)+)", body)
    asker = WOMEN[0]  # standard Spain voice: T1 questions use standard Spanish
    seg = [say("Prueba de expresión e interacción orales. Tarea uno. Va a escuchar cuatro preguntas de carácter "
               "personal. Después de cada pregunta tiene diez segundos para pensar. Cuando oiga la señal, "
               "conteste. En las preguntas uno y dos tiene quince segundos. En las preguntas tres y cuatro, "
               "treinta segundos."), silence(2)]
    for name, qs in series:
        seg += [say(name.replace("Serie", "Serie").replace(" A", " A.").replace(" B", " B.")), silence(1.5)]
        for i, q in enumerate(re.findall(r"^\s*\d+\.\s+(.+)$", qs, flags=re.M), 1):
            qa = say(q.replace("pequeño/a", "pequeño"), asker, RATE["q"])
            seg += [say(f"Pregunta {NUM[i]}."), silence(0.4), qa, silence(10),
                    beep(), silence(15 if i <= 2 else 30), beep(), silence(5)]
        seg += [silence(2)]
    seg += [say("Fin de la tarea.")]
    return seg


def track_speaking_book_t1(md):
    """Speaking book, Tarea 1: all series, official rhythm (question once, 10 s, beep, 15/30 s, beep)."""
    seg = [say("Libro de expresión oral. Tarea uno. Series uno a ocho. Después de cada pregunta tiene diez "
               "segundos para pensar. Cuando oiga la señal, conteste."), silence(2)]
    asker = WOMEN[0]
    for title, body in blocks(md, "exam").items():
        m = re.match(r"Serie (\d+)", title)
        if not m:
            continue
        seg += [say(f"Serie {NUM[int(m.group(1))]}."), silence(1.5)]
        qs = re.findall(r"^\s*\d+\.\s+\*Pregunta \(audio\):\*\s*(.+)$", body, flags=re.M)
        for i, q in enumerate(qs, 1):
            qa = say(re.sub(r"(\w+)o/a\b", r"\1o", q), asker, RATE["q"])
            seg += [say(f"Pregunta {NUM[i]}."), silence(0.4), qa, silence(10),
                    beep(), silence(15 if i <= 2 else 30), beep(), silence(5)]
        seg += [silence(3)]
    seg += [say("Fin de la tarea.")]
    return seg


def track_speaking_book_t4(md):
    """Speaking book, Tarea 4: the 3 questions of every option, 1 minute to answer each."""
    seg = [say("Libro de expresión oral. Tarea cuatro. Primero lea el texto de la opción en el libro. "
               "Después escuche cada pregunta. Cuando oiga la señal, conteste durante un minuto."), silence(2)]
    asker = MEN[0]
    for title, body in blocks(md, "exam").items():
        m = re.match(r"Set (\d+) · Tarea 4", title)
        if not m:
            continue
        opts = re.split(r"^\*\*Opción (\d)\. ([^*]+)\*\*.*$", body, flags=re.M)
        # opts = [pre, n1, name1, body1, n2, name2, body2]
        for k in range(1, len(opts) - 2, 3):
            n, name, ob = opts[k], opts[k + 1].strip(), opts[k + 2]
            qs = re.findall(r"^\s*\d\.\s+(.+)$", ob, flags=re.M)
            if not qs:
                continue
            seg += [say(f"Set {NUM[int(m.group(1))]}. Opción {NUM[int(n)]}: {name}."), silence(1.5)]
            for i, q in enumerate(qs, 1):
                qa = say(re.sub(r"(\w+)o o \w+a\b", r"\1o", q), asker, RATE["q"])
                seg += [say(f"Pregunta {NUM[i]}."), silence(0.4), qa, silence(3), beep(), silence(60), beep(), silence(4)]
            seg += [silence(3)]
    seg += [say("Fin de la tarea.")]
    return seg


def write_mp3(segments, name):
    only = os.environ.get("ONLY")
    if only and not any(name.startswith(o) for o in only.split(",")):
        return
    os.makedirs(OUT, exist_ok=True)
    audio = np.concatenate(segments)
    wav = os.path.join(OUT, name + ".wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    mp3 = os.path.join(OUT, name + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "48k",
                    "-metadata", f"title={name}", "-metadata", "album=SIELE in 7 days - listening practice", mp3], check=True)
    os.remove(wav)
    print(f"{mp3}  {len(audio) / SR / 60:.1f} min")


def main():
    only = os.environ.get("ONLY")

    def make(builder, name):
        if only and not any(name.startswith(o) for o in only.split(",")):
            return
        write_mp3(builder(), name)

    md = open(SRC, encoding="utf-8").read()
    ex, tr = blocks(md, "exam"), blocks(md, "transcript")
    find = lambda d, key: next(v for k, v in d.items() if key in k)
    gender = lambda i, extra: (MEN if "HOMBRE" in extra.upper() else WOMEN)[(i // 2) % 3]

    make(lambda: track_dialogue(instruction(find(ex, "Ejercicio 1")), find(tr, "Ejercicio 1")),
              "01_Tarea1_conversacion")
    make(lambda: track_items(instruction(find(ex, "Ejercicio 2")), find(tr, "Ejercicio 2"),
                          r"\*\*Anuncio (\d+)\.\*\*()\s*(.+?)(?=\n\s*\n|\Z)", "Anuncio",
                          lambda i, e: ADS[(i - 1) % len(ADS)], 2, RATE["t2"]), "02_Tarea2_anuncios")
    make(lambda: track_items(instruction(find(ex, "Ejercicio 3")), find(tr, "Ejercicio 3"),
                          r"\*\*Persona (\d+) \((\w+)\):\*\*\s*(.+?)(?=\n\s*\n|\Z)", "Persona", gender, 3, RATE["t3"]),
              "03_Tarea3_setA_un_viaje")
    make(lambda: track_items(instruction(find(ex, "Ejercicio 4")), find(tr, "Ejercicio 4"),
                          r"\*\*Persona (\d+) \((\w+)\):\*\*\s*(.+?)(?=\n\s*\n|\Z)", "Persona", gender, 3, RATE["t3"]),
              "04_Tarea3_setB_primer_dia")
    make(lambda: track_numbers(instruction(find(ex, "Ejercicio 5")), find(tr, "Ejercicio 5")),
              "05_numeros_horas_precios")
    eio = open(os.path.join(HERE, "src_practice", "p4_EIO.md"), encoding="utf-8").read()
    make(lambda: track_speaking_t1(eio), "06_Oral_Tarea1_simulador")
    sb = os.path.join(HERE, "src_speaking")
    if os.path.exists(os.path.join(sb, "s1_T1.md")):
        make(lambda: track_speaking_book_t1(open(os.path.join(sb, "s1_T1.md"), encoding="utf-8").read()),
                  "07_Oral_libro_Tarea1_series1-8")
    if os.path.exists(os.path.join(sb, "s4_T45.md")):
        make(lambda: track_speaking_book_t4(open(os.path.join(sb, "s4_T45.md"), encoding="utf-8").read()),
                  "08_Oral_libro_Tarea4_preguntas")


if __name__ == "__main__":
    main()
