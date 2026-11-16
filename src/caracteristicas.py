"""
caracteristicas.py - Vector de características rítmicas de un fragmento de audio.

Cada fragmento de 10 s se resume en un vector de números que describen su ritmo.
Todos se calculan a partir de las envolventes de ataques (ritmo.py):

  Grupo              Qué mide                                                       Cant.
  ----------------   ------------------------------------------------------------   -----
  tempo              log2(BPM / 110): qué tan rápido es el pulso                        1
  claridad           R[P]: qué tan regular y marcado es el pulso (0 a 1)                1
  subdivisión        R en P/4, P/3, P/2, 2P/3, 3P/4, 3P/2, 2P: binario o ternario,       7
                     si hay semicorcheas, si el patrón se repite cada 2 pulsos
  energía por banda  fracción de los ataques en graves / medios / agudos                3
  densidad           ataques por segundo en cada banda                                   3
  regularidad        claridad del pulso en cada banda                                    3
  posición           en cada banda: fracción de energía del patrón en los pulsos,       9
                     en los contratiempos (corcheas) y en las semicorcheas
  forma del patrón   |DFT| del patrón de 16 pasos, armónicos 1 a 8, en cada banda       24
                     (no cambia si el patrón se desplaza en el tiempo)
  dinámica           desviación estándar del nivel RMS (dB) en ventanas de 0,5 s         1
  percusividad       fracción de la energía que es percusiva (golpes) y no armónica       3
                     (notas sostenidas), en cada banda; separación por filtros de
                     mediana sobre el espectrograma (HPSS, Fitzgerald 2010)
  fuerza             fuerza media de los ataques (flujo espectral / nivel) y rango         2
                     dinámico p90 - p10 del RMS en dB
                                                                                ----------
                                                                                       57

Los grupos tienen tamaños muy distintos (24 valores de |DFT| frente a 1 de tempo); por eso el
clasificador da a cada grupo el mismo peso total (pesos_por_grupo) y ningún grupo domina.
"""
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import find_peaks

import config as C
from ritmo import analizar_ritmo, autocorrelacion, _interpolar, estimar_tempo

FRACCIONES = [(1 / 4, "1/4"), (1 / 3, "1/3"), (1 / 2, "1/2"), (2 / 3, "2/3"), (3 / 4, "3/4"), (3 / 2, "3/2"),
              (2, "2")]


def nombres_caracteristicas():
    n = ["tempo_log2", "claridad"]
    n += [f"R_{t}P" for _, t in FRACCIONES]
    n += [f"energia_{b}" for b in C.NOMBRES_BANDA]
    n += [f"densidad_{b}" for b in C.NOMBRES_BANDA]
    n += [f"regularidad_{b}" for b in C.NOMBRES_BANDA]
    for b in C.NOMBRES_BANDA:
        n += [f"pulso_{b}", f"contratiempo_{b}", f"semicorchea_{b}"]
    for b in C.NOMBRES_BANDA:
        n += [f"dft{k}_{b}" for k in range(1, 9)]
    n += ["dinamica_dB"]
    n += [f"percusividad_{b}" for b in C.NOMBRES_BANDA]
    n += ["fuerza_ataques", "rango_dB"]
    return n


GRUPOS_PESO = [("tempo",), ("claridad", "R_"), ("energia", "densidad", "regularidad"),
               ("pulso", "contratiempo", "semicorchea"), ("dft",), ("dinamica",), ("percusividad",),
               ("fuerza", "rango")]


def pesos_por_grupo(nombres=None):
    """Peso de cada característica = 1 / sqrt(tamaño de su grupo).

    En la distancia euclidiana un grupo de n características estandarizadas aporta en
    promedio n veces más que una sola; con este peso cada grupo aporta lo mismo."""
    nombres = nombres or nombres_caracteristicas()
    w = np.ones(len(nombres))
    for prefijos in GRUPOS_PESO:
        idx = [i for i, x in enumerate(nombres) if x.startswith(prefijos)]
        w[idx] = 1 / np.sqrt(len(idx))
    return w


def densidad_ataques(e, umbral_rel=0.3, separacion_s=0.07):
    """Ataques por segundo: picos de la envolvente normalizada que superan el 30 % del máximo
    y están separados al menos 70 ms (el límite de golpes que se perciben separados)."""
    if not np.any(e):
        return 0.0
    picos, _ = find_peaks(e / e.max(), height=umbral_rel, distance=max(1, int(separacion_s * C.FS_ENV)))
    return len(picos) / (len(e) / C.FS_ENV)


PISO_DB = -60.0   # por debajo de -60 dBFS se considera silencio (evita que el silencio digital
                  # del final de una canción, -120 dB, se cuente como contraste de volumen)


def nivel_db(bloques):
    """Nivel RMS en dBFS de cada fila de `bloques`, con piso en PISO_DB."""
    rms = np.sqrt(np.mean(bloques ** 2, axis=1))
    return np.maximum(20 * np.log10(rms + 1e-12), PISO_DB)


def dinamica_db(y, ventana_s=0.5):
    n = int(ventana_s * C.SR)
    m = (len(y) // n) * n
    if m == 0:
        return 0.0
    return float(np.std(nivel_db(y[:m].reshape(-1, n))))


def percusividad(S, f, ancho=17):
    """Fracción percusiva de la energía en cada banda.

    En el espectrograma un golpe es una línea VERTICAL (muchas frecuencias en un instante) y
    una nota sostenida es una línea HORIZONTAL (una frecuencia durante mucho tiempo). Un
    filtro de mediana a lo largo del tiempo conserva lo horizontal (H) y uno a lo largo de la
    frecuencia conserva lo vertical (P). La máscara P²/(H²+P²) dice qué parte es golpe."""
    H = median_filter(S, size=(1, ancho))
    P = median_filter(S, size=(ancho, 1))
    mascara = P ** 2 / (H ** 2 + P ** 2 + 1e-12)
    E = S ** 2
    salida = []
    for lo, hi in C.BANDAS.values():
        sel = (f >= lo) & (f < hi)
        salida.append(float((mascara[sel] * E[sel]).sum() / (E[sel].sum() + 1e-12)))
    return salida


def fuerza_ataques(S):
    """Flujo espectral positivo medio dividido por el nivel medio (ambos en escala log).
    Alto con batería marcada (rock, electrónica); bajo con ataques suaves (balada)."""
    L = np.log1p(C.COMPRESION_LOG * S)
    flujo = np.maximum(np.diff(L, axis=1), 0).sum(axis=0)
    return float(np.mean(flujo) / (np.mean(L.sum(axis=0)) + 1e-12))


def rango_db(y, ventana_s=0.5):
    """Diferencia entre el nivel alto (percentil 90) y bajo (percentil 10) del RMS, en dB."""
    n = int(ventana_s * C.SR)
    m = (len(y) // n) * n
    if m == 0:
        return 0.0
    rms = nivel_db(y[:m].reshape(-1, n))
    return float(np.percentile(rms, 90) - np.percentile(rms, 10))


def caracteristicas(y, analisis=None):
    """Devuelve (vector de 57 valores, análisis rítmico completo)."""
    a = analisis or analizar_ritmo(y)
    envs, tempo, patron = a["envs"], a["tempo"], a["patron"]
    P, r = tempo["periodo"], tempo["r"]
    v = []
    v.append(np.log2(tempo["bpm"] / C.BPM_CENTRO) if np.isfinite(tempo["bpm"]) else 0.0)
    v.append(tempo["claridad"])
    v += [_interpolar(r, P * fr) if np.isfinite(P) else 0.0 for fr, _ in FRACCIONES]

    total_bandas = sum(envs[b].sum() for b in C.NOMBRES_BANDA) + 1e-12
    v += [envs[b].sum() / total_bandas for b in C.NOMBRES_BANDA]
    v += [densidad_ataques(envs[b]) for b in C.NOMBRES_BANDA]
    for b in C.NOMBRES_BANDA:
        rb = autocorrelacion(envs[b])
        v.append(_interpolar(rb, P) if np.isfinite(P) else 0.0)

    pasos = np.arange(C.PASOS_POR_COMPAS)
    en_pulso = pasos % 4 == 0             # pasos 0, 4, 8, 12
    en_contra = pasos % 4 == 2            # pasos 2, 6, 10, 14 (corcheas a contratiempo)
    en_semi = pasos % 2 == 1              # pasos impares (semicorcheas)
    for i in range(len(C.NOMBRES_BANDA)):
        p = patron[i]
        s = p.sum() + 1e-12
        v += [p[en_pulso].sum() / s, p[en_contra].sum() / s, p[en_semi].sum() / s]
    for i in range(len(C.NOMBRES_BANDA)):
        D = np.abs(np.fft.rfft(patron[i]))     # 9 valores: k = 0..8
        v += list(D[1:9] / (D[0] + 1e-12))
    v.append(dinamica_db(y))
    v += percusividad(a["S"], a["f"])
    v += [fuerza_ataques(a["S"]), rango_db(y)]
    return np.nan_to_num(np.array(v, dtype=np.float64)), a


def tempo_rapido(y):
    """Solo el tempo (para la prueba de ruido)."""
    a = analizar_ritmo(y)
    return a["tempo"]["bpm"], a["tempo"]["claridad"]
