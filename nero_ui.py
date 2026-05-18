"""
Nero UI — Desktop voice assistant window (PyQt5 + WebSocket)
"""

import sys
import os
import json
import asyncio
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QUrl, QTimer, QObject, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
import websockets
import keyboard

from voice import hablar, escuchar
from main import procesar_comando, EXIT_COMMANDS

# ── WebSocket globals ──────────────────────────────────────────
connected_clients = set()
ws_loop = None
ws_ready = threading.Event()
stop_event = None

voice_lock = threading.Lock()


# ── Signals (thread-safe quit) ─────────────────────────────────
class AppSignals(QObject):
    quit_signal = pyqtSignal()

signals = AppSignals()


# ── WebSocket server ───────────────────────────────────────────
async def ws_handler(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.send(json.dumps({"event": "ready"}))
        async for _ in websocket:
            pass
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)


async def ws_server():
    global stop_event
    stop_event = asyncio.Event()
    async with websockets.serve(ws_handler, "localhost", 8765):
        ws_ready.set()
        await stop_event.wait()


def start_ws():
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)
    ws_loop.run_until_complete(ws_server())


def broadcast(data):
    if not ws_loop or not connected_clients:
        return
    msg = json.dumps(data)
    for c in connected_clients.copy():
        asyncio.run_coroutine_threadsafe(c.send(msg), ws_loop)


# ── Voice command handler ──────────────────────────────────────
def handle_voice():
    if not voice_lock.acquire(blocking=False):
        return

    try:
        broadcast({"event": "listening"})
        texto = escuchar()

        if texto is None:
            broadcast({"event": "error", "text": "No entend\u00ed, repite por favor"})
            return
        if texto == "":
            return

        broadcast({"event": "heard", "text": texto})
        broadcast({"event": "thinking"})

        respuesta = procesar_comando(texto)

        if respuesta == "salir":
            broadcast({"event": "response", "text": "Hasta luego"})
            hablar("Hasta luego")
            signals.quit_signal.emit()
            return

        if respuesta:
            hablar(respuesta)
            broadcast({"event": "response", "text": respuesta})
        else:
            broadcast({"event": "error", "text": "No entend\u00ed, repite por favor"})
    finally:
        voice_lock.release()


# ── PyQt5 window ───────────────────────────────────────────────
class NeroWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nero — Asistente de Voz")
        self.setFixedSize(540, 790)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.browser = QWebEngineView()
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.html")
        self.browser.setUrl(QUrl.fromLocalFile(ui_path))
        layout.addWidget(self.browser)

    def closeEvent(self, event):
        keyboard.unhook_all()
        if ws_loop and stop_event is not None:
            ws_loop.call_soon_threadsafe(stop_event.set)
        event.accept()


# ── Entry point ────────────────────────────────────────────────
def main():
    ws_thread = threading.Thread(target=start_ws, daemon=True)
    ws_thread.start()
    ws_ready.wait(timeout=5)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    signals.quit_signal.connect(app.quit)

    window = NeroWindow()
    window.show()

    QTimer.singleShot(800, lambda: keyboard.add_hotkey(
        "ctrl+shift+n",
        lambda: threading.Thread(target=handle_voice, daemon=True).start(),
    ))

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
