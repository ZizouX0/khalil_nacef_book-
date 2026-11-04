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
SRC = os.path.join(HERE, "src", "03_CA.md")
OUT = os.path.join(HERE, "audio")
SR = 22050
SLOW = 1.08  # A1-B1 tasks are read slowly and clearly

VOICES_DIR = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PIPER_VOICES", "voices")
_cache = {}


def voice(name):
    if name not in _cache:
        _cache[name] = PiperVoice.load(os.path.join(VOICES_DIR, name + ".onnx"))
    return _cache[name]


# who speaks: (model, speaker id)
NARRATOR = ("es_ES-sharvard-medium", 0)
MEN = [("es_ES-davefx-medium", None), ("es_MX-ald-medium", None), ("es_ES-sharvard-medium", 0)]
WOMEN = [("es_ES-sharvard-medium", 1), ("es_AR-daniela-high", None), ("es_MX-claude-high", None)]
ADS = [WOMEN[2], MEN[1], WOMEN[1], MEN[0], WOMEN[0]]
CAST = {"ANDRÉS": MEN[0], "MARTA": WOMEN[0]}


def clean(t):
    t = re.sub(r"\*\*[^*]*\*\*", lambda m: m.group(0).strip("*"), t)
    t = re.sub(r"[*_`]", "", t)
    t = re.sub(r"\[[^\]]*\]", "", t)              # stage directions like [30 s]
    t = t.replace("«", "").replace("»", "").replace("…", "...")
    return re.sub(r"\s+", " ", t).strip()


def say(text, who=NARRATOR, scale=SLOW):
    model, spk = who
    cfg = SynthesisConfig(speaker_id=spk, length_scale=scale)
    chunks = [c.audio_int16_array for c in voice(model).synthesize(clean(text), cfg)]
    return np.concatenate(chunks + [silence(0.25)])


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


def twice(parts, label, who, gap_between=5, after=10, answer_prompt=None):
    seg = [silence(0.4), say(label), silence(0.6)]
    body = say(parts, who)
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
        convo += [say(text, CAST.get(name.strip(), MEN[0])), silence(0.35)]
    convo = np.concatenate(convo)
    return [say(instr), beep(), silence(30), beep(), silence(0.6), convo, silence(10),
            say("Ahora va a escuchar la conversación otra vez."), silence(0.6), convo, silence(30), say("Fin de la tarea.")]


def track_items(instr, transcript, pattern, label_word, voices_for):
    items = re.findall(pattern, transcript, flags=re.S)
    seg = [say(instr), beep(), silence(30), beep(), silence(0.6)]
    for i, it in enumerate(items, 1):
        n, extra, text = it
        who = voices_for(i, extra)
        prompt = f"Conteste a la pregunta número {NUM[i] if i <= 10 else i}." if label_word == "Anuncio" else None
        seg += twice(text, f"{label_word} {NUM[int(n)]}.", who, answer_prompt=prompt)
    seg += [silence(20), say("Fin de la tarea.")]
    return seg


def track_numbers(instr, transcript):
    sents = re.findall(r"^\s*(\d+)\.\s+(.+)$", transcript, flags=re.M)
    seg = [say(instr), beep(), silence(3)]
    pool = MEN + WOMEN
    for i, (n, s) in enumerate(sents):
        who = pool[i % len(pool)]
        body = say(s, who, 1.0)
        seg += [silence(0.4), say(f"Número {NUM[int(n)]}."), silence(0.5), body, silence(3), body, silence(8)]
    seg += [say("Fin del ejercicio.")]
    return seg


def track_speaking_t1(eio_md):
    """Speaking Tarea 1 simulator: each question twice, then a timed answer window between beeps."""
    body = next(v for k, v in blocks(eio_md, "exam").items() if k.startswith("Tarea 1"))
    series = re.findall(r"\*\*(Serie \w)\*\*\s*\n((?:\s*\d+\..+\n?)+)", body)
    asker = WOMEN[0]  # standard Spain voice: T1 questions use standard Spanish
    seg = [say("Prueba de expresión e interacción orales. Tarea uno. Va a escuchar cuatro preguntas de carácter "
               "personal. Escuche cada pregunta dos veces. Cuando oiga la señal, grabe su respuesta. "
               "En las preguntas uno y dos tiene quince segundos. En las preguntas tres y cuatro, treinta segundos."),
           silence(2)]
    for name, qs in series:
        seg += [say(name.replace("Serie", "Serie").replace(" A", " A.").replace(" B", " B.")), silence(1.5)]
        for i, q in enumerate(re.findall(r"^\s*\d+\.\s+(.+)$", qs, flags=re.M), 1):
            qa = say(q.replace("pequeño/a", "pequeño"), asker, 1.0)
            seg += [say(f"Pregunta {NUM[i]}."), silence(0.4), qa, silence(1.5), qa, silence(0.6),
                    beep(), silence(15 if i <= 2 else 30), beep(), silence(2)]
        seg += [silence(2)]
    seg += [say("Fin de la tarea.")]
    return seg


def write_mp3(segments, name):
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
    md = open(SRC, encoding="utf-8").read()
    ex, tr = blocks(md, "exam"), blocks(md, "transcript")
    find = lambda d, key: next(v for k, v in d.items() if key in k)
    gender = lambda i, extra: (MEN if "HOMBRE" in extra.upper() else WOMEN)[(i // 2) % 3]

    write_mp3(track_dialogue(instruction(find(ex, "Ejercicio 1")), find(tr, "Ejercicio 1")),
              "01_Tarea1_conversacion")
    write_mp3(track_items(instruction(find(ex, "Ejercicio 2")), find(tr, "Ejercicio 2"),
                          r"\*\*Anuncio (\d+)\.\*\*()\s*(.+?)(?=\n\s*\n|\Z)", "Anuncio",
                          lambda i, e: ADS[(i - 1) % len(ADS)]), "02_Tarea2_anuncios")
    write_mp3(track_items(instruction(find(ex, "Ejercicio 3")), find(tr, "Ejercicio 3"),
                          r"\*\*Persona (\d+) \((\w+)\):\*\*\s*(.+?)(?=\n\s*\n|\Z)", "Persona", gender),
              "03_Tarea3_setA_un_viaje")
    write_mp3(track_items(instruction(find(ex, "Ejercicio 4")), find(tr, "Ejercicio 4"),
                          r"\*\*Persona (\d+) \((\w+)\):\*\*\s*(.+?)(?=\n\s*\n|\Z)", "Persona", gender),
              "04_Tarea3_setB_primer_dia")
    write_mp3(track_numbers(instruction(find(ex, "Ejercicio 5")), find(tr, "Ejercicio 5")),
              "05_numeros_horas_precios")
    eio = open(os.path.join(HERE, "src", "05_EIO.md"), encoding="utf-8").read()
    write_mp3(track_speaking_t1(eio), "06_Oral_Tarea1_simulador")


if __name__ == "__main__":
    main()
