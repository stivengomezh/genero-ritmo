"""
sinteticos.py - Genera ritmos sintéticos de cada género para probar el sistema.

NO reemplazan a las canciones reales: sirven para que el código se pueda ejecutar y
verificar sin descargar nada, y para tener un caso de control donde se conoce el
patrón exacto de cada género. Cada "canción" se arma sumando instrumentos de
percusión sintetizados (senoides con caída exponencial y ruido filtrado), un bajo
y acordes, sobre una rejilla de 16 pasos por compás, con variaciones aleatorias
de tempo, tiempo (desviación de 4 ms), intensidad, volumen de cada instrumento y notas omitidas.

Uso:  python main.py sinteticos          (4 canciones de 30 s por género en data/sinteticos/)
"""
import numpy as np
from scipy import signal
from scipy.io import wavfile

import config as C

FS = 44100  # se generan a 44,1 kHz (como un MP3 real) para probar también el remuestreo


# ============================================================ Instrumentos
def _env(n, caida_s, fs=FS):
    t = np.arange(n) / fs
    return np.exp(-t / caida_s)


def _ruido_banda(n, f1, f2, rng, fs=FS):
    sos = signal.butter(4, [f1, min(f2, fs / 2 * 0.95)], btype="band", fs=fs, output="sos")
    return signal.sosfilt(sos, rng.standard_normal(n))


def bombo(rng):
    n = int(0.35 * FS)
    t = np.arange(n) / FS
    f = 45 + 90 * np.exp(-t / 0.03)                 # barrido de 135 a 45 Hz
    return np.sin(2 * np.pi * np.cumsum(f) / FS) * _env(n, 0.12) * 1.2


def caja(rng):
    n = int(0.25 * FS)
    t = np.arange(n) / FS
    return 0.7 * _ruido_banda(n, 1200, 6000, rng) * _env(n, 0.06) + 0.5 * np.sin(2 * np.pi * 190 * t) * _env(n, 0.04)


def palmas(rng):
    n = int(0.25 * FS)
    e = np.zeros(n)
    for d in (0, 0.011, 0.022):
        i = int(d * FS)
        e[i:] += _env(n - i, 0.012 if d < 0.02 else 0.08)
    return 0.8 * _ruido_banda(n, 900, 3500, rng) * e


def hihat(rng, abierto=False):
    n = int((0.25 if abierto else 0.06) * FS)
    return 0.35 * _ruido_banda(n, 7000, 16000, rng) * _env(n, 0.09 if abierto else 0.015)


def raspado(rng, largo=0.05):
    """Güira / guacharaca / güiro: ruido agudo modulado en amplitud (las estrías del instrumento)."""
    n = int(largo * FS)
    t = np.arange(n) / FS
    am = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 320 * t))
    return 0.45 * _ruido_banda(n, 3000, 9000, rng) * am * np.sin(np.pi * np.arange(n) / n)


def maraca(rng):
    n = int(0.05 * FS)
    return 0.25 * _ruido_banda(n, 4500, 12000, rng) * _env(n, 0.018)


def campana(rng):
    n = int(0.2 * FS)
    t = np.arange(n) / FS
    tono = signal.square(2 * np.pi * 562 * t) + signal.square(2 * np.pi * 845 * t)
    sos = signal.butter(2, [400, 2500], btype="band", fs=FS, output="sos")
    return 0.25 * signal.sosfilt(sos, tono) * _env(n, 0.06)


def tambor(rng, f0=220, caida=0.12):
    """Conga, bongó, tambor alegre o caja vallenata: senoide con leve caída de tono."""
    n = int(0.3 * FS)
    t = np.arange(n) / FS
    f = f0 * (1 + 0.25 * np.exp(-t / 0.01))
    return (0.8 * np.sin(2 * np.pi * np.cumsum(f) / FS) + 0.15 * _ruido_banda(n, 800, 4000, rng)) * _env(n, caida)


def clave(rng):
    n = int(0.06 * FS)
    t = np.arange(n) / FS
    return 0.5 * np.sin(2 * np.pi * 2500 * t) * _env(n, 0.012)


def nota(f0, dur_s, timbre="bajo", rng=None):
    n = int(dur_s * FS)
    t = np.arange(n) / FS
    if timbre == "bajo":
        x = np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(4 * np.pi * f0 * t)
        return 0.55 * x * _env(n, max(0.15, dur_s * 0.6)) * (1 - np.exp(-t / 0.005))
    if timbre == "distorsion":
        x = np.tanh(4 * (signal.sawtooth(2 * np.pi * f0 * t) + signal.sawtooth(2 * np.pi * f0 * 1.5 * t)))
        return 0.12 * x * (1 - np.exp(-t / 0.01))
    if timbre == "pad":
        x = signal.sawtooth(2 * np.pi * f0 * t) + signal.sawtooth(2 * np.pi * f0 * 1.003 * t)
        sos = signal.butter(2, 1800, fs=FS, output="sos")
        return 0.05 * signal.sosfilt(sos, x) * np.minimum(1, t / 0.08)
    # piano / guitarra: armónicos con caída
    x = sum(np.sin(2 * np.pi * f0 * k * t) / k ** 1.5 for k in range(1, 6))
    return 0.12 * x * _env(n, 0.25 if timbre == "guitarra" else 0.8)


def acorde(raiz, dur_s, timbre, menor=False):
    tercera = 2 ** ((3 if menor else 4) / 12)
    return sum(nota(raiz * r, dur_s, timbre) for r in (1, tercera, 1.5))


# ============================================================ Patrones (32 pasos = 2 compases de 16 semicorcheas)
def _cada(paso, inicio=0, total=32):
    return list(range(inicio, total, paso))


def _rep(pasos):
    """Repite un patrón de 1 compás (16 pasos) en los 2 compases."""
    return sorted(set(pasos + [p + 16 for p in pasos]))


GENEROS_SINT = {
    # nombre: (rango de BPM, {instrumento: [pasos]}, pasos del bajo, pasos de acordes, timbre de acordes)
    "reggaeton": ((88, 100), {"bombo": _rep([0, 4, 8, 12]), "caja": _rep([3, 6, 11, 14]),
                              "hihat": _cada(2)}, _rep([0, 3, 6, 8, 11, 14]), _cada(16), "pad"),
    "salsa": ((165, 195), {"clave": [0, 6, 12, 20, 24], "campana": _cada(4), "conga": _rep([6, 7, 14, 15]),
                           "bongo": _cada(2, 1), "maraca": _cada(2), "bombo": [12, 28]},
              _rep([6, 12]), _rep([0, 3, 6, 10, 12, 14]), "piano"),
    "bachata": ((122, 138), {"guira": _cada(2) + _rep([1, 9]), "bongo": _cada(2), "bongo_slap": _rep([12]),
                             "conga": _rep([10, 14])}, _rep([0, 6, 8, 14]), _cada(2, 1), "guitarra"),
    "vallenato": ((95, 112), {"guacharaca": _cada(1), "caja_v": _rep([0, 6, 8, 12, 14]), "bombo": _rep([0, 8])},
                  _rep([0, 6, 8, 14]), _rep([4, 12]), "piano"),
    "cumbia": ((85, 98), {"guacharaca": _cada(2) + _rep([1, 5, 9, 13]), "tambor": _rep([4, 12]), "maraca": _cada(2),
                          "bombo": _rep([0, 8])}, _rep([0, 6, 8, 14]), _rep([2, 6, 10, 14]), "guitarra"),
    "rock": ((110, 140), {"bombo": _rep([0, 8, 10]), "caja": _rep([4, 12]), "hihat": _cada(2)},
             _cada(2), _cada(8), "distorsion"),
    "electronica": ((122, 130), {"bombo": _cada(4), "palmas": _rep([4, 12]), "hihat_abierto": _cada(4, 2),
                                 "maraca": _cada(1)}, _cada(4, 2), _cada(32), "pad"),
    "balada": ((62, 78), {"bombo": _rep([0, 10]), "caja": _rep([4, 12]), "hihat": _cada(2)},
              _cada(16), _cada(16), "piano"),
}

VOLUMEN = {"bombo": 1.0, "caja": 0.8, "palmas": 0.8, "hihat": 0.6, "hihat_abierto": 0.5, "guira": 0.7,
           "guacharaca": 0.7, "maraca": 0.5, "campana": 0.8, "conga": 0.7, "bongo": 0.5, "bongo_slap": 0.8,
           "tambor": 0.8, "caja_v": 0.8, "clave": 0.7}


def _sonido(nombre, rng):
    if nombre == "bombo": return bombo(rng)
    if nombre == "caja": return caja(rng)
    if nombre == "palmas": return palmas(rng)
    if nombre == "hihat": return hihat(rng)
    if nombre == "hihat_abierto": return hihat(rng, abierto=True)
    if nombre in ("guira", "guacharaca"): return raspado(rng, 0.04 if nombre == "guira" else 0.06)
    if nombre == "maraca": return maraca(rng)
    if nombre == "campana": return campana(rng)
    if nombre == "conga": return tambor(rng, 210, 0.12)
    if nombre == "bongo": return tambor(rng, 420, 0.06)
    if nombre == "bongo_slap": return tambor(rng, 480, 0.04) + 0.5 * _ruido_banda(int(0.3 * FS), 2000, 6000, rng) * _env(int(0.3 * FS), 0.02)
    if nombre == "tambor": return tambor(rng, 180, 0.15)
    if nombre == "caja_v": return tambor(rng, 260, 0.09)
    if nombre == "clave": return clave(rng)
    raise ValueError(nombre)


PROGRESIONES = [[(110.0, True), (87.3, False), (130.8, False), (98.0, False)],      # Am F C G
                [(98.0, False), (130.8, False), (146.8, False), (98.0, False)],     # G C D G
                [(146.8, True), (116.5, False), (87.3, False), (130.8, False)],     # Dm Bb F C
                [(82.4, True), (130.8, False), (98.0, False), (146.8, False)]]      # Em C G D


def generar_cancion(genero, duracion_s=30.0, semilla=0):
    """Sintetiza una canción del género indicado. Devuelve (x a 44,1 kHz, bpm)."""
    rng = np.random.default_rng(semilla)
    (bpm_min, bpm_max), patrones, pasos_bajo, pasos_acorde, timbre = GENEROS_SINT[genero]
    bpm = rng.uniform(bpm_min, bpm_max)
    paso_s = 60 / bpm / 4
    n = int(duracion_s * FS)
    x = np.zeros(n + FS)
    ganancia = {k: VOLUMEN[k] * 10 ** (rng.uniform(-3, 3) / 20) for k in patrones}
    swing = rng.uniform(0, 0.08) * paso_s            # leve retraso de las semicorcheas impares
    progresion = PROGRESIONES[rng.integers(len(PROGRESIONES))]
    transposicion = 2 ** (rng.integers(-2, 3) / 12)
    n_ciclos = int(np.ceil(duracion_s / (32 * paso_s)))

    def poner(sonido, t_s, vel):
        i = int(t_s * FS)
        if 0 <= i < len(x):
            j = min(len(x), i + len(sonido))
            x[i:j] += vel * sonido[:j - i]

    for ciclo in range(n_ciclos):
        t0 = ciclo * 32 * paso_s
        variacion = rng.random() < 0.15                  # de vez en cuando un ciclo con notas omitidas
        for inst, pasos in patrones.items():
            for p in pasos:
                if rng.random() < (0.25 if variacion else 0.05):
                    continue
                t = t0 + p * paso_s + (swing if p % 2 else 0) + rng.normal(0, 0.004)
                vel = ganancia[inst] * rng.uniform(0.75, 1.0) * (1.0 if p % 4 == 0 else 0.85)
                poner(_sonido(inst, rng), t, vel)
        for compas in range(2):
            raiz, menor = progresion[(2 * ciclo + compas) % 4]
            raiz *= transposicion
            for p in pasos_bajo:
                if compas * 16 <= p < (compas + 1) * 16:
                    poner(nota(raiz / 2, min(0.5, 3 * paso_s), "bajo"), t0 + p * paso_s + rng.normal(0, 0.003),
                          rng.uniform(0.8, 1.0))
            for p in pasos_acorde:
                if compas * 16 <= p < (compas + 1) * 16:
                    dur = (16 if timbre in ("pad", "distorsion") else 2) * paso_s
                    if timbre == "distorsion":
                        dur = 8 * paso_s
                    poner(acorde(raiz, dur, timbre, menor), t0 + p * paso_s, rng.uniform(0.7, 1.0))
    # reverberación corta (respuesta al impulso de ruido con caída exponencial) y normalización
    ir = rng.standard_normal(int(0.3 * FS)) * _env(int(0.3 * FS), 0.06)
    ir[0] = 6.0
    x = signal.fftconvolve(x, ir / np.sqrt(np.sum(ir ** 2)))[:n]
    x = np.tanh(1.5 * x / (np.max(np.abs(x)) + 1e-12)) / np.tanh(1.5)    # compresión suave, como una mezcla real
    return 0.89 * x.astype(np.float32), bpm


def generar_todo(por_genero=4, duracion_s=30.0, carpeta=C.CARPETA_SINTETICOS):
    carpeta.mkdir(parents=True, exist_ok=True)
    print(f"Generando {por_genero} ritmos sintéticos de {duracion_s:g} s por género en {carpeta}")
    filas = []
    for gi, genero in enumerate(GENEROS_SINT):
        for k in range(por_genero):
            x, bpm = generar_cancion(genero, duracion_s, semilla=1000 * gi + k)
            ruta = carpeta / f"{genero}_{k + 1:02d}.wav"
            wavfile.write(ruta, FS, (x * 32767).astype(np.int16))
            filas.append((ruta.name, genero, bpm))
            print(f"  {ruta.name:<22} {bpm:6.1f} BPM")
    with open(carpeta / "tempos_reales.csv", "w", encoding="utf-8") as fh:
        fh.write("archivo,genero,bpm\n")
        for nombre, genero, bpm in filas:
            fh.write(f"{nombre},{genero},{bpm:.2f}\n")
    return filas
