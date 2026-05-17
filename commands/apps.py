import os
import sys
import json
import glob
import subprocess
import re
import ctypes
import string

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache.json")

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop")
DOCUMENTS = os.path.join(HOME, "Documents")
DOWNLOADS = os.path.join(HOME, "Downloads")

START_MENU_PATHS = [
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
    os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
]
LOCAL_APP_DATA = os.path.expandvars(r"%LocalAppData%")


def _listar_unidades():
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    return [f"{d}:\\" for d in string.ascii_uppercase if bitmask & (1 << (ord(d) - 65))]


UNIDADES = _listar_unidades()

# --- Cache helpers ---

def _cargar_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"apps": {}, "folders": {}}


def _guardar_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Error cache] {e}")


# --- App search strategies ---

_PALABRAS_EXCLUIR = {"desinstalar", "uninstall", "uninst", "remove", "eliminar"}


def _es_lanzador(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0].lower()
    palabras = nombre.replace("(", " ").replace(")", " ").replace("-", " ").split()
    return not any(p in _PALABRAS_EXCLUIR for p in palabras)

_INDEX_START_MENU = []
_INDEX_STEAM_GAMES = {}
_INDEX_READY = False


def _indexar_todo():
    global _INDEX_READY
    if _INDEX_READY:
        return
    vistos = set()
    for base in START_MENU_PATHS:
        if not os.path.exists(base):
            continue
        for root, _, files in os.walk(base):
            for f in files:
                if f.lower().endswith(".lnk"):
                    ruta = os.path.join(root, f)
                    if ruta not in vistos:
                        vistos.add(ruta)
                        _INDEX_START_MENU.append(ruta)
    for lib in _obtener_librerias_steam():
        if not os.path.exists(lib):
            continue
        for manifest in glob.glob(os.path.join(lib, "appmanifest_*.acf")):
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    c = f.read()
                name = re.search(r'"name"\s+"(.+?)"', c)
                appid = re.search(r'"appid"\s+"(\d+)"', c)
                if name and appid:
                    _INDEX_STEAM_GAMES[name.group(1)] = appid.group(1)
            except Exception:
                continue
    _INDEX_READY = True


def _buscar_en_start_menu(nombre):
    _indexar_todo()
    nombre_lower = nombre.lower()
    fallback = None
    for lnk in _INDEX_START_MENU:
        if nombre_lower in os.path.splitext(os.path.basename(lnk))[0].lower():
            if _es_lanzador(os.path.basename(lnk)):
                return lnk
            if fallback is None:
                fallback = lnk
    return fallback


def _buscar_en_path(nombre):
    try:
        result = subprocess.run(
            ["where.exe", nombre],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            line = result.stdout.strip().split("\n")[0].strip()
            if line:
                return line
    except Exception:
        pass
    return None


def _buscar_en_registro(nombre):
    import winreg
    nombre_lower = nombre.lower()
    nombre_exe = nombre_lower + ".exe"
    rutas = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
    ]
    for base in rutas:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if subkey_name.lower() == nombre_exe or subkey_name.lower() == nombre_lower:
                            with winreg.OpenKey(key, subkey_name) as sk:
                                try:
                                    valor = winreg.QueryValue(sk, None)
                                    if valor and os.path.exists(valor):
                                        return valor
                                except Exception:
                                    pass
                        i += 1
                    except OSError:
                        break
        except Exception:
            continue
    return None


def _buscar_en_program_files(nombre):
    nombre_lower = nombre.lower()
    carpetas_programa = ["Program Files", "Program Files (x86)", "ProgramData"]
    fallback = None
    for unidad in UNIDADES:
        for carpeta in carpetas_programa:
            base = os.path.join(unidad, carpeta)
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                depth = root.replace(base, "").rstrip("\\").count(os.sep)
                if depth > 4:
                    dirs.clear()
                    continue
                for f in files:
                    if f.lower().endswith((".exe", ".lnk")) and nombre_lower in os.path.splitext(f)[0].lower():
                        if _es_lanzador(f):
                            return os.path.join(root, f)
                        if fallback is None:
                            fallback = os.path.join(root, f)
    return fallback


def _buscar_en_localappdata(nombre):
    if not os.path.exists(LOCAL_APP_DATA):
        return None
    nombre_lower = nombre.lower()
    for ext in ["*.exe", "*.lnk"]:
        pattern = os.path.join(LOCAL_APP_DATA, "**", ext)
        for f in glob.glob(pattern, recursive=True):
            if nombre_lower in os.path.splitext(os.path.basename(f))[0].lower():
                return f
    return None


def _buscar_en_desktop(nombre):
    if not os.path.exists(DESKTOP):
        return None
    nombre_lower = nombre.lower()
    for ext in ["*.lnk", "*.exe"]:
        pattern = os.path.join(DESKTOP, ext)
        for f in glob.glob(pattern):
            if nombre_lower in os.path.splitext(os.path.basename(f))[0].lower():
                return f
    return None


def _buscar_en_todas_las_unidades(nombre):
    nombre_lower = nombre.lower()
    carpetas_comunes = [
        "Program Files", "Program Files (x86)", "ProgramData",
        "Tools", "Utilidades", "Portables", "Games", "Juegos",
        "Wondershare", "Adobe", "Microsoft",
    ]
    fallback = None
    for unidad in UNIDADES:
        for carpeta in carpetas_comunes:
            base = os.path.join(unidad, carpeta)
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                depth = root.replace(base, "").rstrip("\\").count(os.sep)
                if depth > 5:
                    dirs.clear()
                    continue
                for f in files:
                    if f.lower().endswith((".exe", ".lnk")) and nombre_lower in os.path.splitext(f)[0].lower():
                        if _es_lanzador(f):
                            return os.path.join(root, f)
                        if fallback is None:
                            fallback = os.path.join(root, f)
    for unidad in UNIDADES:
        for root, dirs, files in os.walk(unidad):
            depth = root.replace(unidad, "").rstrip("\\").count(os.sep)
            if depth > 3:
                dirs.clear()
                continue
            for f in files:
                if f.lower().endswith((".exe", ".lnk")) and nombre_lower in os.path.splitext(f)[0].lower():
                    if _es_lanzador(f):
                        return os.path.join(root, f)
                    if fallback is None:
                        fallback = os.path.join(root, f)
    return fallback


# --- Steam games ---

STEAM_PATH = r"C:\Program Files (x86)\Steam"
STEAM_EXE = os.path.join(STEAM_PATH, "steam.exe")


def _obtener_librerias_steam():
    librerias = [os.path.join(STEAM_PATH, "steamapps")]
    vdf = os.path.join(STEAM_PATH, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf):
        with open(vdf, "r", encoding="utf-8") as f:
            for m in re.finditer(r'"path"\s+"(.+?)"', f.read()):
                librerias.append(os.path.join(m.group(1).replace("\\\\", "\\"), "steamapps"))
    return librerias


def _indexar_juegos_steam(forzar=False):
    _indexar_todo()
    if _INDEX_STEAM_GAMES:
        cache = _cargar_cache()
        cache["steam_games"] = _INDEX_STEAM_GAMES
        cache["steam_ts"] = __import__("time").time()
        _guardar_cache(cache)
    return _INDEX_STEAM_GAMES


def _normalizar(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", "", s).strip()


def _puntuar_coincidencia(query, game_name):
    q = query.lower()
    g = game_name.lower()
    gn = _normalizar(game_name)
    if g == q or gn == q:
        return 100
    if g.startswith(q + ":") or g.startswith(q + " ") or gn.startswith(q):
        return 80
    if re.search(rf"(^|\s){re.escape(q)}($|\s)", g):
        return 60
    if re.search(rf"(^|\s){re.escape(q)}($|\s)", gn):
        return 50
    if q in g:
        return 40
    if q in gn:
        return 30
    return 0


def abrir_juego_steam(nombre):
    nombre_normal = _normalizar(nombre)
    if not nombre_normal:
        return None

    def _buscar(juegos):
        mejor = (0, None, None)
        for game_name, appid in juegos.items():
            score = _puntuar_coincidencia(nombre_normal, game_name)
            if score > mejor[0]:
                mejor = (score, game_name, appid)
        return mejor

    juegos = _indexar_juegos_steam()
    score, game_name, appid = _buscar(juegos)

    if score < 30:
        juegos = _indexar_juegos_steam(forzar=True)
        score, game_name, appid = _buscar(juegos)

    if score >= 30 and game_name and appid:
        try:
            if os.path.exists(STEAM_EXE):
                subprocess.Popen([STEAM_EXE, f"steam://rungameid/{appid}"])
            else:
                subprocess.Popen(f"steam://rungameid/{appid}", shell=True)
            return f"Abriendo {game_name}"
        except Exception as e:
            return f"Error: {e}"

    return None


# --- Main app opener ---

def abrir_aplicacion(nombre):
    nombre = nombre.strip().lower()

    cache = _cargar_cache()
    if nombre in cache.get("apps", {}):
        ruta = cache["apps"][nombre]
        try:
            os.startfile(ruta)
            return f"Abrí {nombre}"
        except Exception:
            pass

    if nombre.startswith("ms-settings:"):
        try:
            subprocess.run(["start", nombre], shell=True, check=True)
            return f"Abrí configuración de Windows"
        except Exception as e:
            return f"Error: {e}"

    buscadores = [
        ("Steam", lambda n: abrir_juego_steam(n) or None),
        ("Registro", _buscar_en_registro),
        ("Start Menu", _buscar_en_start_menu),
        ("PATH", _buscar_en_path),
        ("Program Files", _buscar_en_program_files),
        ("LocalAppData", _buscar_en_localappdata),
        ("Desktop", _buscar_en_desktop),
        ("Todas las unidades", _buscar_en_todas_las_unidades),
    ]

    for nombre_buscador, buscador in buscadores:
        if nombre_buscador == "Steam":
            resultado = buscador(nombre)
            if resultado:
                return resultado
            continue

        ruta = buscador(nombre)
        if not ruta or not os.path.exists(ruta):
            continue

        if nombre_buscador != "PATH":
            nombre_limpio = os.path.splitext(os.path.basename(ruta))[0].lower()
            if not _es_lanzador(nombre_limpio):
                continue

        cache["apps"][nombre] = ruta
        _guardar_cache(cache)
        try:
            os.startfile(ruta)
            return f"Abrí {nombre}"
        except Exception:
            continue

    return f"No encontré {nombre}"


# --- Folder search ---

def _buscar_carpeta_en_unidades(nombre):
    nombre_lower = nombre.lower()
    for unidad in UNIDADES:
        for root, dirs, _ in os.walk(unidad):
            depth = root.replace(unidad, "").rstrip("\\").count(os.sep)
            if depth > 2:
                dirs.clear()
                continue
            for d in dirs:
                if d.lower() == nombre_lower:
                    return os.path.join(root, d)
    return None


def abrir_carpeta(nombre):
    nombre = nombre.strip().lower()

    cache = _cargar_cache()
    if nombre in cache.get("folders", {}):
        ruta = cache["folders"][nombre]
        try:
            os.startfile(ruta)
            return f"Abrí la carpeta {nombre}"
        except Exception:
            pass

    carpetas_base = [HOME, DESKTOP, DOCUMENTS, DOWNLOADS]

    for base in carpetas_base:
        if not os.path.exists(base):
            continue
        for root, dirs, _ in os.walk(base):
            depth = root.replace(base, "").rstrip("\\").count(os.sep)
            if depth > 4:
                dirs.clear()
                continue
            for d in dirs:
                if d.lower() == nombre:
                    ruta = os.path.join(root, d)
                    cache["folders"][nombre] = ruta
                    _guardar_cache(cache)
                    os.startfile(ruta)
                    return f"Abrí la carpeta {nombre}"

    ruta = _buscar_carpeta_en_unidades(nombre)
    if ruta:
        cache["folders"][nombre] = ruta
        _guardar_cache(cache)
        os.startfile(ruta)
        return f"Abrí la carpeta {nombre}"

    return f"No encontré la carpeta {nombre}"
