import speech_recognition as sr
import pyttsx3
import os
import threading
import numpy as np
import sounddevice as sd
import json
import queue

from config import VOZ_VELOCIDAD, VOZ_VOLUMEN, VOSK_MODEL_PATH, STT_IDIOMA

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- TTS ---
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        voz_encontrada = False
        for voz in _engine.getProperty('voices'):
            langs = voz.languages if voz.languages else []
            nombre = voz.name or ""
            if 'spanish' in nombre.lower() or any('es' in l.lower() for l in langs if l):
                _engine.setProperty('voice', voz.id)
                voz_encontrada = True
                break
        if not voz_encontrada:
            voices = _engine.getProperty('voices')
            if voices:
                _engine.setProperty('voice', voices[0].id)
        _engine.setProperty('rate', VOZ_VELOCIDAD)
        _engine.setProperty('volume', VOZ_VOLUMEN)
    return _engine


def hablar(texto):
    try:
        engine = _get_engine()
        engine.say(texto)
        engine.runAndWait()
    except Exception as e:
        print(f"[Error TTS] {e}")


# --- STT ---
RATE = 16000

def escuchar():
    try:
        audio_queue = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[Audio] {status}")
            audio_queue.put(indata.copy())

        buffer = []
        speech_detected = False
        silence_chunks = 0
        best_rms = 0.0
        total_time = 0.0

        CHUNK_MS = 200
        chunk_size = int(RATE * CHUNK_MS / 1000)

        with sd.InputStream(
            samplerate=RATE,
            channels=1,
            dtype='int16',
            callback=callback,
            blocksize=chunk_size
        ):
            while True:
                chunk = audio_queue.get()
                buffer.append(chunk)

                chunk_duration = len(chunk) / RATE
                total_time += chunk_duration

                rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
                if rms > best_rms:
                    best_rms = rms

                threshold = max(500, best_rms * 0.15)

                if rms >= threshold:
                    if not speech_detected:
                        speech_detected = True
                    silence_chunks = 0
                else:
                    silence_chunks += 1

                if speech_detected and silence_chunks * chunk_duration >= 1.0:
                    break
                if total_time >= 8:
                    break
                if not speech_detected and total_time >= 2.0:
                    return ""

        if not speech_detected or total_time < 0.3:
            return ""

        audio = np.concatenate(buffer)

        audio_float = audio.astype(np.float32)
        peak = float(np.max(np.abs(audio_float)))
        if peak > 0 and peak < 25000:
            gain = min(25000.0 / peak, 2.0)
            audio_float *= gain
        audio_norm = np.clip(audio_float, -32768, 32767).astype(np.int16)
        raw_bytes = audio_norm.tobytes()

        audio_data = sr.AudioData(raw_bytes, RATE, 2)

        r = sr.Recognizer()
        text = r.recognize_google(audio_data, language=STT_IDIOMA)
        return text.lower().strip()

    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return _escuchar_vosk(raw_bytes)
    except Exception as e:
        print(f"[Error STT] {e}")
        return None


def _escuchar_vosk(raw_bytes):
    try:
        import vosk
        model_path = os.path.join(BASE_DIR, VOSK_MODEL_PATH)
        if not os.path.exists(model_path):
            return ""
        model = vosk.Model(model_path)
        rec = vosk.KaldiRecognizer(model, RATE)
        rec.AcceptWaveform(raw_bytes)
        result = json.loads(rec.Result())
        text = result.get("text", "").strip()
        return text.lower()
    except Exception:
        return ""
