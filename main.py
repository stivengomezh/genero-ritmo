"""
Reconocimiento de género musical por su ritmo - punto de entrada.

    python main.py            menú interactivo
    python main.py --help     lista de comandos

El código está en src/ (ver README.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from cli import principal  # noqa: E402

if __name__ == "__main__":
    principal()
