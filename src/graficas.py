"""
graficas.py - Estilo común y figuras del análisis rítmico y del clasificador.

    graficar_ritmo                espectrograma, envolventes, autocorrelación y espectro rítmico
    graficar_patrones             patrón de compás promedio de cada género
    graficar_clasificacion        matrices de confusión y comparación de grupos de características
    graficar_mapa_caracteristicas proyección de los fragmentos en 2 dimensiones (PCA)
"""
import numpy as np
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

import config as C  # noqa: E402
from ritmo import tramas_a_segundos, pulsos, espectro_ritmico  # noqa: E402

# ---------------------------------------------------------------- Paleta
# Colores categóricos en orden fijo (validados para daltonismo en pares adyacentes).
CATEGORICOS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
AZUL, NARANJA, AGUA = CATEGORICOS[:3]
COLOR_GENERO = {g: CATEGORICOS[i % 8] for i, g in enumerate(C.GENEROS)}
MARCADOR_GENERO = {g: m for g, m in zip(C.GENEROS, ["o", "s", "^", "D", "v", "P", "X", "*"])}
COLOR_BANDA = {"graves": AZUL, "medios": NARANJA, "agudos": AGUA}
GRIS = "#b9b8b2"
SUPERFICIE = "#fcfcfb"
TEXTO, TEXTO_2, TENUE, REJILLA = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
MAPA_AZUL = LinearSegmentedColormap.from_list(
    "azules", [SUPERFICIE, "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"])

plt.rcParams.update({
    "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
    "axes.edgecolor": TENUE, "axes.labelcolor": TEXTO_2, "axes.titlecolor": TEXTO,
    "axes.titlesize": 11.5, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.labelsize": 10,
    "xtick.color": TENUE, "ytick.color": TENUE, "xtick.labelcolor": TEXTO_2, "ytick.labelcolor": TEXTO_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6,
    "legend.frameon": False, "legend.labelcolor": TEXTO_2, "font.size": 10,
})


def nombre_genero(g):
    return C.NOMBRES_GENERO.get(g, g)


def titulo_figura(fig, texto):
    fig.suptitle(texto, fontsize=13, fontweight="bold", color=TEXTO, x=0.01, ha="left")


def terminar(fig, nombre_archivo, mostrar=False):
    C.CARPETA_RESULTADOS.mkdir(exist_ok=True)
    ruta = C.CARPETA_RESULTADOS / nombre_archivo
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    print(f"  Figura guardada: {ruta}")
    if mostrar:
        plt.show()
    plt.close(fig)
    return ruta


# ============================================================ 1. Cadena de análisis rítmico
def graficar_ritmo(a, titulo="", nombre_archivo="analisis_ritmico.png", mostrar=False, segundos=6.0):
    """Cuatro paneles: espectrograma, envolventes de ataques, autocorrelación y espectro rítmico."""
    envs, tempo = a["envs"], a["tempo"]
    t_env = tramas_a_segundos(np.arange(len(envs["total"])))
    t_fin = min(segundos, t_env[-1])
    beats = tramas_a_segundos(pulsos(a["fase"], tempo["periodo"], len(envs["total"])))

    fig = plt.figure(figsize=(13, 10), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.1, 1.2, 1])
    a_s = fig.add_subplot(gs[0, :])
    a_e = fig.add_subplot(gs[1, :], sharex=a_s)
    a_r = fig.add_subplot(gs[2, 0])
    a_f = fig.add_subplot(gs[2, 1])

    S_db = 20 * np.log10(a["S"] + 1e-6)
    vmax = S_db.max()
    a_s.imshow(S_db, origin="lower", aspect="auto", cmap=MAPA_AZUL, vmin=vmax - 70, vmax=vmax,
               extent=[a["t"][0], a["t"][-1], 0, C.SR / 2 / 1000], interpolation="nearest")
    for b, (f1, f2) in C.BANDAS.items():
        a_s.axhline(f2 / 1000, color=COLOR_BANDA[b], linewidth=1.2, linestyle="--")
        a_s.text(t_fin * 0.995, f2 / 1000, f" {b} ", color=TEXTO, fontsize=8.5, ha="right", va="top",
                 bbox=dict(boxstyle="round,pad=0.15", facecolor=SUPERFICIE, edgecolor="none", alpha=0.8))
    a_s.set_ylim(0, C.SR / 2 / 1000)
    a_s.set_xlim(0, t_fin)
    a_s.set_ylabel("Frecuencia (kHz)")
    a_s.grid(False)
    a_s.set_title("(a) Espectrograma |X(t, f)| en dB: los golpes son líneas verticales (energía en muchas frecuencias a la vez)")

    for i, b in enumerate(C.NOMBRES_BANDA):
        e = envs[b] / (envs[b].max() + 1e-12)
        base = 2 - i
        a_e.fill_between(t_env, base, base + 0.9 * e, color=COLOR_BANDA[b], alpha=0.25, linewidth=0)
        a_e.plot(t_env, base + 0.9 * e, color=COLOR_BANDA[b], linewidth=1.1)
        f1, f2 = C.BANDAS[b]
        a_e.text(-0.01, base + 0.45, f"{b}\n{f1}–{f2} Hz", transform=a_e.get_yaxis_transform(), ha="right",
                 va="center", fontsize=8.5, color=TEXTO_2)
    for x in beats[beats <= t_fin]:
        a_e.axvline(x, color=TENUE, linewidth=0.8, linestyle=":")
    a_e.set_yticks([])
    a_e.set_ylim(-0.05, 3)
    a_e.set_xlabel("Tiempo (s)")
    a_e.set_title(f"(b) Envolventes de ataques por banda (flujo espectral); líneas punteadas = pulsos a "
                  f"{tempo['bpm']:.1f} BPM")

    r = tempo["r"]
    lag_s = np.arange(len(r)) / C.FS_ENV
    a_r.plot(lag_s, r, color=AZUL, linewidth=1.3)
    P_s = tempo["periodo"] / C.FS_ENV
    a_r.axvline(P_s, color=NARANJA, linewidth=1.5, linestyle="--")
    a_r.annotate(f"P = {P_s * 1000:.0f} ms\n→ {tempo['bpm']:.1f} BPM\nR[P] = {tempo['claridad']:.2f}",
                 xy=(P_s, tempo["claridad"]), xytext=(10, 10), textcoords="offset points", fontsize=9, color=TEXTO,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor=SUPERFICIE, edgecolor=REJILLA))
    a_r.axhline(0, color=TENUE, linewidth=0.8)
    a_r.set_xlim(0, min(3.0, lag_s[-1]))
    a_r.set_xlabel("Retardo ℓ (s)")
    a_r.set_ylabel("R[ℓ]")
    a_r.set_title("(c) Autocorrelación de la envolvente total")

    f, E = espectro_ritmico(envs["total"])
    a_f.plot(f * 60, E, color=AZUL, linewidth=1.3)
    a_f.axvline(tempo["bpm"], color=NARANJA, linewidth=1.5, linestyle="--")
    for mult, txt in ((2, "×2"), (4, "×4")):
        if tempo["bpm"] * mult < 600:
            a_f.axvline(tempo["bpm"] * mult, color=TENUE, linewidth=1, linestyle=":")
            a_f.text(tempo["bpm"] * mult, 1.02, txt, ha="center", fontsize=8.5, color=TEXTO_2)
    a_f.set_xlim(0, 600)
    a_f.set_ylim(0, 1.1)
    a_f.set_xlabel("Frecuencia rítmica (BPM = Hz × 60)")
    a_f.set_ylabel("|E(f)| (normalizado)")
    a_f.set_title("(d) Espectro de la envolvente (FFT): pulso y subdivisiones")
    titulo_figura(fig, f"Análisis rítmico{': ' + titulo if titulo else ''}")
    return terminar(fig, nombre_archivo, mostrar)


# ============================================================ 2. Patrones de compás
def dibujar_patron(ax, patron, titulo="", etiquetas=True):
    ax.imshow(patron, cmap=MAPA_AZUL, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    ax.set_xticks(range(C.PASOS_POR_COMPAS))
    ax.set_xticklabels([str(p // 4 + 1) if p % 4 == 0 else "·" for p in range(C.PASOS_POR_COMPAS)], fontsize=8.5)
    ax.set_yticks(range(len(C.NOMBRES_BANDA)))
    ax.set_yticklabels(C.NOMBRES_BANDA if etiquetas else [""] * len(C.NOMBRES_BANDA), fontsize=8.5)
    ax.set_xticks(np.arange(C.PASOS_POR_COMPAS + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(C.NOMBRES_BANDA) + 1) - 0.5, minor=True)
    ax.grid(which="minor", color=SUPERFICIE, linewidth=1.5)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="both", length=0)
    for x in (3.5, 7.5, 11.5):
        ax.axvline(x, color=TENUE, linewidth=1)
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.set_title(titulo, fontsize=10.5)


def graficar_patrones(patrones, nombre_archivo="patrones_compas.png", mostrar=False):
    """patrones: lista de (genero, patron promedio (3x16), tempo mediano, n_fragmentos)."""
    n = len(patrones)
    columnas = 2
    filas = int(np.ceil(n / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(13, 1.75 * filas + 1.2), constrained_layout=True)
    ejes = np.atleast_1d(ejes).ravel()
    for k, (g, patron, bpm, n_frag) in enumerate(patrones):
        dibujar_patron(ejes[k], patron, f"{nombre_genero(g)}  ·  ~{bpm:.0f} BPM  ·  {n_frag} fragmentos",
                       etiquetas=(k % columnas == 0))
    for ax in ejes[n:]:
        ax.set_visible(False)
    titulo_figura(fig, "Patrón rítmico promedio de cada género: dónde caen los golpes en un compás de 4 pulsos")
    fig.text(0.01, -0.02, "Cada fila es una banda (graves = bombo/bajo, medios = caja/congas, agudos = platillos/güira). "
             "Cada columna es una semicorchea; los números marcan los 4 pulsos. Más oscuro = más ataques en esa posición.",
             fontsize=9, color=TEXTO_2)
    return terminar(fig, nombre_archivo, mostrar)


# ============================================================ 3. Clasificación
def _matriz(ax, M, clases, titulo):
    filas = M.sum(axis=1, keepdims=True)
    P = np.divide(M, filas, out=np.zeros_like(M, dtype=float), where=filas > 0)
    ax.imshow(P, cmap=MAPA_AZUL, vmin=0, vmax=1, aspect="equal")
    for i in range(len(clases)):
        for j in range(len(clases)):
            if M[i, j]:
                ax.text(j, i, f"{M[i, j]}", ha="center", va="center", fontsize=9,
                        color=SUPERFICIE if P[i, j] >= 0.55 else TEXTO)
    nombres = [nombre_genero(c) for c in clases]
    ax.set_xticks(range(len(clases)))
    ax.set_xticklabels(nombres, rotation=40, ha="right", fontsize=9)
    ax.set_yticks(range(len(clases)))
    ax.set_yticklabels(nombres, fontsize=9)
    ax.set_xlabel("Género predicho")
    ax.set_ylabel("Género real")
    ax.set_xticks(np.arange(len(clases) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(clases) + 1) - 0.5, minor=True)
    ax.grid(which="minor", color=SUPERFICIE, linewidth=2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="both", length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.set_title(titulo, fontsize=10.5)


def graficar_clasificacion(res, nombre_archivo="clasificacion.png", mostrar=False):
    clases = res["clases"]
    v = res["validacion"]
    fig = plt.figure(figsize=(15, 5.6), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.15])
    _matriz(fig.add_subplot(gs[0, 0]), res["M_cancion"], clases,
            f"(a) Por canción: {v['exactitud_cancion']:.0%} de aciertos")
    _matriz(fig.add_subplot(gs[0, 1]), res["M_fragmento"], clases,
            f"(b) Por fragmento de {C.SEGMENTO_S:g} s: {v['exactitud_fragmento']:.0%}")
    ax = fig.add_subplot(gs[0, 2])
    nombres = [c[0] for c in res["comparacion"]][::-1]
    frag = [100 * c[2] for c in res["comparacion"]][::-1]
    can = [100 * c[3] for c in res["comparacion"]][::-1]
    y = np.arange(len(nombres))
    ax.barh(y + 0.19, can, height=0.36, color=AZUL, label="por canción")
    ax.barh(y - 0.19, frag, height=0.36, color=NARANJA, label="por fragmento")
    for yi, a, b in zip(y, can, frag):
        ax.text(a + 1, yi + 0.19, f"{a:.0f} %", va="center", fontsize=8.5, color=TEXTO_2)
        ax.text(b + 1, yi - 0.19, f"{b:.0f} %", va="center", fontsize=8.5, color=TEXTO_2)
    azar = 100 / len(clases)
    ax.axvline(azar, color=TENUE, linestyle=":", linewidth=1.2)
    ax.text(azar + 1, -0.62, f"azar ({azar:.0f} %)", fontsize=8.5, color=TENUE, va="center")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{n}\n({c[1]} caract.)" for n, c in zip(nombres, res["comparacion"][::-1])], fontsize=8.5)
    ax.set_xlim(0, 112)
    ax.set_xlabel("Exactitud (%)")
    ax.grid(axis="y", visible=False)
    ax.set_ylim(-0.85, len(nombres) - 0.4)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, fontsize=9)
    ax.set_title("(c) ¿Qué características aportan?", fontsize=10.5)
    n_can = len(v["canciones"])
    titulo_figura(fig, f"Clasificación k-NN (k = {res['k']}), validación dejando una canción por fuera "
                       f"({n_can} canciones, {len(res['datos']['X'])} fragmentos)")
    return terminar(fig, nombre_archivo, mostrar)


def graficar_mapa_caracteristicas(datos, clases, nombre_archivo="mapa_caracteristicas.png", mostrar=False):
    """Análisis de componentes principales (PCA): proyecta los vectores estandarizados sobre las
    2 direcciones de mayor varianza (vectores singulares de la matriz de datos)."""
    X = datos["X"]
    Z = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)
    U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    P = Z @ Vt[:2].T
    var = s ** 2 / np.sum(s ** 2)
    fig, ax = plt.subplots(figsize=(10, 6.5), constrained_layout=True)
    for g in clases:
        m = datos["genero"] == g
        ax.scatter(P[m, 0], P[m, 1], s=90 if MARCADOR_GENERO[g] == "*" else 44, c=COLOR_GENERO[g], marker=MARCADOR_GENERO[g], edgecolors=SUPERFICIE,
                   linewidths=0.8, label=nombre_genero(g), alpha=0.9)
    ax.set_xlabel(f"Componente principal 1 ({var[0]:.0%} de la varianza)")
    ax.set_ylabel(f"Componente principal 2 ({var[1]:.0%} de la varianza)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=9.5)
    ax.set_title("Cada punto es un fragmento de 10 s. Solo se ven 2 de las 52 dimensiones, por eso los grupos se "
                 "superponen más que para el clasificador", fontsize=10.5)
    titulo_figura(fig, "Mapa de las características rítmicas (PCA a 2 dimensiones)")
    return terminar(fig, nombre_archivo, mostrar)
