"""
config.py - Parámetros del sistema de reconocimiento de género musical por ritmo.

Todos los módulos leen sus valores de aquí, para que cada número del informe
tenga un solo lugar donde se define y se justifica.
"""
from pathlib import Path

# ---------------------------------------------------------------- Carpetas
CARPETA_PROYECTO = Path(__file__).resolve().parent.parent      # raíz del repositorio (este archivo está en src/)
CARPETA_DATOS = CARPETA_PROYECTO / "data"
CARPETA_CANCIONES = CARPETA_DATOS / "canciones"                # canciones reales (no se suben a GitHub)
CARPETA_SINTETICOS = CARPETA_DATOS / "sinteticos"              # ritmos generados por código (demostración)
CARPETA_GRABACIONES = CARPETA_DATOS / "grabaciones"
CARPETA_RESULTADOS = CARPETA_PROYECTO / "results"

EXTENSIONES_AUDIO = (".wav", ".mp3", ".flac", ".ogg", ".m4a")

# ---------------------------------------------------------------- Géneros
# El género de cada archivo se toma del inicio de su nombre: salsa_01.mp3 -> "salsa".
GENEROS = ["salsa", "reggaeton", "bachata", "vallenato", "cumbia", "rock", "electronica", "balada"]
NOMBRES_GENERO = {"salsa": "Salsa", "reggaeton": "Reggaetón", "bachata": "Bachata", "vallenato": "Vallenato",
                  "cumbia": "Cumbia", "rock": "Rock", "electronica": "Electrónica", "balada": "Balada"}

# ---------------------------------------------------------------- Muestreo
# 22 050 Hz: Nyquist = 11 025 Hz. Conserva los platillos, hi-hats, güira y guacharaca
# (energía entre 3 y 10 kHz), que marcan las subdivisiones del ritmo. Con 11 025 Hz
# (Nyquist 5,5 kHz) se perdería buena parte de esa banda.
SR = 22050

# ---------------------------------------------------------------- STFT
N_FFT = 1024        # 46,4 ms por trama -> Δf = SR/N_FFT = 21,5 Hz
HOP = 256           # 11,6 ms entre tramas (75 % de solapamiento)
VENTANA = "hann"
FS_ENV = SR / HOP   # 86,13 Hz: frecuencia de muestreo de la envolvente de ataques

# ---------------------------------------------------------------- Bandas de frecuencia
# Cada banda separa un grupo de instrumentos de percusión:
BANDAS = {
    "graves": (30, 200),       # bombo, bajo, tumbadora grave
    "medios": (200, 2000),     # caja, congas, bongó, campana, guitarra rítmica
    "agudos": (2000, 10000),   # hi-hat, platillos, güira, guacharaca, maracas
}
NOMBRES_BANDA = list(BANDAS)

# ---------------------------------------------------------------- Envolvente de ataques
COMPRESION_LOG = 100.0      # log(1 + γ|X|): el oído percibe la intensidad en escala logarítmica
VENTANA_MEDIA_S = 0.5       # se resta la media móvil de 0,5 s (quita la tendencia lenta)

# ---------------------------------------------------------------- Tempo
BPM_MIN, BPM_MAX = 50, 220  # rango de búsqueda del pulso
BPM_CENTRO = 110            # preferencia perceptual: tempos cercanos a ~110 BPM pesan más
OCTAVAS_PREFERENCIA = 0.7   # ancho (en octavas) de esa preferencia (desviación de la gaussiana en log2)

# ---------------------------------------------------------------- Segmentación
SEGMENTO_S = 10.0           # cada canción se divide en fragmentos de 10 s ...
SOLAPE = 0.5                # ... que se solapan el 50 % (avanzan 5 s)
PASOS_POR_COMPAS = 16       # un compás de 4 tiempos dividido en semicorcheas
# Para el clasificador, cada canción aporta como máximo MAX_FRAGMENTOS fragmentos repartidos a lo
# largo de la canción, sin los primeros y últimos RECORTE_S segundos (introducción y final, que
# suelen no tener la percusión completa). Así una canción de 7 minutos no pesa el triple que una de 2.
MAX_FRAGMENTOS = 24
RECORTE_S = 15.0

# ---------------------------------------------------------------- Clasificador
K_VECINOS = 5               # k-NN: votan los k fragmentos más parecidos

# ---------------------------------------------------------------- Grabación
SEGUNDOS_GRABACION = 10
