import speech_recognition as sr
import pyttsx3
import os
import threading
import numpy as np
import sounddevice as sd
import json
import queue

from config import VOZ_VELOCIDAD, VOZ_VOLUMEN, VOSK_MODEL_PATH, STT_IDIOMA, VAD

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- TTS ---
_engine = None
_engine_lock = threading.Lock()

def _get_engine():
    global _engine
    if _engine is None:
        with _engine_lock:
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
_recognizer = sr.Recognizer()

def _ruido_es_anomalo(rms, noise_floor, zcr, zcr_voice_range):
    """Filtra ruidos transitorios (golpes, puertas) vs voz real."""
    if rms > noise_floor * 5 and zcr > zcr_voice_range[1]:
        return True
    return False


def _highpass_diff(audio_float):
    """High-pass filter usando primera diferencia (elimina DC y baja frecuencia)."""
    return np.diff(audio_float, prepend=audio_float[0])


def escuchar():
    raw_bytes = b""
    try:
        audio_queue = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[Audio] {status}")
            audio_queue.put(indata.copy())

        buffer = []
        speech_detected = False
        silence_chunks = 0
        total_time = 0.0

        audio_buffer = []
        noise_floor = VAD["noise_floor_init"]

        CHUNK_MS = 200
        chunk_size = int(RATE * CHUNK_MS / 1000)

        with sd.InputStream(
            samplerate=RATE, channels=1, dtype='int16',
            callback=callback, blocksize=chunk_size
        ):
            while True:
                chunk = audio_queue.get()
                total_time += len(chunk) / RATE

                # High-pass filter + RMS en un paso
                chunk_float = chunk.astype(np.float32).flatten()
                chunk_hp = _highpass_diff(chunk_float)
                rms = float(np.sqrt(np.mean(chunk_hp ** 2)))
                audio_buffer.append(chunk_hp)

                # Zero-crossing rate en el chunk filtrado
                signs = np.sign(chunk_hp)
                zcr = float(np.sum(np.abs(np.diff(signs)) > 0)) / len(chunk_hp)

                # Adaptive noise floor tracking
                if noise_floor == 0:
                    noise_floor = rms
                elif rms < noise_floor:
                    noise_floor = noise_floor * (1 - VAD["noise_alpha"]) + rms * VAD["noise_alpha"]
                else:
                    noise_floor = noise_floor * (1 - VAD["noise_alpha"] * 0.1) + rms * VAD["noise_alpha"] * 0.1

                threshold = max(noise_floor * VAD["snr_threshold"], 300)

                is_speech = rms >= threshold and not _ruido_es_anomalo(rms, noise_floor, zcr, (0.3, 0.7))

                if is_speech:
                    if not speech_detected:
                        speech_detected = True
                        audio_buffer = audio_buffer[-3:] or audio_buffer
                    silence_chunks = 0
                else:
                    silence_chunks += 1

                if speech_detected and silence_chunks * (CHUNK_MS / 1000) >= VAD["silence_timeout"]:
                    break
                if total_time >= VAD["max_record"]:
                    break
                if not speech_detected and total_time >= VAD["initial_timeout"]:
                    return ""

        if not speech_detected or total_time < 0.3:
            return ""

        audio_filtered = np.concatenate(audio_buffer).astype(np.float32)

        peak = float(np.max(np.abs(audio_filtered)))
        if peak > 0 and peak < 25000:
            gain = min(25000.0 / peak, 2.0)
            audio_filtered *= gain
        audio_norm = np.clip(audio_filtered, -32768, 32767).astype(np.int16)
        raw_bytes = audio_norm.tobytes()

        audio_data = sr.AudioData(raw_bytes, RATE, 2)

        text = _recognizer.recognize_google(audio_data, language=STT_IDIOMA)
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
