"""FUNCTIONAL CORE - reglas del proyecto."""

from app.core.validaciones import validar_texto_obligatorio, validar_texto_opcional
from app.domain.models import Proyecto, Resumen
from app.domain.result import buscar_primero, combinar, mapear


def crear_proyecto(nombre, descripcion):
    """Valida los datos y devuelve Success(Proyecto sin id) o Failure."""
    return mapear(
        combinar(
            validar_texto_obligatorio(nombre, "nombre del proyecto", 100),
            validar_texto_opcional(descripcion, "descripción", 500),
        ),
        lambda v: Proyecto(id=None, nombre=v[0], descripcion=v[1]),
    )


def buscar_proyecto(proyectos, proyecto_id):
    """AUSENCIA DE VALOR: Some(proyecto) o Nothing()."""
    return buscar_primero(proyectos, lambda p: p.id == proyecto_id)


def resumir_proyecto(integrantes, entregables, tareas) -> Resumen:
    """Totales para la pantalla principal."""
    return Resumen(
        integrantes=len(integrantes),
        entregables=len(entregables),
        tareas=len(tareas),
    )
