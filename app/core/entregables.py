"""FUNCTIONAL CORE - reglas de los entregables (paquetes de trabajo de la EDT).

La EDT responde: ¿QUÉ trabajo hay que realizar?
Es un árbol de dos niveles:   Proyecto -> Entregable -> Tarea
"""

from app.core.filtros import crear_filtro_por_entregable, filtrar_tareas
from app.core.validaciones import (
    validar_id_obligatorio,
    validar_texto_obligatorio,
    validar_texto_opcional,
)
from app.domain.models import Entregable
from app.domain.result import buscar_primero, combinar, mapear


def crear_entregable(nombre, descripcion, proyecto_id):
    """Valida los datos y devuelve Success(Entregable sin id) o Failure."""
    return mapear(
        combinar(
            validar_texto_obligatorio(nombre, "nombre del entregable", 100),
            validar_texto_opcional(descripcion, "descripción", 500),
            validar_id_obligatorio(proyecto_id, "proyecto"),
        ),
        lambda v: Entregable(id=None, nombre=v[0], descripcion=v[1], proyecto_id=v[2]),
    )


def buscar_entregable(entregables, entregable_id):
    """AUSENCIA DE VALOR: Some(entregable) o Nothing()."""
    return buscar_primero(entregables, lambda e: e.id == entregable_id)


def construir_edt(entregables, tareas):
    """Arma la EDT sin modificar nada: tupla de (entregable, tupla de sus tareas).

    Cada entregable usa una closure (`crear_filtro_por_entregable`) que recuerda su id.
    """
    return tuple(
        (e, filtrar_tareas(tareas, crear_filtro_por_entregable(e.id))) for e in entregables
    )
