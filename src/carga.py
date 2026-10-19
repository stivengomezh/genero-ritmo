"""
carga.py - Lectura de los audios, preprocesamiento y segmentación en fragmentos.

    archivo --> muestras en [-1, 1] --> mono --> filtro antialiasing + cambio de tasa a SR
            --> sin componente DC y con amplitud máxima 1 --> fragmentos de SEGMENTO_S segundos
"""
import json
import shutil
import subprocess
from math import gcd
from pathlib import Path

import numpy as np
from scipy import signal

import config as C


# ============================================================ Lectura
def cargar_original(ruta):
    """Lee el archivo tal como viene: devuelve (x, fs) con x de forma (canales, N) en [-1, 1].

    Intenta, en orden: soundfile (WAV, MP3, FLAC, OGG), librosa, scipy (solo WAV) y ffmpeg.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo {ruta}")
    try:
        import soundfile as sf
        x, fs = sf.read(str(ruta), dtype="float32", always_2d=True)
        return np.ascontiguousarray(x.T), int(fs)
    except Exception:  # librería no instalada o formato que no soporta (por ejemplo .m4a)
        pass
    try:
        import librosa
        x, fs = librosa.load(str(ruta), sr=None, mono=False)
        return np.atleast_2d(x).astype(np.float32), int(fs)
    except ImportError:
        pass
    if ruta.suffix.lower() == ".wav":
        from scipy.io import wavfile
        try:
            fs, x = wavfile.read(str(ruta))
            return np.atleast_2d(a_flotante(x).T), int(fs)
        except ValueError:
            pass  # WAV comprimido u otro formato con extensión .wav
    return _cargar_con_ffmpeg(ruta)


def _cargar_con_ffmpeg(ruta):
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError(f"No se puede leer {Path(ruta).name}: instale soundfile (py -m pip install soundfile) "
                           f"o convierta el archivo a MP3 o WAV.")
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate,channels",
         "-of", "json", str(ruta)], capture_output=True, check=True, text=True).stdout)["streams"][0]
    fs, canales = int(info["sample_rate"]), int(info["channels"])
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, dtype=np.float32).reshape(-1, canales).T.copy(), fs


def a_flotante(y):
    """Convierte muestras enteras (int16, int32, uint8) a float en [-1, 1]."""
    if np.issubdtype(y.dtype, np.integer):
        info = np.iinfo(y.dtype)
        y = (y.astype(np.float64) - (info.max + info.min + 1) / 2) / (info.max + 1)
    return y.astype(np.float32)


# ============================================================ Preprocesamiento
def remuestrear(y, fs_original, fs_destino=C.SR):
    """Cambia la frecuencia de muestreo con un filtro polifásico (incluye el filtro antialiasing).

    Ejemplo 44 100 -> 22 050 Hz: interpola por 1, filtra pasabajos en 11 025 Hz y diezma por 2.
    """
    if fs_original == fs_destino:
        return np.asarray(y, dtype=np.float32)
    g = gcd(int(fs_original), int(fs_destino))
    return signal.resample_poly(y, int(fs_destino) // g, int(fs_original) // g).astype(np.float32)


def normalizar(y):
    """Resta la media (componente DC) y escala para que el máximo absoluto sea 1."""
    y = np.asarray(y, dtype=np.float32)
    y = y - y.mean()
    pico = float(np.max(np.abs(y))) if y.size else 0.0
    return y / pico if pico > 0 else y


def cargar_audio(ruta, sr=C.SR):
    """Lee un archivo y lo deja listo para el análisis: mono, a `sr` Hz, sin DC, máximo 1."""
    x, fs = cargar_original(ruta)
    return normalizar(remuestrear(x.mean(axis=0), fs, sr))


# ============================================================ Organización de los datos
def genero_de_archivo(ruta):
    """El género es la primera parte del nombre del archivo: 'reggaeton_03.mp3' -> 'reggaeton'."""
    nombre = Path(ruta).stem.lower()
    for g in sorted(C.GENEROS, key=len, reverse=True):
        if nombre.startswith(g):
            return g
    return None


def listar_canciones(carpeta=C.CARPETA_CANCIONES):
    """Lista [(ruta, genero)] de los audios de la carpeta cuyo nombre empieza por un género conocido."""
    carpeta = Path(carpeta)
    if not carpeta.exists():
        return []
    salida = []
    for p in sorted(carpeta.iterdir()):
        if p.suffix.lower() in C.EXTENSIONES_AUDIO:
            g = genero_de_archivo(p)
            if g is None:
                print(f"  (se omite {p.name}: el nombre no empieza por un género de {C.GENEROS})")
            else:
                salida.append((p, g))
    return salida


def carpeta_por_defecto():
    """Usa las canciones reales si existen; si no, los ritmos sintéticos de demostración."""
    if listar_canciones(C.CARPETA_CANCIONES):
        return C.CARPETA_CANCIONES
    return C.CARPETA_SINTETICOS


# ============================================================ Segmentación
def fragmentar(y, sr=C.SR, segmento_s=C.SEGMENTO_S, solape=C.SOLAPE):
    """Divide la señal en fragmentos de `segmento_s` segundos que avanzan segmento_s·(1 - solape).

    Devuelve una lista de (inicio_s, fragmento). Si la señal es más corta que un fragmento,
    se devuelve completa como único fragmento.
    """
    n = int(segmento_s * sr)
    paso = max(1, int(n * (1 - solape)))
    if len(y) <= n:
        return [(0.0, y)]
    return [(i / sr, y[i:i + n]) for i in range(0, len(y) - n + 1, paso)]


def fragmentos_para_clasificar(y, sr=C.SR, maximo=C.MAX_FRAGMENTOS, recorte_s=C.RECORTE_S):
    """Fragmentos que se usan para entrenar y evaluar: sin introducción ni final (si la canción
    es lo bastante larga) y como máximo `maximo`, repartidos uniformemente a lo largo de la canción."""
    frags = fragmentar(y, sr)
    dur = len(y) / sr
    if dur > 2 * recorte_s + 3 * C.SEGMENTO_S:
        frags = [(ini, f) for ini, f in frags if ini >= recorte_s and ini + C.SEGMENTO_S <= dur - recorte_s]
    if len(frags) > maximo:
        idx = np.round(np.linspace(0, len(frags) - 1, maximo)).astype(int)
        frags = [frags[i] for i in idx]
    return frags
