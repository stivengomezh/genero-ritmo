"""
ritmo.py - Análisis rítmico de una señal de audio.

Cadena de procesamiento:

    x[n] (22 050 Hz)
      --> STFT |X(m, k)|                       espectrograma (tramas de 46 ms cada 11,6 ms)
      --> log(1 + γ|X|)                        compresión logarítmica (como el oído)
      --> flujo espectral por banda            "cuánta energía nueva aparece" en cada trama
      --> envolvente de ataques e_b[m]         una señal nueva, muestreada a 86,13 Hz
      --> autocorrelación R[ℓ]                 periodicidad -> tempo (pulsos por minuto)
      --> FFT de la envolvente                 espectro rítmico (frecuencias de 0,5 a 10 Hz)
      --> patrón de compás                     dónde caen los golpes dentro de un compás de 16 pasos

La idea central: el ritmo es la periodicidad de los ATAQUES (los golpes), no de la
forma de onda. Por eso se construye una señal que vale mucho cuando empieza un golpe
y casi cero en el resto, y se estudia la periodicidad de esa señal.
"""
import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, uniform_filter1d

import config as C


# ============================================================ 1. Espectrograma
def espectrograma(y, sr=C.SR):
    """STFT con ventana de Hann. Devuelve (|X| de forma (frecuencias, tramas), f en Hz, t en s)."""
    f, t, Z = signal.stft(y, fs=sr, window=C.VENTANA, nperseg=C.N_FFT, noverlap=C.N_FFT - C.HOP,
                          boundary=None, padded=False)
    return np.abs(Z), f, t


# ============================================================ 2. Envolventes de ataques
def envolventes(S, f):
    """Flujo espectral por banda: e_b[m] = Σ_{k en b} max(0, L[k, m] - L[k, m-1]),  L = log(1 + γ|X|).

    Solo se suman los aumentos de energía (rectificación de media onda): un golpe es un
    aumento brusco; la caída del sonido no interesa. Luego se resta la media móvil de
    0,5 s para quitar la tendencia lenta (crescendos, cambios de sección).

    La envolvente "total" es la suma de las tres bandas, cada una dividida por su desviación
    estándar: así las tres pesan lo mismo. Si se sumaran todas las frecuencias directamente,
    los agudos (90 % de los bins de la FFT) dominarían, y con ruido blanco, que tapa sobre
    todo los agudos, la envolvente se perdería; con el mismo peso, los graves (donde la
    música sigue por encima del ruido) mantienen el pulso.

    Devuelve un diccionario {banda: envolvente} con las bandas de C.BANDAS y "total".
    Las envolventes por banda no se normalizan, para poder comparar la energía entre bandas.
    """
    L = np.log1p(C.COMPRESION_LOG * S)
    flujo = np.maximum(0.0, np.diff(L, axis=1, prepend=L[:, :1]))
    salida = {}
    n_media = max(1, int(round(C.VENTANA_MEDIA_S * C.FS_ENV)))
    for nombre, (f_min, f_max) in C.BANDAS.items():
        mascara = (f >= f_min) & (f < f_max)
        e = flujo[mascara].sum(axis=0)
        e = np.maximum(0.0, e - uniform_filter1d(e, n_media, mode="nearest"))
        salida[nombre] = e
    salida["total"] = sum(salida[b] / (salida[b].std() + 1e-12) for b in C.BANDAS)
    return salida


def normalizada(e):
    m = float(np.max(e)) if len(e) else 0.0
    return e / m if m > 0 else e


# ============================================================ 3. Autocorrelación y tempo
def autocorrelacion(e, max_lag_s=4.0):
    """R[ℓ] = Σ_m ẽ[m]·ẽ[m+ℓ] / Σ_m ẽ[m]²,  con ẽ = e - media.

    Si los golpes se repiten cada P tramas, R tiene picos en ℓ = P, 2P, 3P...
    R[0] = 1 y |R[ℓ]| ≤ 1. Se calcula con la FFT (más rápido que la suma directa).
    """
    x = np.asarray(e, dtype=np.float64) - np.mean(e)
    n = len(x)
    max_lag = min(n - 1, int(max_lag_s * C.FS_ENV))
    if n < 2 or not np.any(x):
        return np.zeros(max_lag + 1)
    nfft = 1 << int(np.ceil(np.log2(2 * n)))
    X = np.fft.rfft(x, nfft)
    r = np.fft.irfft(np.abs(X) ** 2, nfft)[:max_lag + 1]
    # corrección por el número de términos que se suman en cada retardo (estimador insesgado)
    r = r / (n - np.arange(max_lag + 1))
    return r / r[0]


def _interpolar(r, lag):
    """Valor de R en un retardo no entero (interpolación lineal)."""
    if lag < 0 or lag > len(r) - 1:
        return 0.0
    i = int(np.floor(lag))
    a = lag - i
    return float(r[i] if i + 1 >= len(r) else (1 - a) * r[i] + a * r[i + 1])


def peso_perceptual(bpm):
    """Preferencia gaussiana en escala logarítmica alrededor de BPM_CENTRO.

    La autocorrelación tiene picos en el pulso, en el doble y en la mitad del periodo.
    Todos son "correctos" matemáticamente; se elige el que un oyente marcaría con el pie.
    """
    return np.exp(-0.5 * (np.log2(np.asarray(bpm) / C.BPM_CENTRO) / C.OCTAVAS_PREFERENCIA) ** 2)


def estimar_tempo(e, r=None):
    """Tempo a partir de la autocorrelación de la envolvente.

    Puntaje(ℓ) = peso(ℓ) · (R[ℓ] + ½ R[2ℓ] + ½ R[ℓ/2])   para ℓ entre BPM_MAX y BPM_MIN.
    Sumar R[2ℓ] favorece al periodo que se sigue repitiendo (un pulso de verdad, no un
    golpe aislado); sumar R[ℓ/2] favorece al periodo que además tiene subdivisiones
    (corcheas), que es lo que un oyente suele marcar como pulso.
    El máximo se refina con interpolación parabólica para no quedar limitado a la
    resolución de una trama (11,6 ms).

    Devuelve un diccionario: bpm, periodo (en tramas, no entero), claridad (= R en el periodo),
    r (la autocorrelación) y puntaje.
    """
    if r is None:
        r = autocorrelacion(e)
    lag_min = int(np.floor(60 * C.FS_ENV / C.BPM_MAX))
    lag_max = min(len(r) // 2 - 1, int(np.ceil(60 * C.FS_ENV / C.BPM_MIN)))
    if lag_max <= lag_min + 2:
        return {"bpm": float("nan"), "periodo": float("nan"), "claridad": 0.0, "r": r, "puntaje": None}
    lags = np.arange(lag_min, lag_max + 1)
    bpm = 60 * C.FS_ENV / lags
    rp = np.maximum(r, 0)
    mitad = np.interp(lags / 2, np.arange(len(r)), rp)
    puntaje = peso_perceptual(bpm) * (rp[lags] + 0.5 * rp[2 * lags] + 0.5 * mitad)
    k = int(np.argmax(puntaje))
    lag = float(lags[k])
    if 0 < k < len(lags) - 1:  # interpolación parabólica del máximo
        a, b, c = puntaje[k - 1], puntaje[k], puntaje[k + 1]
        den = a - 2 * b + c
        if den < 0:
            lag += 0.5 * (a - c) / den
    return {"bpm": 60 * C.FS_ENV / lag, "periodo": lag, "claridad": _interpolar(r, lag), "r": r,
            "puntaje": (lags, puntaje)}


# ============================================================ 4. Espectro rítmico
def espectro_ritmico(e, f_max=10.0):
    """FFT de la envolvente de ataques: E[k] = Σ_m (e[m] - ē)·w[m]·e^(−j2πkm/M).

    El eje de frecuencia va en Hz (ciclos de golpes por segundo) y se puede leer en
    BPM multiplicando por 60. Como la envolvente está muestreada a 86,13 Hz, su
    Nyquist es 43 Hz: de sobra para ritmos (10 Hz = 600 golpes por minuto).
    """
    x = (np.asarray(e) - np.mean(e)) * np.hanning(len(e))
    nfft = max(len(x), 1 << 14)                 # relleno con ceros: curva más suave para graficar
    E = np.abs(np.fft.rfft(x, nfft))
    f = np.fft.rfftfreq(nfft, 1 / C.FS_ENV)
    sel = f <= f_max
    return f[sel], E[sel] / (E[sel].max() + 1e-12)


# ============================================================ 5. Patrón de compás
def fase_pulso(e, periodo):
    """Instante (en tramas) del primer pulso: la fase φ que hace que e[φ + k·P] sea máxima en promedio."""
    if not np.isfinite(periodo) or periodo <= 1:
        return 0.0
    m = np.arange(len(e))
    mejor, mejor_valor = 0.0, -1.0
    for fase in np.arange(0, periodo, 0.5):
        puntos = np.arange(fase, len(e) - 1, periodo)
        valor = float(np.interp(puntos, m, e).mean())
        if valor > mejor_valor:
            mejor, mejor_valor = fase, valor
    return mejor


def patron_compas(envs, periodo, fase=None, pasos=C.PASOS_POR_COMPAS):
    """Promedia, compás por compás, la envolvente de cada banda en 16 posiciones (semicorcheas).

    Un compás = 4 pulsos = 4·P tramas; cada paso dura P/4 tramas. Para cada paso del compás
    se toma el máximo de la envolvente en ±½ paso (tolera pequeñas imprecisiones del músico
    y del tempo estimado) y se promedia sobre todos los compases.

    El resultado es una matriz (bandas x 16) normalizada por banda entre 0 (la posición más
    débil) y 1 (la más fuerte): el "dibujo" del ritmo. Se rota de a un pulso (4 pasos) para que el paso 0 sea el pulso con más bombo.

    Devuelve (patron, fase, n_compases).
    """
    bandas = C.NOMBRES_BANDA
    n_tramas = len(envs["total"])
    if not np.isfinite(periodo) or periodo <= 1:
        return np.zeros((len(bandas), pasos)), 0.0, 0
    if fase is None:
        fase = fase_pulso(normalizada(envs["total"]) + normalizada(envs["graves"]), periodo)
    paso = 4 * periodo / pasos
    n_compases = int((n_tramas - 1 - fase) // (4 * periodo))
    if n_compases < 1:
        return np.zeros((len(bandas), pasos)), fase, 0
    ancho = max(1, int(round(paso)))
    m = np.arange(n_tramas)
    posiciones = fase + paso * np.arange(n_compases * pasos)
    patron = np.zeros((len(bandas), pasos))
    for i, b in enumerate(bandas):
        e_max = maximum_filter1d(envs[b], size=ancho, mode="nearest")
        valores = np.interp(posiciones, m, e_max).reshape(n_compases, pasos)
        p = valores.mean(axis=0)
        rango = p.max() - p.min()
        patron[i] = (p - p.min()) / rango if rango > 0 else 0.0   # 0 = posición más débil, 1 = más fuerte
    # rotación de a un pulso: el paso 0 es el pulso con más energía en graves
    rot = int(np.argmax([patron[0, 4 * j] + 0.5 * patron[1, 4 * j] for j in range(4)]))
    return np.roll(patron, -4 * rot, axis=1), fase + rot * periodo, n_compases


def pulsos(fase, periodo, n_tramas):
    """Tramas donde cae cada pulso (para graficar sobre la señal)."""
    if not np.isfinite(periodo) or periodo <= 1:
        return np.empty(0)
    return np.arange(fase, n_tramas, periodo)


def tramas_a_segundos(m):
    """Instante de cada trama de la STFT (centro de la ventana), en segundos."""
    return (np.asarray(m) * C.HOP + C.N_FFT / 2) / C.SR


# ============================================================ Todo junto
def analizar_ritmo(y, sr=C.SR):
    """Ejecuta toda la cadena y devuelve un diccionario con los pasos intermedios (para graficar)."""
    if len(y) < 4 * C.N_FFT:
        raise ValueError(f"El audio es demasiado corto ({len(y) / sr:.2f} s).")
    S, f, t = espectrograma(y, sr)
    envs = envolventes(S, f)
    tempo = estimar_tempo(envs["total"])
    patron, fase, n_compases = patron_compas(envs, tempo["periodo"])
    return {"S": S, "f": f, "t": t, "envs": envs, "tempo": tempo, "patron": patron, "fase": fase,
            "n_compases": n_compases}
