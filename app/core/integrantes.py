"""FUNCTIONAL CORE - reglas de los integrantes del equipo."""

from app.core.validaciones import validar_texto_obligatorio
from app.domain.models import Integrante
from app.domain.result import Nothing, Some, Success, buscar_primero, dato_invalido, encadenar

SIN_ASIGNAR = "Sin asignar"


def crear_integrante(nombre, existentes=()):
    """Valida el nombre y rechaza duplicados (sin distinguir mayúsculas)."""

    def rechazar_duplicado(nombre_limpio):
        ya_existe = any(i.nombre.lower() == nombre_limpio.lower() for i in existentes)
        if ya_existe:
            return dato_invalido(f"Ya existe un integrante llamado '{nombre_limpio}'.")
        return Success(Integrante(id=None, nombre=nombre_limpio))

    return encadenar(validar_texto_obligatorio(nombre, "nombre", 60), rechazar_duplicado)


def buscar_integrante(integrantes, integrante_id):
    """AUSENCIA DE VALOR: Some(integrante) o Nothing()."""
    return buscar_primero(integrantes, lambda i: i.id == integrante_id)


def nombre_integrante(integrantes, integrante_id) -> str:
    """Nombre para mostrar en pantalla; "Sin asignar" si no hay responsable."""
    match buscar_integrante(integrantes, integrante_id):
        case Some(valor=integrante):
            return integrante.nombre
        case Nothing():
            return SIN_ASIGNAR
