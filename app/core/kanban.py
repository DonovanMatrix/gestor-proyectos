"""FUNCTIONAL CORE - reglas del tablero Kanban.

El Kanban responde: ¿en qué ESTADO está el trabajo?

Transiciones permitidas (todas las demás se rechazan):

    Pendiente    -> En progreso
    En progreso  -> En revisión   (avance normal)
                 -> Pendiente     (se pausa o se devuelve a la cola)
    En revisión  -> Terminada     (la revisión se aprueba)
                 -> En progreso   (la revisión se rechaza y hay que corregir)
    Terminada    -> En progreso   (se reabre porque apareció un error)

No se permite saltar etapas (por ejemplo Pendiente -> Terminada) porque
nada llegaría a revisión.
"""

from dataclasses import replace

from app.core.filtros import crear_filtro_por_estado, filtrar_tareas
from app.core.validaciones import convertir_a_enum
from app.domain.models import ESTADOS_KANBAN, Estado
from app.domain.result import Success, encadenar, mapear, transicion_invalida


def estados_siguientes(estado):
    """PATTERN MATCHING: a qué estados puede pasar una tarea desde `estado`."""
    match estado:
        case Estado.PENDIENTE:
            return (Estado.EN_PROGRESO,)
        case Estado.EN_PROGRESO:
            return (Estado.EN_REVISION, Estado.PENDIENTE)
        case Estado.EN_REVISION:
            return (Estado.TERMINADA, Estado.EN_PROGRESO)
        case Estado.TERMINADA:
            return (Estado.EN_PROGRESO,)
        case _:
            # Estado desconocido: no hay transiciones posibles.
            return ()


def validar_transicion(actual, nuevo):
    """PATTERN MATCHING sobre el par (estado actual, estado nuevo).

    Devuelve Success(nuevo) si la transición está permitida o un Failure explicando por qué no.
    """
    match (actual, nuevo):
        case (a, b) if a == b:
            return transicion_invalida(f"La tarea ya está en '{a.value}'.")
        case (a, b) if b in estados_siguientes(a):
            return Success(b)
        case (a, b):
            permitidos = ", ".join(e.value for e in estados_siguientes(a))
            return transicion_invalida(
                f"No se puede pasar de '{a.value}' a '{b.value}'. "
                f"Desde '{a.value}' solo se permite: {permitidos}."
            )


def cambiar_estado(tarea, nuevo_estado):
    """Devuelve Success(tarea_nueva) o Failure. La tarea original NUNCA se modifica.

    `nuevo_estado` puede ser un `Estado` o su texto (por ejemplo "En revisión").
    """
    return mapear(
        encadenar(
            convertir_a_enum(Estado, nuevo_estado, "estado"),
            lambda nuevo: validar_transicion(tarea.estado, nuevo),
        ),
        # `replace` crea una COPIA con el estado cambiado: inmutabilidad.
        lambda nuevo: replace(tarea, estado=nuevo),
    )


def agrupar_por_estado(tareas):
    """Arma las columnas del tablero: {Estado: tupla de tareas de ese estado}."""
    return {
        estado: filtrar_tareas(tareas, crear_filtro_por_estado(estado))
        for estado in ESTADOS_KANBAN
    }
