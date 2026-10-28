"""Pruebas de las reglas Kanban (pattern matching) y de la inmutabilidad al cambiar estado."""

import pytest

from app.core.kanban import (
    agrupar_por_estado,
    cambiar_estado,
    estados_siguientes,
    validar_transicion,
)
from app.domain.models import Estado, Prioridad, Tarea
from app.domain.result import CodigoError, Failure, Success


def tarea_en(estado):
    return Tarea(1, "Tarea", "", 1, None, Prioridad.MEDIA, estado)


# ------------------------------------------------------------ transiciones válidas
@pytest.mark.parametrize(
    "actual, nuevo",
    [
        (Estado.PENDIENTE, Estado.EN_PROGRESO),
        (Estado.EN_PROGRESO, Estado.EN_REVISION),
        (Estado.EN_PROGRESO, Estado.PENDIENTE),
        (Estado.EN_REVISION, Estado.TERMINADA),
        (Estado.EN_REVISION, Estado.EN_PROGRESO),
        (Estado.TERMINADA, Estado.EN_PROGRESO),
    ],
)
def test_transiciones_validas(actual, nuevo):
    resultado = cambiar_estado(tarea_en(actual), nuevo)
    assert isinstance(resultado, Success)
    assert resultado.valor.estado == nuevo


def test_flujo_completo_pendiente_a_terminada():
    tarea = tarea_en(Estado.PENDIENTE)
    for siguiente in (Estado.EN_PROGRESO, Estado.EN_REVISION, Estado.TERMINADA):
        tarea = cambiar_estado(tarea, siguiente).valor
    assert tarea.estado == Estado.TERMINADA


# ------------------------------------------------------------ transiciones inválidas
@pytest.mark.parametrize(
    "actual, nuevo",
    [
        (Estado.PENDIENTE, Estado.EN_REVISION),
        (Estado.PENDIENTE, Estado.TERMINADA),
        (Estado.EN_PROGRESO, Estado.TERMINADA),
        (Estado.EN_REVISION, Estado.PENDIENTE),
        (Estado.TERMINADA, Estado.PENDIENTE),
        (Estado.TERMINADA, Estado.EN_REVISION),
    ],
)
def test_transiciones_invalidas_devuelven_failure(actual, nuevo):
    resultado = cambiar_estado(tarea_en(actual), nuevo)
    assert isinstance(resultado, Failure)
    assert resultado.error.codigo == CodigoError.TRANSICION_INVALIDA


def test_pasar_al_mismo_estado_se_rechaza():
    resultado = cambiar_estado(tarea_en(Estado.PENDIENTE), Estado.PENDIENTE)
    assert isinstance(resultado, Failure)
    assert "ya está" in resultado.error.mensaje


def test_la_tarea_original_no_cambia_cuando_la_operacion_falla():
    original = tarea_en(Estado.PENDIENTE)
    resultado = cambiar_estado(original, Estado.TERMINADA)
    assert isinstance(resultado, Failure)
    assert original.estado == Estado.PENDIENTE


def test_la_tarea_original_no_cambia_cuando_la_operacion_funciona():
    original = tarea_en(Estado.PENDIENTE)
    nueva = cambiar_estado(original, Estado.EN_PROGRESO).valor
    assert original.estado == Estado.PENDIENTE  # inmutabilidad
    assert nueva.estado == Estado.EN_PROGRESO
    assert nueva is not original
    assert (nueva.id, nueva.nombre) == (original.id, original.nombre)


def test_el_mensaje_de_error_explica_que_se_permite():
    mensaje = cambiar_estado(tarea_en(Estado.PENDIENTE), Estado.TERMINADA).error.mensaje
    assert "Pendiente" in mensaje and "Terminada" in mensaje and "En progreso" in mensaje


# ------------------------------------------------------------ estado desconocido
def test_estado_desconocido_en_texto_devuelve_failure():
    resultado = cambiar_estado(tarea_en(Estado.PENDIENTE), "Archivada")
    assert isinstance(resultado, Failure)
    assert resultado.error.codigo == CodigoError.DATO_INVALIDO
    assert "Archivada" in resultado.error.mensaje


def test_estado_en_texto_valido_se_acepta():
    resultado = cambiar_estado(tarea_en(Estado.PENDIENTE), "En progreso")
    assert resultado.valor.estado == Estado.EN_PROGRESO


def test_estados_siguientes_de_un_valor_desconocido_es_vacio():
    assert estados_siguientes("Archivada") == ()
    assert estados_siguientes(None) == ()


def test_estados_siguientes_de_pendiente():
    assert estados_siguientes(Estado.PENDIENTE) == (Estado.EN_PROGRESO,)


def test_validar_transicion_devuelve_el_nuevo_estado():
    assert validar_transicion(Estado.PENDIENTE, Estado.EN_PROGRESO) == Success(Estado.EN_PROGRESO)


# ------------------------------------------------------------ tablero
def test_agrupar_por_estado_arma_las_cuatro_columnas():
    tareas = (
        tarea_en(Estado.PENDIENTE),
        tarea_en(Estado.PENDIENTE),
        tarea_en(Estado.TERMINADA),
    )
    columnas = agrupar_por_estado(tareas)
    assert list(columnas) == [
        Estado.PENDIENTE,
        Estado.EN_PROGRESO,
        Estado.EN_REVISION,
        Estado.TERMINADA,
    ]
    assert [len(columnas[e]) for e in columnas] == [2, 0, 0, 1]


def test_agrupar_sin_tareas_deja_columnas_vacias():
    assert all(len(ts) == 0 for ts in agrupar_por_estado(()).values())
