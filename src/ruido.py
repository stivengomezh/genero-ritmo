"""
ruido.py - Degradaciones controladas de la señal (para estudiar la robustez).

    ruido blanco gaussiano   densidad espectral plana: igual potencia en todas las frecuencias
    ruido rosa               densidad 1/f: más energía en graves, parecido al ruido ambiente
    filtro de micrófono      pasabanda Butterworth de orden 4 entre 300 y 3 400 Hz (celular / teléfono)

La cantidad de ruido se fija con la relación señal/ruido:  SNR = 10·log10(P_señal / P_ruido) dB.
"""
import numpy as np
from scipy import signal

import config as C


def ruido_blanco(n, rng):
    return rng.standard_normal(n)


def ruido_rosa(n, rng):
    """Ruido blanco filtrado en frecuencia por 1/√f: la potencia queda proporcional a 1/f."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.arange(len(X), dtype=float)
    f[0] = 1.0
    return np.fft.irfft(X / np.sqrt(f), n)


def agregar_ruido(y, snr_db, rng, tipo="blanco"):
    """Suma ruido escalado para obtener exactamente la SNR pedida."""
    r = ruido_rosa(len(y), rng) if tipo == "rosa" else ruido_blanco(len(y), rng)
    p_senal = np.mean(np.asarray(y, dtype=np.float64) ** 2)
    r *= np.sqrt(p_senal / 10 ** (snr_db / 10) / np.mean(r ** 2))
    return (y + r).astype(np.float32)


def filtro_microfono(y, sr=C.SR, f_baja=300, f_alta=3400):
    sos = signal.butter(4, [f_baja, f_alta], btype="band", fs=sr, output="sos")
    return signal.sosfilt(sos, y).astype(np.float32)
