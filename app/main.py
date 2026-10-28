"""IMPERATIVE SHELL - ensamble e inicio de la aplicación.

FastAPI solo sirve la aplicación ReactPy. NO hay endpoints REST propios.

Ejecutar:   uvicorn app.main:app --reload
"""

import logging
import os

from fastapi import FastAPI
from reactpy import component
from reactpy.backend.fastapi import configure

from app.adapters.database import abrir_conexion, inicializar_esquema
from app.domain.result import Failure
from app.ui.inicio import Inicio

# La ruta de la base se puede cambiar con la variable de entorno GESTOR_DB.
RUTA_DB = os.environ.get("GESTOR_DB", "gestor_proyectos.db")


def crear_aplicacion(ruta_db: str = RUTA_DB) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conexion = abrir_conexion(ruta_db)
    resultado = inicializar_esquema(conexion)  # creación controlada de las tablas
    if isinstance(resultado, Failure):
        raise RuntimeError(resultado.error.mensaje)

    @component
    def Raiz():
        return Inicio(conexion)

    aplicacion = FastAPI(title="Gestor de Proyectos con EDT y Kanban")
    configure(aplicacion, Raiz)  # integra ReactPy dentro de FastAPI
    return aplicacion


app = crear_aplicacion()
