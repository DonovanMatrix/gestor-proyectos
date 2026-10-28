"""FUNCTIONAL CORE - reglas de las tareas.

Funciones puras: misma entrada -> misma salida, sin SQLite, sin ReactPy, sin archivos.
"""

from collections import Counter
from dataclasses import replace

from app.core.entregables import buscar_entregable
from app.core.integrantes import buscar_integrante
from app.core.validaciones import (
    convertir_a_enum,
    validar_id_obligatorio,
    validar_texto_obligatorio,
    validar_texto_opcional,
)
from app.domain.models import Estado, Prioridad, Tarea
from app.domain.result import (
    Success,
    buscar_primero,
    combinar,
    de_opcion,
    encadenar,
    mapear,
)


def validar_tarea(tarea: Tarea):
    """Valida los datos de una tarea. Devuelve Success(tarea_limpia) o Failure."""

    def aplicar_limpieza(valores):
        nombre, descripcion, entregable_id = valores
        return replace(
            tarea, nombre=nombre, descripcion=descripcion, entregable_id=entregable_id
        )

    return mapear(
        combinar(
            validar_texto_obligatorio(tarea.nombre, "nombre de la tarea", 100),
            validar_texto_opcional(tarea.descripcion, "descripción", 500),
            validar_id_obligatorio(tarea.entregable_id, "entregable"),
        ),
        aplicar_limpieza,
    )


def crear_tarea(
    nombre, descripcion, entregable_id, responsable_id, prioridad, estado=Estado.PENDIENTE
):
    """Crea una tarea validando todos sus datos. Aún no tiene id (lo da la base de datos)."""
    return encadenar(
        combinar(
            convertir_a_enum(Prioridad, prioridad, "prioridad"),
            convertir_a_enum(Estado, estado, "estado"),
        ),
        lambda enums: validar_tarea(
            Tarea(
                id=None,
                nombre=nombre,
                descripcion=descripcion,
                entregable_id=entregable_id,
                responsable_id=responsable_id,
                prioridad=enums[0],
                estado=enums[1],
            )
        ),
    )


def actualizar_tarea(tarea: Tarea, **cambios):
    """Devuelve una tarea NUEVA con los cambios aplicados (y validada). La original no cambia.

    Ejemplo: actualizar_tarea(tarea, nombre="Nuevo nombre", prioridad=Prioridad.ALTA)
    """
    return validar_tarea(replace(tarea, **cambios))


def verificar_referencias(tarea: Tarea, entregables, integrantes):
    """Comprueba que el entregable (y el responsable, si hay) realmente existen."""
    entregable = de_opcion(buscar_entregable(entregables, tarea.entregable_id), "el entregable")
    if tarea.responsable_id is None:
        responsable = Success(None)  # una tarea puede estar sin responsable
    else:
        responsable = de_opcion(
            buscar_integrante(integrantes, tarea.responsable_id), "el integrante"
        )
    return mapear(combinar(entregable, responsable), lambda _: tarea)


def buscar_tarea(tareas, tarea_id):
    """AUSENCIA DE VALOR: Some(tarea) si existe, Nothing() si no existe."""
    return buscar_primero(tareas, lambda t: t.id == tarea_id)


def contar_pendientes(tareas) -> int:
    """Cuenta las tareas que todavía no están terminadas."""
    return sum(1 for t in tareas if t.estado != Estado.TERMINADA)


def contar_pendientes_por_integrante(tareas) -> dict:
    """{responsable_id: cantidad de tareas sin terminar}. Ignora tareas sin responsable."""
    return dict(
        Counter(
            t.responsable_id
            for t in tareas
            if t.responsable_id is not None and t.estado != Estado.TERMINADA
        )
    )


def porcentaje_terminado(tareas) -> int:
    """Porcentaje (0-100) de tareas terminadas. Sin tareas devuelve 0."""
    if not tareas:
        return 0
    terminadas = sum(1 for t in tareas if t.estado == Estado.TERMINADA)
    return round(100 * terminadas / len(tareas))
