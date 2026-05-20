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


_PROCESOS_CRITICOS = {
    "winlogon.exe", "csrss.exe", "services.exe", "lsass.exe",
    "svchost.exe", "smss.exe", "wininit.exe", "system",
    "system idle process", "spoolsv.exe", "taskmgr.exe",
}

_EXE_CONOCIDOS = {
    "chrome": "chrome.exe", "firefox": "firefox.exe", "edge": "msedge.exe",
    "spotify": "Spotify.exe", "discord": "Discord.exe", "steam": "steam.exe",
    "notepad": "notepad.exe", "bloc de notas": "notepad.exe",
    "word": "WINWORD.EXE", "excel": "EXCEL.EXE", "powerpoint": "POWERPNT.EXE",
    "code": "Code.exe", "vscode": "Code.exe", "visual studio code": "Code.exe",
    "explorer": "explorer.exe", "explorador": "explorer.exe",
    "calculadora": "Calculator.exe", "cmd": "cmd.exe",
    "terminal": "WindowsTerminal.exe", "powershell": "powershell.exe",
    "powershell ise": "powershell_ise.exe",
    "outlook": "OUTLOOK.EXE", "telegram": "Telegram.exe",
    "whatsapp": "WhatsApp.exe", "slack": "Slack.exe",
    "notion": "Notion.exe", "obsidian": "Obsidian.exe",
    "brave": "brave.exe", "opera": "opera.exe", "safari": "safari.exe",
    "vlc": "vlc.exe", "mpc": "mpc-hc64.exe",
    "7zip": "7zFM.exe", "winrar": "WinRAR.exe",
    "photoshop": "Photoshop.exe", "illustrator": "Illustrator.exe",
    "figma": "Figma.exe", "blender": "blender.exe",
    "unity": "Unity.exe", "unreal": "UnrealEditor.exe",
    "goland": "goland64.exe", "pycharm": "pycharm64.exe",
    "intellij": "idea64.exe", "webstorm": "webstorm64.exe",
    "android studio": "studio64.exe", "xampp": "xampp-control.exe",
    "docker": "Docker Desktop.exe", "postman": "Postman.exe",
    "mysql": "mysql.exe", "mongodb": "mongod.exe",
    "github desktop": "GitHubDesktop.exe", "sourcetree": "SourceTree.exe",
    "filezilla": "filezilla.exe", "putty": "putty.exe",
    "obs": "obs64.exe", "audacity": "audacity.exe",
    "calibre": "calibre.exe", "foxit": "FoxitReader.exe",
    "adobe acrobat": "Acrobat.exe", "acrobat": "Acrobat.exe",
    "teamviewer": "TeamViewer.exe", "anydesk": "AnyDesk.exe",
    "nvidia": "nvidia-smi.exe", "geforce": "GeForceExperience.exe",
    "cortana": "Cortana.exe", "skype": "Skype.exe",
}


def _buscar_exe_por_nombre(nombre):
    nombre = nombre.lower().strip()
    if nombre in _EXE_CONOCIDOS:
        return _EXE_CONOCIDOS[nombre]
    try:
        result = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(",")
            if parts:
                exe = parts[0].strip('"').strip()
                if nombre in exe.lower().replace(".exe", ""):
                    return exe
    except Exception:
        pass
    return None


def cerrar_aplicacion(nombre):
    exe = _buscar_exe_por_nombre(nombre)
    if not exe:
        return f"No encontré {nombre} ejecutándose"
    if exe.lower() in _PROCESOS_CRITICOS:
        return f"No puedo cerrar {nombre}, es un proceso del sistema"
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", exe],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return f"Cerrado {nombre}"
    except Exception as e:
        return f"Error al cerrar {nombre}: {e}"


def cerrar_ventana_activa():
    if pyautogui is None:
        return "pyautogui no está instalado"
    try:
        pyautogui.hotkey("alt", "f4")
        return "Ventana cerrada"
    except Exception as e:
        return f"Error al cerrar ventana: {e}"



