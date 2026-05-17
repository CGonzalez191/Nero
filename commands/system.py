import os
import subprocess
import ctypes
from datetime import datetime

try:
    import pyautogui
except ImportError:
    pyautogui = None


def cambiar_volumen(accion):
    try:
        from pycaw.pycaw import AudioUtilities

        devices = AudioUtilities.GetSpeakers()
        volume = devices.EndpointVolume

        if accion == "subir":
            current = volume.GetMasterVolumeLevelScalar()
            new_vol = min(1.0, current + 0.1)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            return f"Volumen subido al {int(new_vol * 100)}%"
        elif accion == "bajar":
            current = volume.GetMasterVolumeLevelScalar()
            new_vol = max(0.0, current - 0.1)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            return f"Volumen bajado al {int(new_vol * 100)}%"
        elif accion == "silenciar":
            volume.SetMute(1, None)
            return "Silenciado"
        elif accion == "activar":
            volume.SetMute(0, None)
            return "Sonido activado"
    except Exception as e:
        return f"Error al cambiar volumen: {e}"


def decir_hora():
    ahora = datetime.now()
    return f"Son las {ahora.hour} con {ahora.minute} minutos"


def decir_fecha():
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    ahora = datetime.now()
    return f"Hoy es {dias[ahora.weekday()]} {ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"


def tomar_captura():
    if pyautogui is None:
        return "pyautogui no está instalado"
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo = os.path.join(desktop, f"captura_{timestamp}.png")
    try:
        pyautogui.screenshot(archivo)
        return f"Captura guardada como captura_{timestamp}.png"
    except Exception as e:
        return f"Error al tomar captura: {e}"


def cancelar_apagado():
    try:
        subprocess.run(["shutdown", "/a"], check=True)
        return "Apagado cancelado"
    except subprocess.CalledProcessError:
        return "No hay un apagado pendiente"



