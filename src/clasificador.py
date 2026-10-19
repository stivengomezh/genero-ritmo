"""
clasificador.py - Primer clasificador de género: k vecinos más cercanos (k-NN).

1. Cada canción se divide en fragmentos de 10 s (solapados 50 %) y cada fragmento se
   resume en un vector de 52 características rítmicas (caracteristicas.py).
2. Las características se estandarizan: z = (v - media) / desviación, con la media y la
   desviación del conjunto de ENTRENAMIENTO (así ninguna domina por tener números grandes).
3. Para un fragmento nuevo se buscan los k fragmentos más cercanos (distancia euclidiana)
   y votan por su género. El género de una canción es el más votado entre sus fragmentos.

Validación "dejando una canción por fuera": se entrena con todas las canciones menos una
y se prueba con esa; se repite con cada canción. Nunca hay fragmentos de la misma canción
en entrenamiento y prueba a la vez (si los hubiera, el clasificador reconocería la canción,
no el género, y el resultado sería engañosamente alto).
"""
import csv
import time
from collections import Counter
from pathlib import Path

import numpy as np

import config as C
from carga import cargar_audio, fragmentar, fragmentos_para_clasificar, listar_canciones, carpeta_por_defecto
from caracteristicas import caracteristicas, nombres_caracteristicas


# ============================================================ Conjunto de datos
def extraer_conjunto(carpeta=None, usar_cache=True):
    """Calcula las características de todos los fragmentos de todas las canciones.

    Devuelve un diccionario con X (fragmentos x 52), genero, cancion, inicio_s y tempo (BPM).
    Guarda una copia en results/caracteristicas_<carpeta>.npz para no recalcular.
    """
    carpeta = Path(carpeta or carpeta_por_defecto())
    canciones = listar_canciones(carpeta)
    if not canciones:
        raise FileNotFoundError(f"No hay canciones en {carpeta}. Vea data/canciones/LEEME.md "
                                f"o genere ritmos de prueba con: python main.py sinteticos")
    cache = C.CARPETA_RESULTADOS / f"caracteristicas_{carpeta.name}.npz"
    # la copia se invalida si cambian los audios o el código que calcula las características
    import hashlib
    codigo = b"".join((Path(__file__).parent / m).read_bytes() for m in ("config.py", "carga.py", "ritmo.py", "caracteristicas.py"))
    firma = hashlib.sha1(codigo).hexdigest()[:12] + ";" + ";".join(f"{p.name}:{p.stat().st_size}" for p, _ in canciones)
    if usar_cache and cache.exists():
        d = np.load(cache, allow_pickle=False)
        if str(d["firma"]) == firma and d["X"].shape[1] == len(nombres_caracteristicas()):
            print(f"Características leídas de {cache.name} ({len(d['X'])} fragmentos)")
            return {k: d[k] for k in ("X", "genero", "cancion", "inicio_s", "tempo")}

    print(f"Extrayendo características de {len(canciones)} canciones de {carpeta}")
    X, gen, can, ini, tem = [], [], [], [], []
    t0 = time.perf_counter()
    for ruta, genero in canciones:
        y = cargar_audio(ruta)
        frags = fragmentos_para_clasificar(y)
        for inicio, fragmento in frags:
            v, a = caracteristicas(fragmento)
            X.append(v)
            gen.append(genero)
            can.append(ruta.stem)
            ini.append(inicio)
            tem.append(a["tempo"]["bpm"])
        print(f"  {ruta.name:<28} {len(y) / C.SR:6.1f} s  {len(frags):3d} fragmentos  "
              f"tempo mediano {np.median(tem[-len(frags):]):6.1f} BPM")
    datos = {"X": np.array(X), "genero": np.array(gen), "cancion": np.array(can), "inicio_s": np.array(ini),
             "tempo": np.array(tem)}
    C.CARPETA_RESULTADOS.mkdir(exist_ok=True)
    np.savez(cache, firma=firma, **datos)
    print(f"  ({time.perf_counter() - t0:.0f} s)  Guardado en {cache}")
    return datos


# ============================================================ k-NN
class KNN:
    def __init__(self, k=C.K_VECINOS, columnas=None):
        self.k = k
        self.columnas = columnas            # subconjunto de características (None = todas)

    def _sel(self, X):
        return X if self.columnas is None else X[:, self.columnas]

    def entrenar(self, X, y):
        X = self._sel(X)
        self.media = X.mean(axis=0)
        self.desv = X.std(axis=0) + 1e-9
        self.X = (X - self.media) / self.desv
        self.y = np.asarray(y)
        return self

    def votos(self, X):
        """Para cada fragmento: {género: peso}, con peso = 1/(distancia + ε) de los k vecinos."""
        Z = (self._sel(X) - self.media) / self.desv
        D = np.sqrt(((Z[:, None, :] - self.X[None, :, :]) ** 2).sum(axis=2))
        k = min(self.k, len(self.y))
        vecinos = np.argsort(D, axis=1)[:, :k]
        salida = []
        for i in range(len(Z)):
            v = Counter()
            for j in vecinos[i]:
                v[self.y[j]] += 1.0 / (D[i, j] + 1e-6)
            salida.append(v)
        return salida

    def predecir(self, X):
        return np.array([v.most_common(1)[0][0] for v in self.votos(X)])


def votar_cancion(votos_fragmentos):
    """Género de una canción: suma de los votos ponderados de todos sus fragmentos."""
    total = Counter()
    for v in votos_fragmentos:
        s = sum(v.values())
        for g, p in v.items():
            total[g] += p / s          # cada fragmento aporta 1 voto repartido entre géneros
    n = sum(total.values())
    return total.most_common(1)[0][0], {g: p / n for g, p in total.items()}


# ============================================================ Validación
def validar(datos, k=C.K_VECINOS, columnas=None):
    """Validación dejando una canción por fuera. Devuelve aciertos por fragmento y por canción."""
    X, gen, can = datos["X"], datos["genero"], datos["cancion"]
    pred_frag = np.empty(len(X), dtype=object)
    filas_cancion = []
    for nombre in np.unique(can):
        prueba = can == nombre
        modelo = KNN(k, columnas).entrenar(X[~prueba], gen[~prueba])
        votos = modelo.votos(X[prueba])
        pred_frag[prueba] = [v.most_common(1)[0][0] for v in votos]
        g_pred, prob = votar_cancion(votos)
        filas_cancion.append((nombre, gen[prueba][0], g_pred, prob.get(g_pred, 0.0)))
    exac_frag = float(np.mean(pred_frag == gen))
    exac_can = float(np.mean([r == p for _, r, p, _ in filas_cancion]))
    return {"pred_fragmento": pred_frag.astype(str), "canciones": filas_cancion, "exactitud_fragmento": exac_frag,
            "exactitud_cancion": exac_can}


def matriz_confusion(reales, predichos, clases):
    idx = {c: i for i, c in enumerate(clases)}
    M = np.zeros((len(clases), len(clases)), dtype=int)
    for r, p in zip(reales, predichos):
        M[idx[r], idx[p]] += 1
    return M


GRUPOS = {
    "Solo tempo": lambda n: [i for i, x in enumerate(n) if x == "tempo_log2"],
    "Tempo y subdivisión (autocorrelación)": lambda n: [i for i, x in enumerate(n) if x.startswith(("tempo", "claridad", "R_"))],
    "Energía, densidad y regularidad por banda": lambda n: [i for i, x in enumerate(n) if x.startswith(("energia", "densidad", "regularidad"))],
    "Patrón de compás (posición y |DFT|)": lambda n: [i for i, x in enumerate(n) if x.startswith(("pulso", "contratiempo", "semicorchea", "dft"))],
    "Todas las características": lambda n: list(range(len(n))),
}


def evaluar(carpeta=None, k=C.K_VECINOS, graficar=True, mostrar=False):
    datos = extraer_conjunto(carpeta)
    nombres = nombres_caracteristicas()
    clases = [g for g in C.GENEROS if g in set(datos["genero"])]
    n_can = len(np.unique(datos["cancion"]))
    print(f"\n{len(datos['X'])} fragmentos de {n_can} canciones, {len(clases)} géneros "
          f"(azar = {100 / len(clases):.0f} %). Validación dejando una canción por fuera, k = {k}.\n")

    comparacion = []
    for nombre_grupo, f in GRUPOS.items():
        cols = f(nombres)
        r = validar(datos, k, cols)
        comparacion.append((nombre_grupo, len(cols), r["exactitud_fragmento"], r["exactitud_cancion"]))
        print(f"  {nombre_grupo:<45} {len(cols):3d} caract.  fragmentos {r['exactitud_fragmento']:6.1%}  "
              f"canciones {r['exactitud_cancion']:6.1%}")
    res = validar(datos, k)

    print("\n  Canción                        real          predicho      confianza")
    for nombre, real, pred, conf in res["canciones"]:
        marca = "  " if real == pred else "✗ "
        print(f"  {marca}{nombre:<28} {real:<13} {pred:<13} {conf:5.0%}")

    C.CARPETA_RESULTADOS.mkdir(exist_ok=True)
    with open(C.CARPETA_RESULTADOS / "clasificacion_canciones.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cancion", "genero_real", "genero_predicho", "confianza"])
        for fila in res["canciones"]:
            w.writerow([fila[0], fila[1], fila[2], f"{fila[3]:.3f}"])
    with open(C.CARPETA_RESULTADOS / "clasificacion_grupos.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["caracteristicas", "cantidad", "exactitud_fragmento", "exactitud_cancion"])
        for g, n, ef, ec in comparacion:
            w.writerow([g, n, f"{ef:.3f}", f"{ec:.3f}"])

    M_frag = matriz_confusion(datos["genero"], res["pred_fragmento"], clases)
    M_can = matriz_confusion([c[1] for c in res["canciones"]], [c[2] for c in res["canciones"]], clases)
    resultado = {"datos": datos, "clases": clases, "validacion": res, "comparacion": comparacion,
                 "M_fragmento": M_frag, "M_cancion": M_can, "k": k, "nombres": nombres}
    if graficar:
        import graficas as G
        G.graficar_clasificacion(resultado, mostrar=mostrar)
        G.graficar_mapa_caracteristicas(datos, clases, mostrar=mostrar)
    return resultado


# ============================================================ Clasificar un audio nuevo
def clasificar_senal(y, carpeta=None, k=C.K_VECINOS, datos=None):
    """Entrena con todas las canciones de la base y clasifica la señal `y` (ya a SR Hz)."""
    datos = datos or extraer_conjunto(carpeta)
    modelo = KNN(k).entrenar(datos["X"], datos["genero"])
    frags = fragmentar(y)
    vectores, tempos = [], []
    for _, f in frags:
        v, a = caracteristicas(f)
        vectores.append(v)
        tempos.append(a["tempo"]["bpm"])
    votos = modelo.votos(np.array(vectores))
    genero, prob = votar_cancion(votos)
    return {"genero": genero, "probabilidades": dict(sorted(prob.items(), key=lambda x: -x[1])),
            "por_fragmento": [(ini, v.most_common(1)[0][0]) for (ini, _), v in zip(frags, votos)],
            "tempo": float(np.median(tempos))}


def imprimir_clasificacion(res, nombre=""):
    print("=" * 60)
    print(f"{nombre}  ->  GÉNERO: {C.NOMBRES_GENERO.get(res['genero'], res['genero']).upper()}")
    print(f"  Tempo estimado: {res['tempo']:.0f} BPM")
    print("  Votos:")
    for g, p in res["probabilidades"].items():
        print(f"    {C.NOMBRES_GENERO.get(g, g):<12} {'█' * int(round(30 * p)):<30} {p:5.0%}")
    if len(res["por_fragmento"]) > 1:
        print("  Por fragmento: " + ", ".join(f"{ini:.0f}s:{g}" for ini, g in res["por_fragmento"]))
    print("=" * 60)
