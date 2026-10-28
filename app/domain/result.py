"""Manejo funcional de errores y de ausencia de valor.

Dos ideas distintas, y no se deben confundir:

* Result  -> ¿la operación salió bien o mal?     Success(valor) | Failure(error)
* Option  -> ¿el valor buscado existe o no?      Some(valor)    | Nothing()

Ninguna regla de negocio lanza excepciones: devuelve un Success o un Failure.
Una búsqueda que no encuentra nada devuelve Nothing(), nunca un objeto "vacío".
"""

from dataclasses import dataclass
from enum import Enum
from functools import reduce
from typing import Any, Callable, Iterable


# --------------------------------------------------------------------------
# Errores esperados
# --------------------------------------------------------------------------
class CodigoError(Enum):
    DATO_INVALIDO = "dato_invalido"
    NO_EXISTE = "no_existe"
    TRANSICION_INVALIDA = "transicion_invalida"
    ERROR_PERSISTENCIA = "error_persistencia"


@dataclass(frozen=True)
class Error:
    codigo: CodigoError
    mensaje: str


# --------------------------------------------------------------------------
# Result: Success | Failure
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Success:
    valor: Any


@dataclass(frozen=True)
class Failure:
    error: Error


# Constructores de fallos frecuentes (devuelven directamente un Failure).
def dato_invalido(mensaje: str) -> Failure:
    return Failure(Error(CodigoError.DATO_INVALIDO, mensaje))


def no_existe(entidad: str) -> Failure:
    """`entidad` incluye el artículo: no_existe("la tarea") -> "No existe la tarea."."""
    return Failure(Error(CodigoError.NO_EXISTE, f"No existe {entidad}."))


def transicion_invalida(mensaje: str) -> Failure:
    return Failure(Error(CodigoError.TRANSICION_INVALIDA, mensaje))


def error_persistencia(mensaje: str) -> Failure:
    return Failure(Error(CodigoError.ERROR_PERSISTENCIA, mensaje))


# --------------------------------------------------------------------------
# Option: Some | Nothing  (ausencia de valor)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Some:
    valor: Any


@dataclass(frozen=True)
class Nothing:
    """Representa explícitamente "no se encontró nada"."""


# --------------------------------------------------------------------------
# Funciones de orden superior para combinar resultados
# --------------------------------------------------------------------------
def mapear(resultado, funcion: Callable[[Any], Any]):
    """Si es Success, transforma el valor. Si es Failure, lo deja igual."""
    match resultado:
        case Success(valor):
            return Success(funcion(valor))
        case Failure():
            return resultado


def encadenar(resultado, funcion: Callable[[Any], Any]):
    """Si es Success, ejecuta el siguiente paso (que a su vez devuelve un Result).

    Si algún paso falla, los siguientes NO se ejecutan y se propaga el Failure.
    """
    match resultado:
        case Success(valor):
            return funcion(valor)
        case Failure():
            return resultado


def tuberia(resultado_inicial, *pasos: Callable[[Any], Any]):
    """Encadena varios pasos en orden: tuberia(r, f, g, h) == encadenar(encadenar(encadenar(r, f), g), h)."""
    return reduce(encadenar, pasos, resultado_inicial)


def combinar(*resultados):
    """Si todos son Success devuelve Success(tupla de valores); si no, el primer Failure."""
    for resultado in resultados:
        match resultado:
            case Failure():
                return resultado
    return Success(tuple(r.valor for r in resultados))


def de_opcion(opcion, entidad: str):
    """Convierte Some/Nothing a Success/Failure(NO_EXISTE)."""
    match opcion:
        case Some(valor):
            return Success(valor)
        case Nothing():
            return no_existe(entidad)


def buscar_primero(elementos: Iterable, criterio: Callable[[Any], bool]):
    """Devuelve Some(primer elemento que cumple el criterio) o Nothing()."""
    encontrado = next((e for e in elementos if criterio(e)), None)
    # Un elemento nunca es None en este proyecto; None solo significa "no hubo".
    return Nothing() if encontrado is None else Some(encontrado)
