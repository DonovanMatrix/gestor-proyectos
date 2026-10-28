"""El Functional Core no debe depender de efectos externos.

Esta prueba lee el código fuente de `app/core/` y `app/domain/` y comprueba que
no importan SQLite, ReactPy, FastAPI, ni módulos de archivos / consola / red.
"""

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2] / "app"
CARPETAS_PURAS = [RAIZ / "core", RAIZ / "domain"]
PROHIBIDOS = {
    "sqlite3", "reactpy", "fastapi", "uvicorn", "starlette",
    "os", "sys", "pathlib", "shutil", "socket", "logging", "time", "random",
    "app.adapters", "app.ui", "app.shell", "app.main",
}


def archivos_puros():
    return sorted(p for carpeta in CARPETAS_PURAS for p in carpeta.glob("*.py"))


def modulos_importados(ruta: Path):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            yield from (alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            yield nodo.module


@pytest.mark.parametrize("ruta", archivos_puros(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_el_core_no_importa_efectos_externos(ruta):
    prohibidos = [
        m for m in modulos_importados(ruta)
        if m in PROHIBIDOS or m.split(".")[0] in PROHIBIDOS
    ]
    assert prohibidos == [], f"{ruta.name} importa módulos con efectos: {prohibidos}"


@pytest.mark.parametrize("ruta", archivos_puros(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_el_core_no_imprime_ni_abre_archivos(ruta):
    llamadas = {
        nodo.func.id
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8")))
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
    }
    assert not llamadas & {"print", "open", "input"}
