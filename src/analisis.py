"""
analisis.py - Análisis de las señales para la Entrega 2 de Teoría de Señales.

    1. Adquisición / carga     formato, fs, Ts, canales, número de muestras
    2. Representación temporal x(t) de una canción por género y ventanas ampliadas
    3. Caracterización         mín, máx, media, RMS, factor de cresta, energía por banda, tempo...
    4. Análisis frecuencial    espectro |X(f)| con la FFT; espectro de la envolvente rítmica
    5. Muestreo                justificación de fs = 22 050 Hz y efecto del aliasing
    6. Ruido                   señal original vs. con ruido: forma de onda, envolvente, autocorrelación, tempo
    7. Segmentación            fragmentos de 10 s, tramas de la STFT y compases de 16 pasos

Uso:  python main.py analizar                    (carpeta por defecto: canciones reales o sintéticas)
      python main.py analizar --cancion salsa_01
"""
import csv
from pathlib import Path

import numpy as np
from scipy import signal

import config as C
from carga import cargar_original, remuestrear, normalizar, fragmentar, listar_canciones, carpeta_por_defecto
from ritmo import analizar_ritmo, espectrograma, envolventes, autocorrelacion, estimar_tempo, tramas_a_segundos, pulsos
from ruido import agregar_ruido
import graficas as G
from graficas import plt, AZUL, NARANJA, AGUA, GRIS, SUPERFICIE, TEXTO, TEXTO_2, TENUE, REJILLA, COLOR_BANDA


# ============================================================ Espectro con la FFT
def espectro(y, fs):
    """X[k] = FFT{ y[n]·w[n] } con ventana de Hann. Devuelve (f, |X|²) con N/2+1 frecuencias de 0 a fs/2,
    separadas Δf = fs/N."""
    N = len(y)
    X = np.fft.rfft(y * np.hanning(N))
    return np.fft.rfftfreq(N, 1 / fs), np.abs(X) ** 2


def espectro_tercios(f, P, f_min=20.0, f_max=None):
    """Promedia la potencia en bandas de 1/6 de octava (escala logarítmica, como el oído).
    Devuelve (centros_Hz, nivel_dB respecto a la banda más fuerte)."""
    f_max = f_max or f[-1]
    centros = f_min * 2 ** (np.arange(0, np.log2(f_max / f_min) * 6) / 6)
    lo = np.searchsorted(f, centros * 2 ** (-1 / 12))
    hi = np.searchsorted(f, centros * 2 ** (1 / 12))
    acum = np.concatenate(([0.0], np.cumsum(P)))
    dens = (acum[hi] - acum[lo]) / np.maximum(hi - lo, 1)
    return centros, 10 * np.log10(dens / dens.max() + 1e-30)


# ============================================================ 3. Caracterización
def caracterizar(ruta, genero):
    x, fs = cargar_original(ruta)
    canales, N = x.shape
    ym = x.mean(axis=0)
    pico = float(np.max(np.abs(ym)))
    rms = float(np.sqrt(np.mean(ym ** 2)))
    f, P = espectro(ym, fs)
    Pt = P.sum()
    y = normalizar(remuestrear(ym, fs, C.SR))
    analisis = [analizar_ritmo(fr) for _, fr in fragmentar(y)]
    tempos = np.array([a["tempo"]["bpm"] for a in analisis])
    d = {
        "cancion": Path(ruta).stem, "genero": genero, "formato": Path(ruta).suffix.lstrip(".").upper(),
        "fs_Hz": fs, "Ts_us": 1e6 / fs, "canales": canales, "muestras": N, "duracion_s": N / fs,
        "muestras_22050": len(y), "minimo": float(ym.min()), "maximo": float(ym.max()), "media": float(ym.mean()),
        "rms_dBFS": 20 * np.log10(rms + 1e-12), "cresta_dB": 20 * np.log10(pico / (rms + 1e-12)),
        "saturadas_pct": 100 * float(np.mean(np.abs(x) >= 0.999)),
        "correlacion_LR": float(np.corrcoef(x[0], x[1])[0, 1]) if canales == 2 else float("nan"),
        "energia_bajo_11025Hz_pct": 100 * float(P[f < C.SR / 2].sum() / Pt),
        "energia_graves_pct": 100 * float(P[(f >= 30) & (f < 200)].sum() / Pt),
        "energia_medios_pct": 100 * float(P[(f >= 200) & (f < 2000)].sum() / Pt),
        "energia_agudos_pct": 100 * float(P[(f >= 2000) & (f < 10000)].sum() / Pt),
        "centroide_Hz": float(np.sum(f * P) / Pt),
        "tempo_BPM": float(np.median(tempos)),
        "tempo_desv_BPM": float(np.std(tempos)),
        "claridad_pulso": float(np.median([a["tempo"]["claridad"] for a in analisis])),
        "fragmentos": len(analisis),
    }
    return d, {"x": x, "fs": fs, "y": y, "f": f, "P": P, "analisis": analisis}


COLUMNAS_TABLA = [
    ("cancion", "Canción", "{}"), ("duracion_s", "Duración (s)", "{:.1f}"), ("fs_Hz", "fs (Hz)", "{}"),
    ("canales", "Canales", "{}"), ("muestras", "N original", "{:,}"), ("muestras_22050", "N (22 050 Hz)", "{:,}"),
    ("minimo", "Mín", "{:.3f}"), ("maximo", "Máx", "{:.3f}"), ("media", "Media", "{:+.5f}"),
    ("rms_dBFS", "RMS (dBFS)", "{:.1f}"), ("cresta_dB", "Cresta (dB)", "{:.1f}"),
    ("energia_bajo_11025Hz_pct", "Energía < 11 kHz (%)", "{:.2f}"), ("energia_graves_pct", "Graves (%)", "{:.0f}"),
    ("energia_medios_pct", "Medios (%)", "{:.0f}"), ("energia_agudos_pct", "Agudos (%)", "{:.1f}"),
    ("tempo_BPM", "Tempo (BPM)", "{:.0f}"), ("claridad_pulso", "Claridad R[P]", "{:.2f}"),
]


def guardar_tabla(filas):
    C.CARPETA_RESULTADOS.mkdir(exist_ok=True)
    with open(C.CARPETA_RESULTADOS / "caracterizacion.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    with open(C.CARPETA_RESULTADOS / "caracterizacion.md", "w", encoding="utf-8") as fh:
        fh.write("| " + " | ".join(t for _, t, _ in COLUMNAS_TABLA) + " |\n")
        fh.write("|" + "---|" * len(COLUMNAS_TABLA) + "\n")
        for d in filas:
            fh.write("| " + " | ".join(fmt.format(d[c]).replace(",", " ") if "{:," in fmt else fmt.format(d[c])
                                       for c, _, fmt in COLUMNAS_TABLA) + " |\n")
    print(f"  Tabla guardada: {C.CARPETA_RESULTADOS / 'caracterizacion.csv'} y caracterizacion.md")


def resumen_por_genero(filas):
    """Promedio de algunas medidas por género (para el README)."""
    salida = []
    for g in C.GENEROS:
        sel = [d for d in filas if d["genero"] == g]
        if not sel:
            continue
        salida.append({"genero": g, "canciones": len(sel),
                       "tempo_min": min(d["tempo_BPM"] for d in sel), "tempo_max": max(d["tempo_BPM"] for d in sel),
                       **{k: float(np.mean([d[k] for d in sel])) for k in
                          ("rms_dBFS", "cresta_dB", "energia_graves_pct", "energia_agudos_pct", "claridad_pulso",
                           "centroide_Hz")}})
    with open(C.CARPETA_RESULTADOS / "resumen_generos.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(salida[0].keys()))
        w.writeheader()
        w.writerows(salida)
    return salida


# ============================================================ Utilidades de dibujo
def _envolvente_minmax(y, n_bloques=2500):
    b = max(1, len(y) // n_bloques)
    m = (len(y) // b) * b
    r = y[:m].reshape(-1, b)
    return r.min(axis=1), r.max(axis=1), (np.arange(r.shape[0]) * b + b / 2)


def _rms_corto(y, fs, ventana_s=0.1):
    n = max(1, int(ventana_s * fs))
    m = (len(y) // n) * n
    rms = np.sqrt(np.mean(y[:m].reshape(-1, n) ** 2, axis=1))
    return rms, (np.arange(len(rms)) + 0.5) * ventana_s


# ============================================================ 2. Representación temporal
def figura_formas_de_onda(ejemplos, nombre_archivo="formas_de_onda.png", mostrar=False):
    """x(t) completa de una canción por género (mezcla mono a la fs original) con su RMS de 100 ms."""
    n = len(ejemplos)
    fig, ejes = plt.subplots(n, 1, figsize=(12, 1.55 * n + 1), constrained_layout=True)
    ejes = np.atleast_1d(ejes)
    for ax, (d, extra) in zip(ejes, ejemplos):
        ym, fs = extra["x"].mean(axis=0), extra["fs"]
        mn, mx, idx = _envolvente_minmax(ym)
        ax.fill_between(idx / fs, mn, mx, color=G.COLOR_GENERO[d["genero"]], alpha=0.55, linewidth=0)
        rms, tr = _rms_corto(ym, fs)
        ax.plot(tr, rms, color=TEXTO_2, linewidth=0.9)
        ax.set_xlim(0, len(ym) / fs)
        ax.set_ylim(-1.1, 1.1)
        ax.set_yticks([-1, 0, 1])
        ax.set_ylabel("x(t)")
        ax.set_title(f"{G.nombre_genero(d['genero'])} ({d['cancion']})  ·  {d['duracion_s']:.1f} s  ·  "
                     f"RMS {d['rms_dBFS']:.1f} dBFS  ·  ~{d['tempo_BPM']:.0f} BPM", fontsize=10)
    ejes[-1].set_xlabel("Tiempo (s)")
    G.titulo_figura(fig, "Forma de onda x(t) de una canción por género (mezcla mono; ±1 = escala completa; "
                         "línea gris = RMS en ventanas de 100 ms)")
    return G.terminar(fig, nombre_archivo, mostrar)


def figura_ventanas(d, extra, nombre_archivo="ventana_temporal.png", mostrar=False):
    """(a) 4 s de señal con los ataques detectados y los pulsos; (b) 30 ms con las muestras a 44,1 y 22,05 kHz."""
    y, fs_o = extra["y"], extra["fs"]
    a = extra["analisis"][len(extra["analisis"]) // 2]       # un fragmento del centro de la canción
    frags = fragmentar(y)
    inicio_frag, frag = frags[len(frags) // 2]
    env = a["envs"]["total"]
    t_env = tramas_a_segundos(np.arange(len(env)))
    beats = tramas_a_segundos(pulsos(a["fase"], a["tempo"]["periodo"], len(env)))
    from scipy.signal import find_peaks
    picos, _ = find_peaks(env / env.max(), height=0.3, distance=int(0.07 * C.FS_ENV))
    t0 = 2.0
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(12, 9.5), constrained_layout=True,
                                     gridspec_kw={"height_ratios": [1.2, 0.8, 1]})
    i0, i1 = int(t0 * C.SR), int((t0 + 4) * C.SR)
    t = np.arange(i0, i1) / C.SR
    a1.plot(t, frag[i0:i1], color=G.COLOR_GENERO[d["genero"]], linewidth=0.4)
    for x in beats[(beats >= t0) & (beats <= t0 + 4)]:
        a1.axvline(x, color=TEXTO_2, linewidth=1, linestyle="--")
    tp = t_env[picos]
    sel = (tp >= t0) & (tp <= t0 + 4)
    a1.scatter(tp[sel], np.full(sel.sum(), 1.05), marker="v", s=36, color=NARANJA, zorder=3, label="ataque detectado")
    a1.plot([], [], color=TEXTO_2, linestyle="--", label=f"pulso ({a['tempo']['bpm']:.0f} BPM)")
    a1.set_xlim(t0, t0 + 4)
    a1.set_ylim(-1.1, 1.2)
    a1.set_ylabel("Amplitud")
    a1.legend(loc="lower right", ncol=2, fontsize=9)
    a1.set_title(f"(a) 4 s de {d['cancion']} (desde t = {inicio_frag + t0:.0f} s): los golpes son ráfagas "
                 "de amplitud que se repiten con el pulso")

    a2.plot(t_env, env / env.max(), color=AZUL, linewidth=1.2)
    a2.scatter(t_env[picos], env[picos] / env.max(), s=18, color=NARANJA, zorder=3)
    for x in beats[(beats >= t0) & (beats <= t0 + 4)]:
        a2.axvline(x, color=TEXTO_2, linewidth=1, linestyle="--")
    a2.set_xlim(t0, t0 + 4)
    a2.set_ylabel("e[m] (norm.)")
    a2.set_xlabel("Tiempo (s)")
    a2.set_title(f"(b) Envolvente de ataques de la misma ventana (muestreada a {C.FS_ENV:.2f} Hz = 22 050 / 256)")

    # (c) muestras: señal original a fs_o y remuestreada a 22 050 Hz
    ym = extra["x"].mean(axis=0)
    c = int((inicio_frag + t0 + 1.0) * fs_o)
    n = int(0.003 * fs_o)
    tk = np.arange(n) / fs_o * 1000
    a3.plot(tk, ym[c:c + n], color=GRIS, linewidth=1, zorder=1)
    a3.scatter(tk, ym[c:c + n], s=16, color=AZUL, zorder=3, label=f"{fs_o} Hz  (Ts = {1e6 / fs_o:.1f} µs)")
    y22 = remuestrear(ym, fs_o, C.SR)
    m0 = int(np.ceil(c * C.SR / fs_o))
    m1 = int(np.floor((c + n - 1) * C.SR / fs_o))
    tm = (np.arange(m0, m1 + 1) / C.SR - c / fs_o) * 1000
    a3.vlines(tm, 0, y22[m0:m1 + 1], color=NARANJA, linewidth=2, zorder=2)
    a3.scatter(tm, y22[m0:m1 + 1], s=46, color=NARANJA, edgecolors=SUPERFICIE, linewidths=1.2, zorder=4,
               label=f"{C.SR} Hz  (Ts = {1e6 / C.SR:.1f} µs)")
    a3.axhline(0, color=TENUE, linewidth=0.8)
    a3.set_xlabel("Tiempo (ms)")
    a3.set_ylabel("Amplitud")
    a3.legend(loc="upper right", fontsize=9)
    a3.set_title("(c) Detalle de 3 ms: cada punto es una muestra x[n] = x(n·Ts)")
    G.titulo_figura(fig, f"Representación temporal de {G.nombre_genero(d['genero'])} ({d['cancion']}) a distintas escalas")
    return G.terminar(fig, nombre_archivo, mostrar)


# ============================================================ 4. Análisis frecuencial
def figura_espectros(ejemplos, nombre_archivo="espectros_fft.png", mostrar=False):
    n = len(ejemplos)
    columnas = 2
    filas = int(np.ceil(n / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(13, 2.3 * filas + 1.2), sharex=True, sharey=True,
                             constrained_layout=True)
    ejes = np.atleast_1d(ejes).ravel()
    for ax, (d, extra) in zip(ejes, ejemplos):
        fc, db = espectro_tercios(extra["f"], extra["P"], 20, extra["fs"] / 2)
        for b, (f1, f2) in C.BANDAS.items():
            ax.axvspan(f1, f2, color=COLOR_BANDA[b], alpha=0.07, linewidth=0)
        ax.axvspan(C.SR / 2, extra["fs"] / 2, color=GRIS, alpha=0.25, linewidth=0)
        ax.axvline(C.SR / 2, color=TEXTO_2, linestyle="--", linewidth=1)
        ax.plot(fc, db, color=G.COLOR_GENERO[d["genero"]], linewidth=1.6)
        ax.set_xscale("log")
        ax.set_xlim(20, extra["fs"] / 2)
        ax.set_ylim(-80, 5)
        ax.set_xticks([31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000])
        ax.set_xticklabels(["31", "63", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"])
        ax.minorticks_off()
        ax.text(0.86, 0.95, f"graves {d['energia_graves_pct']:.0f} % · medios {d['energia_medios_pct']:.0f} % · "
                f"agudos {d['energia_agudos_pct']:.1f} %\n{d['energia_bajo_11025Hz_pct']:.2f} % por debajo de 11 025 Hz",
                transform=ax.transAxes, ha="right", va="top", fontsize=8.3, color=TEXTO_2,
                bbox=dict(boxstyle="round,pad=0.2", facecolor=SUPERFICIE, edgecolor="none", alpha=0.85))
        ax.set_title(f"{G.nombre_genero(d['genero'])} ({d['cancion']})", fontsize=10.5)
    for ax in ejes[n:]:
        ax.set_visible(False)
    for ax in ejes[::columnas]:
        ax.set_ylabel("|X(f)| (dB)")
    for ax in ejes[max(0, n - columnas):n]:
        ax.set_xlabel("Frecuencia (Hz, escala logarítmica)")
    G.titulo_figura(fig, "Espectro de magnitud |X(f)| de cada canción completa (FFT con ventana de Hann; "
                         "0 dB = banda más fuerte; promediado en 1/6 de octava)")
    fig.text(0.01, -0.015, "Franjas de color: bandas de análisis (graves 30–200 Hz, medios 200–2 000 Hz, agudos "
             "2–10 kHz). Zona gris: lo que se elimina al bajar a fs = 22 050 Hz (por encima de Nyquist = 11 025 Hz).",
             fontsize=9, color=TEXTO_2)
    return G.terminar(fig, nombre_archivo, mostrar)


# ============================================================ 5. Muestreo y aliasing
def figura_aliasing(d, extra, nombre_archivo="muestreo_aliasing.png", mostrar=False):
    """Bajar de fs original a 22 050 Hz bien (con filtro) y mal (tomando 1 de cada M muestras)."""
    ym, fs = extra["x"].mean(axis=0), extra["fs"]
    M = fs // C.SR
    if M < 2 or fs % C.SR:
        print(f"  (se omite la figura de aliasing: fs = {fs} Hz no es múltiplo entero de {C.SR} Hz)")
        return None, None
    c = len(ym) // 2
    seg = ym[max(0, c - 5 * fs): c + 5 * fs]
    bien = remuestrear(seg, fs, C.SR)
    mal = seg[::M].astype(np.float32)
    n = min(len(bien), len(mal))
    bien, mal = bien[:n], mal[:n]
    f, Pb = espectro(bien, C.SR)
    _, Pm = espectro(mal, C.SR)
    fc, db_b = espectro_tercios(f, Pb, 20, C.SR / 2)
    _, db_m = espectro_tercios(f, Pm, 20, C.SR / 2)
    ref = 10 * np.log10(max(Pb.max(), Pm.max()))
    db_b += 10 * np.log10(Pb.max()) - ref
    db_m += 10 * np.log10(Pm.max()) - ref
    banda = (f >= 8000) & (f < C.SR / 2)
    exceso = 10 * np.log10(Pm[banda].sum() / Pb[banda].sum())
    fig, ax = plt.subplots(figsize=(12, 4.6), constrained_layout=True)
    ax.plot(fc, db_m, color=NARANJA, linewidth=1.4, label=f"Sin filtro: x[{M}n] (hay aliasing)")
    ax.plot(fc, db_b, color=AZUL, linewidth=1.6, label="Con filtro antialiasing (el que usa el sistema)")
    ax.axvspan(8000, C.SR / 2, color=GRIS, alpha=0.18, linewidth=0)
    ax.text(9400, -6, f"8–11 kHz:\n+{exceso:.1f} dB de\nenergía falsa", ha="center", va="top", fontsize=9, color=TEXTO)
    ax.set_xscale("log")
    ax.set_xlim(20, C.SR / 2)
    ax.set_xticks([31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000])
    ax.set_xticklabels(["31", "63", "125", "250", "500", "1k", "2k", "4k", "8k"])
    ax.minorticks_off()
    ax.set_ylim(-80, 5)
    ax.set_xlabel(f"Frecuencia (Hz)  ·  0 a {C.SR / 2:,.0f} Hz (Nyquist con fs = {C.SR:,} Hz)".replace(",", " "))
    ax.set_ylabel("|X(f)| (dB)")
    ax.legend(loc="lower left", fontsize=9)
    ax.set_title(f"Submuestreo de {d['cancion']} de {fs} a {C.SR} Hz (10 s centrales)")
    ruta = G.terminar(fig, nombre_archivo, mostrar)
    return ruta, {"exceso_8k_11k_dB": exceso}


# ============================================================ 6. Ruido
def figura_ruido(d, extra, snr_db=0.0, semilla=0, nombre_archivo="ruido_comparacion.png", mostrar=False):
    y = extra["y"]
    frags = fragmentar(y)
    inicio, q = frags[len(frags) // 2]
    rng = np.random.default_rng(semilla)
    r = agregar_ruido(q, snr_db, rng, "blanco")
    a_q, a_r = analizar_ritmo(q), analizar_ritmo(r)
    fig = plt.figure(figsize=(13, 9), constrained_layout=True)
    gs = fig.add_gridspec(3, 2)
    ax_t = fig.add_subplot(gs[0, :])
    ax_e = fig.add_subplot(gs[1, :])
    ax_r = fig.add_subplot(gs[2, 0])
    ax_f = fig.add_subplot(gs[2, 1])

    t0, t1 = 2.0, 5.0
    i0, i1 = int(t0 * C.SR), int(t1 * C.SR)
    t = np.arange(i0, i1) / C.SR
    ax_t.plot(t, r[i0:i1], color=GRIS, linewidth=0.4, label=f"Con ruido blanco (SNR {snr_db:g} dB)")
    ax_t.plot(t, q[i0:i1], color=AZUL, linewidth=0.4, label="Original")
    ax_t.set_xlim(t0, t1)
    ax_t.set_ylabel("Amplitud")
    ax_t.legend(loc="upper right", fontsize=9, ncol=2)
    ax_t.set_title("(a) Dominio del tiempo: con igual potencia de ruido que de música, los golpes casi no se ven")

    te = tramas_a_segundos(np.arange(len(a_q["envs"]["total"])))
    for a, color, etiqueta in ((a_r, GRIS, "con ruido"), (a_q, AZUL, "original")):
        e = a["envs"]["total"]
        ax_e.plot(te, e / e.max(), color=color, linewidth=1.2, label=etiqueta)
    ax_e.set_xlim(t0, t1)
    ax_e.set_ylabel("e[m] (norm.)")
    ax_e.set_xlabel("Tiempo (s)")
    ax_e.legend(loc="upper right", fontsize=9, ncol=2)
    ax_e.set_title("(b) Envolvente de ataques: el ruido agrega picos pequeños en todas partes; los golpes "
                   "fuertes deben seguir sobresaliendo")

    for a, color, etiqueta in ((a_r, GRIS, "con ruido"), (a_q, AZUL, "original")):
        rr = a["tempo"]["r"]
        ax_r.plot(np.arange(len(rr)) / C.FS_ENV, rr, color=color, linewidth=1.3,
                  label=f"{etiqueta}: {a['tempo']['bpm']:.1f} BPM, R[P] = {a['tempo']['claridad']:.2f}")
    ax_r.axhline(0, color=TENUE, linewidth=0.8)
    ax_r.set_xlim(0, 3)
    ax_r.set_xlabel("Retardo ℓ (s)")
    ax_r.set_ylabel("R[ℓ]")
    ax_r.legend(fontsize=8.5, loc="upper right")
    ax_r.set_title(f"(c) Autocorrelación: R[P] pasa de {a_q['tempo']['claridad']:.2f} a {a_r['tempo']['claridad']:.2f}")

    tabla = prueba_ruido_tempo(extra.get("todas", [(d["cancion"], y)]), semilla=semilla)
    for tipo, color in (("blanco", AZUL), ("rosa", NARANJA)):
        snrs = sorted({s for (tt, s) in tabla if tt == tipo}, reverse=True)
        ax_f.plot(snrs, [100 * tabla[(tipo, s)] for s in snrs], color=color, marker="o", linewidth=2,
                  markeredgecolor=SUPERFICIE, label=f"ruido {tipo}")
    ax_f.set_xlim(max(snrs) + 1, min(snrs) - 1)
    ax_f.set_ylim(0, 105)
    ax_f.set_xticks(snrs)
    ax_f.set_xlabel("SNR (dB)  ← menos ruido · más ruido →")
    ax_f.set_ylabel("Tempo igual al original (%)")
    ax_f.legend(fontsize=9, loc="lower left")
    ax_f.set_title(f"(d) Fragmentos cuyo tempo no cambia (±4 %), todas las canciones")
    G.titulo_figura(fig, f"Efecto del ruido: {d['cancion']}, fragmento de {C.SEGMENTO_S:g} s desde t = {inicio:.0f} s")
    ruta = G.terminar(fig, nombre_archivo, mostrar)
    return ruta, {"tabla": tabla, "bpm_original": a_q["tempo"]["bpm"], "bpm_ruido": a_r["tempo"]["bpm"],
                  "claridad_original": a_q["tempo"]["claridad"], "claridad_ruido": a_r["tempo"]["claridad"]}


def prueba_ruido_tempo(canciones, snrs=(20, 10, 5, 0, -5), por_cancion=3, semilla=0):
    """Fracción de fragmentos cuyo tempo con ruido coincide (±4 %) con el tempo sin ruido."""
    rng = np.random.default_rng(semilla)
    conteo = {}
    for _, y in canciones:
        frags = fragmentar(y)
        elegidos = [frags[i] for i in np.linspace(0, len(frags) - 1, min(por_cancion, len(frags))).astype(int)]
        for _, q in elegidos:
            bpm0 = analizar_ritmo(q)["tempo"]["bpm"]
            for tipo in ("blanco", "rosa"):
                for s in snrs:
                    bpm = analizar_ritmo(agregar_ruido(q, s, rng, tipo))["tempo"]["bpm"]
                    ok, tot = conteo.get((tipo, s), (0, 0))
                    conteo[(tipo, s)] = (ok + (abs(bpm / bpm0 - 1) < 0.04), tot + 1)
    tabla = {k: ok / tot for k, (ok, tot) in conteo.items()}
    with open(C.CARPETA_RESULTADOS / "ruido_tempo.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ruido", "snr_dB", "fragmentos_tempo_igual_pct"])
        for (tipo, s), v in sorted(tabla.items(), key=lambda x: (x[0][0], -x[0][1])):
            w.writerow([tipo, s, f"{100 * v:.1f}"])
    return tabla


# ============================================================ 7. Segmentación
def figura_segmentacion(d, extra, nombre_archivo="segmentacion.png", mostrar=False):
    y = extra["y"]
    dur = len(y) / C.SR
    a = extra["analisis"][len(extra["analisis"]) // 2]
    frags = fragmentar(y)
    inicio_frag = frags[len(frags) // 2][0]
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True,
                                     gridspec_kw={"height_ratios": [1, 1, 1.1]})
    mn, mx, idx = _envolvente_minmax(y)
    a1.fill_between(idx / C.SR, mn, mx, color=GRIS, linewidth=0)
    hueco = 0.012 * dur
    for k, (ini, _) in enumerate(frags):
        nivel = 1.15 + 0.17 * (k % 2)
        color = AZUL if k % 2 == 0 else NARANJA
        a1.plot([ini + hueco / 2, ini + C.SEGMENTO_S - hueco / 2], [nivel, nivel], color=color, linewidth=5,
                solid_capstyle="round")
        if len(frags) <= 24:
            a1.text(ini + C.SEGMENTO_S / 2, nivel + 0.07, f"{k + 1}", ha="center", fontsize=7.5, color=TEXTO_2)
    a1.set_xlim(0, dur)
    a1.set_ylim(-1.1, 1.55)
    a1.set_yticks([-1, 0, 1])
    a1.set_xlabel("Tiempo (s)")
    a1.set_ylabel("Amplitud")
    a1.set_title(f"(a) La canción se divide en {len(frags)} fragmentos de {C.SEGMENTO_S:g} s que avanzan "
                 f"{C.SEGMENTO_S * (1 - C.SOLAPE):g} s (solapamiento {C.SOLAPE:.0%}); cada fragmento es un ejemplo")

    t0 = 3.0
    i0 = int((inicio_frag + t0) * C.SR)
    n_tramas = 8
    largo = (n_tramas - 1) * C.HOP + C.N_FFT
    seg = y[i0:i0 + largo]
    ts = np.arange(len(seg)) / C.SR * 1000
    a2.plot(ts, seg / (np.max(np.abs(seg)) + 1e-12), color=GRIS, linewidth=0.6)
    w = signal.get_window("hann", C.N_FFT)
    base, paso, alto = 1.25, 0.32, 0.28
    for k in range(n_tramas):
        tk = (k * C.HOP + np.arange(C.N_FFT)) / C.SR * 1000
        color = AZUL if k % 2 == 0 else NARANJA
        a2.fill_between(tk, base + paso * k, base + paso * k + w * alto, color=color, alpha=0.15, linewidth=0)
        a2.plot(tk, base + paso * k + w * alto, color=color, linewidth=1.4)
        a2.text(tk[0] - 1.5, base + paso * k, f"trama {k}", fontsize=7.5, color=TEXTO_2, ha="right", va="center")
    a2.text(largo / C.SR * 1000, base + paso * n_tramas + alto + 0.05,
            f"cada trama: {C.N_FFT} muestras = {C.N_FFT / C.SR * 1000:.1f} ms con ventana de Hann · salto {C.HOP} "
            f"muestras = {C.HOP / C.SR * 1000:.1f} ms · solapamiento {1 - C.HOP / C.N_FFT:.0%}",
            ha="right", fontsize=9, color=TEXTO)
    a2.set_xlim(-22, largo / C.SR * 1000 + 3)
    a2.set_ylim(-1.1, base + paso * n_tramas + alto + 0.25)
    a2.set_yticks([-1, 0, 1])
    a2.set_xlabel("Tiempo (ms)")
    a2.set_ylabel("Amplitud (norm.)")
    a2.set_title("(b) Dentro de cada fragmento, la STFT toma tramas cortas: cada trama da una muestra de la envolvente")

    env = a["envs"]
    P = a["tempo"]["periodo"]
    compas = 4 * P
    m0 = a["fase"]
    m1 = m0 + 2 * compas
    te = tramas_a_segundos(np.arange(len(env["total"])))
    for i, b in enumerate(C.NOMBRES_BANDA):
        e = env[b] / (env[b].max() + 1e-12)
        a3.plot(te, 2 - i + 0.85 * e, color=COLOR_BANDA[b], linewidth=1.1, label=b)
    for k in range(33):
        x = tramas_a_segundos(m0 + k * compas / 16)
        estilo = dict(color=TEXTO, linewidth=1.4) if k % 16 == 0 else \
            dict(color=TEXTO_2, linewidth=0.9, linestyle="--") if k % 4 == 0 else dict(color=REJILLA, linewidth=0.7)
        a3.axvline(x, **estilo)
    a3.set_xlim(tramas_a_segundos(m0) - 0.05, tramas_a_segundos(m1) + 0.05)
    a3.set_yticks([0.4, 1.4, 2.4])
    a3.set_yticklabels(C.NOMBRES_BANDA[::-1])
    a3.set_xlabel("Tiempo (s)")
    a3.set_title(f"(c) Rejilla del compás: 2 compases de 4 pulsos (P = {P / C.FS_ENV * 1000:.0f} ms) divididos en 16 "
                 "semicorcheas; se promedia la envolvente en cada casilla")
    G.titulo_figura(fig, f"Segmentación de la señal ({d['cancion']}, a {C.SR} Hz)")
    return G.terminar(fig, nombre_archivo, mostrar)


def figura_tempos(filas, nombre_archivo="tempos_por_genero.png", mostrar=False):
    generos = [g for g in C.GENEROS if any(d["genero"] == g for d in filas)]
    fig, ax = plt.subplots(figsize=(11, 4.6), constrained_layout=True)
    for i, g in enumerate(generos):
        v = [d["tempo_BPM"] for d in filas if d["genero"] == g]
        ax.scatter(v, np.full(len(v), i) + np.linspace(-0.12, 0.12, len(v)), s=60, color=G.COLOR_GENERO[g],
                   marker=G.MARCADOR_GENERO[g], edgecolors=SUPERFICIE, linewidths=1, zorder=3)
    ax.set_yticks(range(len(generos)))
    ax.set_yticklabels([G.nombre_genero(g) for g in generos])
    ax.set_xlabel("Tempo estimado (BPM, mediana de los fragmentos de cada canción)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Cada punto es una canción: el tempo solo no basta, varios géneros comparten el mismo rango")
    G.titulo_figura(fig, "Tempo por género")
    return G.terminar(fig, nombre_archivo, mostrar)


# ============================================================ Todo junto
def analizar(carpeta=None, cancion=None, mostrar=False):
    carpeta = Path(carpeta or carpeta_por_defecto())
    canciones = listar_canciones(carpeta)
    if not canciones:
        print(f"No hay audios en {carpeta}. Vea data/canciones/LEEME.md o ejecute: python main.py sinteticos")
        return None
    print(f"Analizando {len(canciones)} canciones de {carpeta}")
    filas, extras = [], {}
    for ruta, genero in canciones:
        d, extra = caracterizar(ruta, genero)
        filas.append(d)
        extras[d["cancion"]] = extra
        print(f"  {d['cancion']:<26} {d['formato']:>4} {d['fs_Hz']} Hz {d['canales']} can. {d['duracion_s']:6.1f} s  "
              f"RMS {d['rms_dBFS']:6.1f} dBFS  tempo {d['tempo_BPM']:6.1f} BPM  R[P] {d['claridad_pulso']:.2f}")
    guardar_tabla(filas)
    resumen = resumen_por_genero(filas)

    # una canción representativa por género (la primera de cada uno)
    ejemplos = []
    for g in C.GENEROS:
        d = next((x for x in filas if x["genero"] == g), None)
        if d:
            ejemplos.append((d, extras[d["cancion"]]))
    elegida = cancion or ejemplos[0][0]["cancion"]
    if elegida not in extras:
        raise ValueError(f"No se encontró '{elegida}'. Opciones: {', '.join(extras)}")
    d_sel = next(x for x in filas if x["cancion"] == elegida)
    ex_sel = extras[elegida]
    ex_sel["todas"] = [(nombre, e["y"]) for nombre, e in extras.items()]

    figura_formas_de_onda(ejemplos, mostrar=mostrar)
    figura_ventanas(d_sel, ex_sel, mostrar=mostrar)
    figura_espectros(ejemplos, mostrar=mostrar)
    _, info_alias = figura_aliasing(d_sel, ex_sel, mostrar=mostrar)
    _, info_ruido = figura_ruido(d_sel, ex_sel, mostrar=mostrar)
    figura_segmentacion(d_sel, ex_sel, mostrar=mostrar)
    figura_tempos(filas, mostrar=mostrar)
    a_sel = ex_sel["analisis"][len(ex_sel["analisis"]) // 2]
    G.graficar_ritmo(a_sel, f"{G.nombre_genero(d_sel['genero'])} ({elegida}), fragmento central",
                     "analisis_ritmico.png", mostrar=mostrar)
    for d, ex in ejemplos:   # una figura de análisis rítmico por género
        G.graficar_ritmo(ex["analisis"][len(ex["analisis"]) // 2], f"{G.nombre_genero(d['genero'])} ({d['cancion']})",
                         f"analisis_ritmico_{d['genero']}.png", mostrar=False)

    patrones = []
    for g in C.GENEROS:
        sel = [a for d in filas if d["genero"] == g for a in extras[d["cancion"]]["analisis"] if a["n_compases"] > 0]
        if sel:
            patrones.append((g, np.mean([a["patron"] for a in sel], axis=0),
                             float(np.median([a["tempo"]["bpm"] for a in sel])), len(sel)))
    G.graficar_patrones(patrones, mostrar=mostrar)

    print(f"\nResumen ({elegida}):")
    if info_alias:
        print(f"  Aliasing sin filtro: +{info_alias['exceso_8k_11k_dB']:.1f} dB de energía falsa entre 8 y 11 kHz")
    print(f"  Ruido blanco 0 dB: tempo {info_ruido['bpm_original']:.1f} -> {info_ruido['bpm_ruido']:.1f} BPM, "
          f"claridad {info_ruido['claridad_original']:.2f} -> {info_ruido['claridad_ruido']:.2f}")
    print("  Fragmentos con el mismo tempo según la SNR: " + ", ".join(
        f"{t} {s} dB: {100 * v:.0f} %" for (t, s), v in sorted(info_ruido["tabla"].items(), key=lambda x: (x[0][0], -x[0][1]))))
    return {"filas": filas, "resumen": resumen, "aliasing": info_alias, "ruido": info_ruido, "patrones": patrones}
