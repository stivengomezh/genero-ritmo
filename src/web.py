"""
web.py - Página web local del proyecto (Mini-Shazam: género musical por el ritmo).

    python main.py web          abre http://127.0.0.1:8000 en el navegador

La página (carpeta web/) deja subir un archivo de audio o grabar con el micrófono del
navegador y muestra el género, los votos, el tempo y el patrón de compás. El análisis lo
hace el mismo código del proyecto (carga.py, ritmo.py, caracteristicas.py, clasificador.py):
la página solo envía el audio y dibuja la respuesta.

No usa ninguna biblioteca adicional: el servidor es http.server de la biblioteca estándar.
Solo atiende en 127.0.0.1 (este computador); no queda visible en la red.

Rutas:
    GET  /                  página (web/index.html)
    GET  /img/...           imágenes de la página (web/img/)
    GET  /api/estado        canciones, fragmentos y géneros de la base
    POST /api/clasificar    cuerpo = bytes del audio (MP3, WAV, FLAC, OGG); cabecera X-Nombre
"""
import json
import mimetypes
import tempfile
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

import numpy as np

import config as C
from carga import cargar_audio, fragmentar, fragmentos_para_clasificar
from clasificador import carpeta_por_defecto, clasificar_senal, extraer_conjunto

CARPETA_WEB = C.CARPETA_PROYECTO / "web"
MAX_BYTES = 80 * 1024 * 1024            # tamaño máximo de un audio subido
EXTENSIONES = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}
ESTADO = {"datos": None, "carpeta": None}
CANDADO = threading.Lock()              # un análisis a la vez


def analizar_bytes(contenido, nombre):
    """Guarda el audio en un archivo temporal, lo clasifica y devuelve un diccionario JSON."""
    ext = Path(nombre).suffix.lower()
    if ext not in EXTENSIONES:
        raise ValueError(f"Formato no admitido ({ext or 'sin extensión'}). Use MP3, WAV, FLAC u OGG.")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / f"audio{ext}"
        ruta.write_bytes(contenido)
        y = cargar_audio(ruta)
    duracion = len(y) / C.SR
    if duracion < 3:
        raise ValueError(f"El audio dura {duracion:.1f} s; se necesitan al menos 3 s (lo ideal son 10 s o más).")
    nivel = 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)

    datos = ESTADO["datos"]
    stem = Path(nombre).stem.lower()
    excluir = stem if stem in set(datos["cancion"]) else None
    # canción completa: los mismos 24 fragmentos que usa la validación; audio corto: todos
    frags = fragmentos_para_clasificar(y) if duracion > 60 else fragmentar(y)
    t0 = time.perf_counter()
    res = clasificar_senal(y, datos=datos, excluir=excluir, frags=frags)
    return {
        "nombre": nombre,
        "genero": res["genero"],
        "nombre_genero": C.NOMBRES_GENERO.get(res["genero"], res["genero"]),
        "votos": [{"genero": g, "nombre": C.NOMBRES_GENERO.get(g, g), "p": round(float(p), 4)}
                  for g, p in res["probabilidades"].items()],
        "tempo": round(res["tempo"], 1) if np.isfinite(res["tempo"]) else None,
        "claridad": round(res["claridad"], 3),
        "duracion_s": round(duracion, 1),
        "nivel_dbfs": round(float(nivel), 1),
        "fragmentos": [{"t": round(float(t), 1), "genero": g} for t, g in res["por_fragmento"]],
        "patron": [[round(float(v), 3) for v in fila] for fila in res["patron"]],
        "bandas": list(C.NOMBRES_BANDA),
        "excluida": excluir is not None,
        "segundos_analisis": round(time.perf_counter() - t0, 1),
    }


def estado():
    d = ESTADO["datos"]
    presentes = set(d["genero"])
    generos = [g for g in C.GENEROS if g in presentes]
    return {"canciones": int(len(np.unique(d["cancion"]))), "fragmentos": int(len(d["X"])),
            "generos": [{"genero": g, "nombre": C.NOMBRES_GENERO.get(g, g)} for g in generos],
            "carpeta": ESTADO["carpeta"], "sinteticos": ESTADO["carpeta"] == C.CARPETA_SINTETICOS.name}


class Manejador(BaseHTTPRequestHandler):
    server_version = "MiniShazam/1.0"

    def log_message(self, formato, *args):          # registro corto en la terminal
        print(f"  [{time.strftime('%H:%M:%S')}] {formato % args}")

    def _json(self, objeto, codigo=200):
        cuerpo = json.dumps(objeto, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _archivo(self, ruta):
        ruta = ruta.resolve()
        if CARPETA_WEB.resolve() not in ruta.parents or not ruta.is_file():   # nada fuera de web/
            self.send_error(404, "No encontrado")
            return
        cuerpo = ruta.read_bytes()
        tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", tipo + ("; charset=utf-8" if tipo.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        ruta = unquote(self.path.split("?")[0])
        if ruta in ("/", "/index.html"):
            self._archivo(CARPETA_WEB / "index.html")
        elif ruta == "/api/estado":
            self._json(estado())
        else:
            self._archivo(CARPETA_WEB / ruta.lstrip("/"))

    def do_POST(self):
        if self.path != "/api/clasificar":
            self.send_error(404, "No encontrado")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n <= 0:
                raise ValueError("No llegó ningún audio.")
            if n > MAX_BYTES:
                raise ValueError(f"El archivo pesa más de {MAX_BYTES // 1024 // 1024} MB.")
            contenido = self.rfile.read(n)
            nombre = Path(unquote(self.headers.get("X-Nombre", "audio.wav"))).name
            with CANDADO:
                self._json(analizar_bytes(contenido, nombre))
        except (ValueError, RuntimeError, FileNotFoundError) as e:
            self._json({"error": str(e)}, 400)
        except Exception as e:                                   # noqa: BLE001 - se informa en la página
            self._json({"error": f"No se pudo analizar el audio ({type(e).__name__}: {e})"}, 500)


def servir(carpeta=None, puerto=8000, abrir=True):
    carpeta = Path(carpeta or carpeta_por_defecto())
    print("Preparando la base de canciones (la primera vez tarda varios minutos)...")
    ESTADO["datos"] = extraer_conjunto(carpeta)
    ESTADO["carpeta"] = carpeta.name
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    except OSError as e:
        raise RuntimeError(f"No se pudo usar el puerto {puerto} ({e}). Pruebe: python main.py web --puerto 8080")
    url = f"http://127.0.0.1:{puerto}"
    e = estado()
    print(f"\nMini-Shazam listo: {e['canciones']} canciones, {len(e['generos'])} géneros.")
    print(f"  Abra {url} en el navegador.   (Ctrl + C para detener)\n")
    if abrir:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()
