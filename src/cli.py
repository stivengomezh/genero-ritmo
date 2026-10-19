"""
cli.py - Comandos del sistema (se ejecuta con "python main.py" desde la raíz del repositorio).

    python main.py                       menú interactivo
    python main.py sinteticos            genera ritmos de prueba en data/sinteticos/
    python main.py analizar              forma de onda, caracterización, FFT, muestreo, ruido, segmentación
    python main.py ritmo ARCHIVO         espectrograma, envolventes, autocorrelación y patrón de un audio
    python main.py evaluar               clasificador k-NN con validación dejando una canción por fuera
    python main.py clasificar ARCHIVO    predice el género de un audio
    python main.py grabar                graba con el micrófono y predice el género

Opciones generales:
    --carpeta RUTA   carpeta de canciones (por defecto data/canciones; si está vacía, data/sinteticos)
    --no-mostrar     guarda las figuras en results/ sin abrir ventanas
"""
import argparse
import sys
from pathlib import Path

import config as C


def _backend(mostrar):
    if not mostrar:
        import matplotlib
        matplotlib.use("Agg")


def cmd_sinteticos(args):
    from sinteticos import generar_todo
    generar_todo(args.por_genero, args.duracion)


def cmd_analizar(args):
    _backend(not args.no_mostrar)
    from analisis import analizar
    analizar(args.carpeta, args.cancion, mostrar=not args.no_mostrar)


def cmd_ritmo(args):
    _backend(not args.no_mostrar)
    from carga import cargar_audio
    from ritmo import analizar_ritmo
    from graficas import graficar_ritmo, graficar_patrones
    y = cargar_audio(args.archivo)
    i = int(args.inicio * C.SR)
    y = y[i:i + int(args.duracion * C.SR)]
    a = analizar_ritmo(y)
    nombre = Path(args.archivo).stem
    print(f"{nombre}: {len(y) / C.SR:.1f} s | tempo {a['tempo']['bpm']:.1f} BPM | claridad R[P] = "
          f"{a['tempo']['claridad']:.2f} | {a['n_compases']} compases")
    graficar_ritmo(a, nombre, f"ritmo_{nombre}.png", mostrar=not args.no_mostrar)
    graficar_patrones([(nombre, a["patron"], a["tempo"]["bpm"], 1)], f"patron_{nombre}.png",
                      mostrar=not args.no_mostrar)


def cmd_evaluar(args):
    _backend(not args.no_mostrar)
    from clasificador import evaluar
    evaluar(args.carpeta, k=args.k, mostrar=not args.no_mostrar)


def cmd_clasificar(args):
    from carga import cargar_audio
    from clasificador import clasificar_senal, imprimir_clasificacion
    y = cargar_audio(args.archivo)
    if args.inicio is not None or args.duracion is not None:
        i = int((args.inicio or 0) * C.SR)
        y = y[i:] if args.duracion is None else y[i:i + int(args.duracion * C.SR)]
    res = clasificar_senal(y, args.carpeta, k=args.k)
    imprimir_clasificacion(res, Path(args.archivo).name)


def cmd_grabar(args):
    from microfono import grabar
    from clasificador import clasificar_senal, imprimir_clasificacion
    y = grabar(args.segundos)
    imprimir_clasificacion(clasificar_senal(y, args.carpeta, k=args.k), "micrófono")


# ============================================================ Menú
def menu():
    ns = lambda **kw: argparse.Namespace(carpeta=None, no_mostrar=False, k=C.K_VECINOS, **kw)  # noqa: E731
    opciones = {
        "1": ("Generar ritmos sintéticos de prueba", lambda: cmd_sinteticos(argparse.Namespace(por_genero=4, duracion=30.0))),
        "2": ("Análisis de las señales (Entrega 2)", lambda: cmd_analizar(ns(cancion=None))),
        "3": ("Ver el análisis rítmico de un archivo", lambda: cmd_ritmo(ns(archivo=_pedir_archivo(), inicio=0.0, duracion=30.0))),
        "4": ("Evaluar el clasificador", lambda: cmd_evaluar(ns())),
        "5": ("Clasificar un archivo", lambda: cmd_clasificar(ns(archivo=_pedir_archivo(), inicio=None, duracion=None))),
        "6": ("Clasificar desde el micrófono", lambda: cmd_grabar(ns(segundos=C.SEGUNDOS_GRABACION))),
    }
    while True:
        print("\n===== GÉNERO MUSICAL POR RITMO =====")
        for k, (texto, _) in opciones.items():
            print(f"  {k}. {texto}")
        print("  0. Salir")
        e = input("Opción: ").strip()
        if e == "0":
            break
        if e in opciones:
            try:
                opciones[e][1]()
            except (RuntimeError, FileNotFoundError, ValueError) as err:
                print(f"Error: {err}")
        else:
            print("Opción no válida.")


def _pedir_archivo():
    ruta = input("Ruta del archivo de audio: ").strip().strip('"')
    if not Path(ruta).exists():
        raise FileNotFoundError(f"No existe el archivo {ruta}")
    return ruta


# ============================================================ Argumentos
def crear_parser():
    p = argparse.ArgumentParser(description="Reconocimiento de género musical por su ritmo")
    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--carpeta", default=None, help="carpeta de canciones etiquetadas")
    comun.add_argument("--no-mostrar", action="store_true", help="guardar figuras sin abrir ventanas")
    sub = p.add_subparsers(dest="comando")

    s = sub.add_parser("sinteticos", help="generar ritmos sintéticos de prueba")
    s.add_argument("--por-genero", type=int, default=4)
    s.add_argument("--duracion", type=float, default=30.0)
    s.set_defaults(func=cmd_sinteticos)

    s = sub.add_parser("analizar", parents=[comun], help="análisis de las señales (Entrega 2)")
    s.add_argument("--cancion", help="canción para las figuras de detalle (por defecto la primera de salsa)")
    s.set_defaults(func=cmd_analizar)

    s = sub.add_parser("ritmo", parents=[comun], help="análisis rítmico de un archivo")
    s.add_argument("archivo")
    s.add_argument("--inicio", type=float, default=0.0)
    s.add_argument("--duracion", type=float, default=30.0)
    s.set_defaults(func=cmd_ritmo)

    s = sub.add_parser("evaluar", parents=[comun], help="validar el clasificador")
    s.add_argument("--k", type=int, default=C.K_VECINOS)
    s.set_defaults(func=cmd_evaluar)

    s = sub.add_parser("clasificar", parents=[comun], help="predecir el género de un archivo")
    s.add_argument("archivo")
    s.add_argument("--inicio", type=float)
    s.add_argument("--duracion", type=float)
    s.add_argument("--k", type=int, default=C.K_VECINOS)
    s.set_defaults(func=cmd_clasificar)

    s = sub.add_parser("grabar", parents=[comun], help="grabar con el micrófono y predecir el género")
    s.add_argument("--segundos", type=float, default=C.SEGUNDOS_GRABACION)
    s.add_argument("--k", type=int, default=C.K_VECINOS)
    s.set_defaults(func=cmd_grabar)
    return p


def principal():
    args = crear_parser().parse_args()
    if args.comando is None:
        menu()
        return
    try:
        args.func(args)
    except (RuntimeError, FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    principal()
