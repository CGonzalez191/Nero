# Nero - Asistente de voz

Asistente de voz en español para Windows. Reconoce comandos por voz y puede abrir aplicaciones, sitios web, juegos de Steam, controlar volumen, tomar capturas, etc.

## Requisitos

- Python 3.10+
- Conexión a internet (para reconocimiento por Google Speech)

## Instalación
bash
pip install -r requirements.txt

Uso
python main.py
Comandos disponibles

"abrir youtube / facebook / github / etc" — abre sitios web
"abrir steam / chrome / discord / etc" — abre aplicaciones
"abrir [nombre del juego]" — abre juegos de Steam
"busca en google [consulta]"
"sube / baja volumen", "silencia", "activa el sonido"
"qué hora es", "qué día es"
"toma una captura"
"crea un archivo / carpeta llamado..."
"lee el archivo [nombre]"
"cancela el apagado"
"salir" — cierra el asistente


Modelo Vosk (fallback offline)
Si no hay internet, descargá https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip y extraelo en modelos/. ``
