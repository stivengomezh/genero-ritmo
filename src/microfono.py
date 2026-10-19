"""
microfono.py - Grabación de un fragmento desde el micrófono (pip install sounddevice).

Se graba a la frecuencia nativa del micrófono (44 100 o 48 000 Hz, porque muchas tarjetas
no aceptan otras) y luego se remuestrea a SR con el mismo filtro que se usa para las canciones.
"""
import time
from datetime import datetime

import numpy as np
from scipy.io import wavfile

import config as C
from carga import remuestrear, normalizar


def grabar(segundos=C.SEGUNDOS_GRABACION, guardar=True, dispositivo=None):
    try:
        import sounddevice as sd
    except (ImportError, OSError) as e:
        raise RuntimeError("No se pudo cargar 'sounddevice'. Instálelo con:  pip install sounddevice") from e
    info = sd.query_devices(dispositivo, kind="input")
    fs = int(info["default_samplerate"])
    print(f"Micrófono: {info['name']} ({fs} Hz)")
    for k in (3, 2, 1):
        print(f"  Grabando en {k}...", end="\r", flush=True)
        time.sleep(1)
    print(f"  GRABANDO {segundos:g} s - acerque el micrófono a la música    ")
    audio = sd.rec(int(segundos * fs), samplerate=fs, channels=1, dtype="float32", device=dispositivo)
    sd.wait()
    audio = audio[:, 0]
    nivel = 20 * np.log10(np.sqrt(np.mean(audio ** 2)) + 1e-12)
    print(f"  Grabación terminada (nivel {nivel:.0f} dBFS).")
    if nivel < -50:
        print("  Atención: el nivel es muy bajo. ¿El micrófono está activo?")
    if guardar:
        C.CARPETA_GRABACIONES.mkdir(parents=True, exist_ok=True)
        ruta = C.CARPETA_GRABACIONES / f"grabacion_{datetime.now():%Y%m%d_%H%M%S}.wav"
        wavfile.write(ruta, fs, (np.clip(audio, -1, 1) * 32767).astype(np.int16))
        print(f"  Guardada en {ruta}")
    return normalizar(remuestrear(audio, fs, C.SR))
