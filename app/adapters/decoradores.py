"""IMPERATIVE SHELL - decorador para una preocupación transversal.

`@registrar_operacion` anota en el log cuánto tarda una operación externa
(por ejemplo, una consulta a SQLite) y si terminó con un Failure.

NO contiene reglas de negocio: solo observa y devuelve el MISMO resultado.
Escribir en el log es un efecto secundario, por eso está aquí y no en el core.
"""

import functools
import logging
import time

from app.domain.result import Failure

logger = logging.getLogger("gestor_proyectos")


def registrar_operacion(funcion):
    """Recibe una función y devuelve otra que hace lo mismo, pero midiendo y registrando."""

    @functools.wraps(funcion)  # conserva el nombre y la documentación originales
    def envoltura(*args, **kwargs):
        inicio = time.perf_counter()
        try:
            resultado = funcion(*args, **kwargs)
        finally:
            milisegundos = (time.perf_counter() - inicio) * 1000
            logger.info("%s terminó en %.2f ms", funcion.__name__, milisegundos)
        if isinstance(resultado, Failure):
            logger.warning("%s falló: %s", funcion.__name__, resultado.error.mensaje)
        return resultado

    return envoltura
