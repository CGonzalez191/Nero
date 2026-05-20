import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice import hablar, escuchar
from commands.apps import abrir_aplicacion, abrir_carpeta, instalar_juego_steam
from commands.files import crear_archivo, crear_carpeta, leer_archivo
from commands.browser import abrir_sitio, buscar_en_web, SITIOS
from commands.system import (
    cambiar_volumen, decir_hora, decir_fecha,
    tomar_captura, cancelar_apagado,
    cerrar_aplicacion, cerrar_ventana_activa,
)
EXIT_COMMANDS = ["salir", "adiós", "adios", "chao", "termina"]


def procesar_comando(texto):
    t = texto.lower().strip()

    # --- Salir ---
    if t in EXIT_COMMANDS:
        return "salir"

    # --- Cancelar apagado ---
    if re.search(r"cancela(r)?\s+(el\s+)?apagado", t):
        return cancelar_apagado()

    # --- Volumen ---
    if t in ("silencia", "silenciar", "silencio"):
        return cambiar_volumen("silenciar")
    if t in ("activa el sonido", "activar sonido", "activa sonido", "activar"):
        return cambiar_volumen("activar")
    if re.search(r"(sube|subí|subir)\s+(el\s+)?volumen", t):
        return cambiar_volumen("subir")
    if re.search(r"(baja|bajá|bajar)\s+(el\s+)?volumen", t):
        return cambiar_volumen("bajar")

    # --- Hora ---
    if t in ("qué hora es", "que hora es", "dime la hora", "decime la hora"):
        return decir_hora()

    # --- Fecha ---
    if t in ("qué día es", "que dia es", "dime el día", "dime el dia", "decime el día", "decime el dia"):
        return decir_fecha()

    # --- Captura ---
    if re.search(r"toma\s+una\s+captura", t) or re.search(r"saca\s+una\s+foto", t) or "captura de pantalla" in t:
        return tomar_captura()

    # --- Buscar en web con motor explícito ---
    match = re.search(r"busca\s+en\s+(\w+)\s+(.+)", t)
    if match:
        return buscar_en_web(match.group(2).strip(), match.group(1))

    # --- Búsquedas semánticas (motor por defecto) ---
    match = re.search(r"(?:qué|que)\s+(?:es|significa)\s+(.+)", t)
    if match:
        return buscar_en_web(match.group(1).strip())

    match = re.search(r"(?:dime|cuéntame|cuentame|háblame|hablame|decime)\s+(?:sobre|de)\s+(.+)", t)
    if match:
        return buscar_en_web(match.group(1).strip())

    match = re.search(r"explica(?:me)?\s+(.+)", t)
    if match:
        return buscar_en_web(match.group(1).strip())

    match = re.search(r"investiga\s+(.+)", t)
    if match:
        return buscar_en_web(match.group(1).strip())

    # --- "busca X" sin motor (usa default) ---
    match = re.search(r"busca\s+(.+)", t)
    if match:
        return buscar_en_web(match.group(1).strip())

    # --- Instalar en Steam ---
    match = re.search(r"(?:instala|instalar)\s+(.+?)\s+en\s+steam", t)
    if match:
        return instalar_juego_steam(match.group(1).strip())

    # --- Leer archivo ---
    match = re.search(r"(lee|leé)\s+(el\s+)?archivo\s+(.+)", t)
    if match:
        return leer_archivo(match.group(3).strip())

    # --- Crear carpeta ---
    match = re.search(r"crea\s+una\s+carpeta\s+llamad[ao]\s+(.+)", t)
    if match:
        return crear_carpeta(match.group(1).strip())

    # --- Crear archivo ---
    match = re.search(r"crea\s+un\s+archivo\s+llamado\s+(.+)", t)
    if match:
        return crear_archivo(match.group(1).strip())

    # --- Cerrar aplicación ---
    match = re.search(r"(?:cierra|cerrá|cerrar)\s+(.+)", t)
    if match:
        query = match.group(1).strip().lower()
        if query in ("la ventana", "ventana", "esta ventana", "la pestaña", "pestaña"):
            return cerrar_ventana_activa()
        if query in ("todo", "todo"):
            return "No voy a cerrar todo por si acaso"
        return cerrar_aplicacion(query)

    # --- Abrir carpeta (antes que "abre" genérico) ---
    match = re.search(r"(?:abre|abrí|abrir)\s+(?:la\s+)?carpeta\s+(.+)", t)
    if match:
        return abrir_carpeta(match.group(1).strip())

    # --- Abrir (sitio o app) ---
    match = re.search(r"(?:abre|abrí|abrir)\s+(.+)", t)
    if match:
        query = match.group(1).strip().lower()
        for key in SITIOS:
            if key in query:
                return abrir_sitio(key)
        return abrir_aplicacion(query)

    # --- Sitio directo (ej: solo "youtube") ---
    for key in SITIOS:
        if t == key or t.startswith(key + " ") or t.endswith(" " + key) or (" " + key + " ") in t:
            return abrir_sitio(key)

    return None


def main():
    hablar("Nero listo")
    print("[Nero] Nero listo")

    while True:
        print("[Nero] Escuchando... (di 'salir' para terminar)")
        texto = escuchar()

        if texto is None:
            hablar("No entendí, repite por favor")
            continue
        if texto == "":
            continue

        print(f"[Tú] {texto}")
        print("[Nero] Buscando...")

        respuesta = procesar_comando(texto)

        if respuesta == "salir":
            hablar("Hasta luego")
            print("[Nero] Hasta luego")
            break
        elif respuesta:
            print(f"[Nero] {respuesta}")
            hablar(respuesta)
        else:
            hablar("No entendí, repite por favor")


if __name__ == "__main__":
    main()
