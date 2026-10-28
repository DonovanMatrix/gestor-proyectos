"""Datos de ejemplo compartidos por las pruebas unitarias (sin SQLite ni ReactPy)."""

import pytest

from app.domain.models import Estado, Integrante, Entregable, Prioridad, Tarea


@pytest.fixture
def tareas():
    return (
        Tarea(1, "Levantar requisitos", "", 1, 10, Prioridad.ALTA, Estado.PENDIENTE),
        Tarea(2, "Diseñar base de datos", "", 1, 20, Prioridad.MEDIA, Estado.EN_PROGRESO),
        Tarea(3, "Crear interfaz", "", 2, 10, Prioridad.BAJA, Estado.EN_REVISION),
        Tarea(4, "Realizar pruebas", "", 2, None, Prioridad.ALTA, Estado.TERMINADA),
    )


@pytest.fixture
def integrantes():
    return (Integrante(10, "Ana"), Integrante(20, "Carlos"))


@pytest.fixture
def entregables():
    return (Entregable(1, "Análisis", "", 1), Entregable(2, "Desarrollo", "", 1))
