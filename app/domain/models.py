"""Modelos del dominio.

Todos los modelos son `frozen=True`: una vez creados NO se pueden modificar.
Para "cambiar" una tarea se crea una copia nueva con `dataclasses.replace`.
Esto es la INMUTABILIDAD del proyecto.
"""

from dataclasses import dataclass
from enum import Enum


class Estado(Enum):
    """Columnas del tablero Kanban."""

    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    EN_REVISION = "En revisión"
    TERMINADA = "Terminada"


class Prioridad(Enum):
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


# Orden en que se muestran las columnas del Kanban.
ESTADOS_KANBAN = (
    Estado.PENDIENTE,
    Estado.EN_PROGRESO,
    Estado.EN_REVISION,
    Estado.TERMINADA,
)

# Menor número = más urgente. Se usa para ordenar tareas.
PESO_PRIORIDAD = {
    Prioridad.ALTA: 0,
    Prioridad.MEDIA: 1,
    Prioridad.BAJA: 2,
}


# `id` es None mientras el objeto todavía no se ha guardado en SQLite.
# La base de datos asigna el id real y devuelve una copia con ese id.


@dataclass(frozen=True)
class Proyecto:
    id: int | None
    nombre: str
    descripcion: str


@dataclass(frozen=True)
class Integrante:
    id: int | None
    nombre: str


@dataclass(frozen=True)
class Entregable:
    """Paquete de trabajo de la EDT (responde: ¿qué trabajo hay que realizar?)."""

    id: int | None
    nombre: str
    descripcion: str
    proyecto_id: int


@dataclass(frozen=True)
class Tarea:
    """Unidad de trabajo dentro de un entregable.

    `estado` dice en qué punto del Kanban está (¿en qué estado está el trabajo?).
    `responsable_id` es None cuando la tarea aún no tiene responsable.
    """

    id: int | None
    nombre: str
    descripcion: str
    entregable_id: int
    responsable_id: int | None
    prioridad: Prioridad
    estado: Estado


@dataclass(frozen=True)
class Resumen:
    """Totales que se muestran en la pantalla principal."""

    integrantes: int
    entregables: int
    tareas: int
