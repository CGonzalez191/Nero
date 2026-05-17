import os
import re

HOME = os.path.expanduser("~")
UBICACIONES = {
    "escritorio": os.path.join(HOME, "Desktop"),
    "documentos": os.path.join(HOME, "Documents"),
    "descargas": os.path.join(HOME, "Downloads"),
    "música": os.path.join(HOME, "Music"),
    "imágenes": os.path.join(HOME, "Pictures"),
    "videos": os.path.join(HOME, "Videos"),
}


def _detectar_ubicacion(texto):
    for nombre, ruta in UBICACIONES.items():
        if f" en {nombre}" in texto.lower() or f"en {nombre}" == texto.lower().split()[-2:]:
            return ruta
    return UBICACIONES["escritorio"]


def crear_archivo(texto):
    match = re.search(
        r"llamado\s+(.+?)(?:\s+(?:con\s+el\s+contenido|que\s+diga)\s+(.+))?$",
        texto,
        re.IGNORECASE
    )
    if not match:
        return None

    nombre = match.group(1).strip().strip('"\'').strip()
    contenido = match.group(2).strip().strip('"\'') if match.group(2) else ""

    if "." not in nombre:
        nombre += ".txt"

    destino = _detectar_ubicacion(texto)
    ruta = os.path.join(destino, nombre)

    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"Creé el archivo {nombre}"
    except Exception as e:
        return f"Error al crear archivo: {e}"


def crear_carpeta(texto):
    match = re.search(r"llamada\s+(.+?)(?:\s+en\s+.+)?$", texto, re.IGNORECASE)
    if not match:
        return None

    nombre = match.group(1).strip().strip('"\'').strip()
    destino = _detectar_ubicacion(texto)
    ruta = os.path.join(destino, nombre)

    try:
        os.makedirs(ruta, exist_ok=True)
        return f"Creé la carpeta {nombre}"
    except Exception as e:
        return f"Error al crear carpeta: {e}"


def leer_archivo(texto):
    match = re.search(r"(?:el\s+)?archivo\s+(.+)", texto, re.IGNORECASE)
    if not match:
        return None

    nombre = match.group(1).strip().strip('"\'').strip()

    for destino in UBICACIONES.values():
        ruta = os.path.join(destino, nombre)
        if os.path.isfile(ruta):
            break
        ruta_txt = ruta + ".txt"
        if os.path.isfile(ruta_txt):
            ruta = ruta_txt
            break
    else:
        return f"No encontré el archivo {nombre}"

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read(500)
        return f"El archivo {nombre} dice: {contenido}"
    except Exception as e:
        return f"Error al leer archivo: {e}"
