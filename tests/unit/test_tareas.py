"""Pruebas del Functional Core: tareas, inmutabilidad y ausencia de valor."""

import dataclasses

import pytest

from app.core.entregables import construir_edt, crear_entregable
from app.core.integrantes import crear_integrante, nombre_integrante
from app.core.proyectos import crear_proyecto, resumir_proyecto
from app.core.tareas import (
    actualizar_tarea,
    buscar_tarea,
    contar_pendientes,
    contar_pendientes_por_integrante,
    crear_tarea,
    porcentaje_terminado,
    validar_tarea,
    verificar_referencias,
)
from app.domain.models import Estado, Prioridad
from app.domain.result import CodigoError, Failure, Nothing, Some, Success


# ------------------------------------------------------------ crear / validar
def test_tarea_valida_se_crea_pendiente_y_sin_id():
    resultado = crear_tarea("  Escribir informe ", "detalle", 1, None, "Alta")
    assert isinstance(resultado, Success)
    tarea = resultado.valor
    assert tarea.nombre == "Escribir informe"  # se limpian espacios
    assert tarea.estado == Estado.PENDIENTE
    assert tarea.prioridad == Prioridad.ALTA
    assert tarea.id is None
    assert tarea.responsable_id is None


@pytest.mark.parametrize("nombre", ["", "   ", None])
def test_tarea_sin_nombre_es_invalida(nombre):
    resultado = crear_tarea(nombre, "", 1, None, "Alta")
    assert isinstance(resultado, Failure)
    assert resultado.error.codigo == CodigoError.DATO_INVALIDO


def test_nombre_demasiado_largo_es_invalido():
    assert isinstance(crear_tarea("x" * 101, "", 1, None, "Alta"), Failure)
    assert isinstance(crear_tarea("x" * 100, "", 1, None, "Alta"), Success)  # límite exacto


@pytest.mark.parametrize("entregable_id", [None, 0, -3, "1", True])
def test_tarea_necesita_un_entregable_valido(entregable_id):
    assert isinstance(crear_tarea("Algo", "", entregable_id, None, "Alta"), Failure)


def test_prioridad_desconocida_es_invalida():
    resultado = crear_tarea("Algo", "", 1, None, "Urgentísima")
    assert isinstance(resultado, Failure)
    assert "'prioridad'" in resultado.error.mensaje
    assert "Urgentísima" in resultado.error.mensaje


def test_validar_tarea_revisa_una_tarea_ya_construida(tareas):
    mala = dataclasses.replace(tareas[0], nombre="")
    assert isinstance(validar_tarea(mala), Failure)
    assert validar_tarea(tareas[0]) == Success(tareas[0])


# ------------------------------------------------------------ actualización
def test_actualizar_tarea_devuelve_una_tarea_nueva_con_el_cambio(tareas):
    original = tareas[0]
    resultado = actualizar_tarea(original, nombre="Nuevo nombre", prioridad=Prioridad.BAJA)
    assert isinstance(resultado, Success)
    assert resultado.valor.nombre == "Nuevo nombre"
    assert resultado.valor.prioridad == Prioridad.BAJA
    assert resultado.valor.id == original.id  # lo demás se conserva


def test_actualizar_con_datos_invalidos_falla_y_no_toca_la_original(tareas):
    original = tareas[0]
    resultado = actualizar_tarea(original, nombre="")
    assert isinstance(resultado, Failure)
    assert original.nombre == "Levantar requisitos"


# ------------------------------------------------------------ inmutabilidad
def test_la_tarea_es_inmutable(tareas):
    with pytest.raises(dataclasses.FrozenInstanceError):
        tareas[0].estado = Estado.TERMINADA


def test_actualizar_no_modifica_el_objeto_original(tareas):
    original = tareas[0]
    copia_antes = dataclasses.replace(original)  # copia para comparar
    nueva = actualizar_tarea(original, nombre="Otro").valor
    assert original == copia_antes
    assert nueva is not original


# ------------------------------------------------------------ ausencia de valor
def test_buscar_tarea_existente(tareas):
    assert buscar_tarea(tareas, 2) == Some(tareas[1])


def test_buscar_tarea_inexistente_devuelve_nothing(tareas):
    assert buscar_tarea(tareas, 100) == Nothing()


def test_buscar_en_lista_vacia_devuelve_nothing():
    assert buscar_tarea((), 1) == Nothing()


def test_nombre_de_integrante_sin_responsable(integrantes):
    assert nombre_integrante(integrantes, 10) == "Ana"
    assert nombre_integrante(integrantes, None) == "Sin asignar"
    assert nombre_integrante(integrantes, 999) == "Sin asignar"


# ------------------------------------------------------------ referencias
def test_verificar_referencias_acepta_ids_existentes(tareas, entregables, integrantes):
    assert verificar_referencias(tareas[0], entregables, integrantes) == Success(tareas[0])


def test_verificar_referencias_acepta_tarea_sin_responsable(tareas, entregables, integrantes):
    assert isinstance(verificar_referencias(tareas[3], entregables, integrantes), Success)


def test_verificar_referencias_rechaza_entregable_inexistente(tareas, integrantes):
    resultado = verificar_referencias(tareas[0], (), integrantes)
    assert resultado.error.codigo == CodigoError.NO_EXISTE
    assert resultado.error.mensaje == "No existe el entregable."


def test_verificar_referencias_rechaza_responsable_inexistente(tareas, entregables):
    resultado = verificar_referencias(tareas[0], entregables, ())
    assert resultado.error.mensaje == "No existe el integrante."


# ------------------------------------------------------------ cálculos
def test_contar_pendientes(tareas):
    assert contar_pendientes(tareas) == 3  # la tarea 4 está terminada


def test_contar_pendientes_por_integrante(tareas):
    assert contar_pendientes_por_integrante(tareas) == {10: 2, 20: 1}


def test_contar_pendientes_con_lista_vacia():
    assert contar_pendientes_por_integrante(()) == {}


def test_porcentaje_terminado(tareas):
    assert porcentaje_terminado(tareas) == 25
    assert porcentaje_terminado(()) == 0


# ------------------------------------------------------------ otras entidades
def test_proyecto_valido_e_invalido():
    assert crear_proyecto(" Biblioteca ", "desc").valor.nombre == "Biblioteca"
    assert isinstance(crear_proyecto("", "desc"), Failure)


def test_integrante_duplicado_se_rechaza(integrantes):
    assert isinstance(crear_integrante("Luis", integrantes), Success)
    resultado = crear_integrante("ana", integrantes)  # mismo nombre sin importar mayúsculas
    assert isinstance(resultado, Failure)
    assert isinstance(crear_integrante("   ", integrantes), Failure)


def test_entregable_valido_e_invalido():
    assert crear_entregable("Diseño", "", 1).valor.proyecto_id == 1
    assert isinstance(crear_entregable("", "", 1), Failure)
    assert isinstance(crear_entregable("Diseño", "", None), Failure)


def test_construir_edt_agrupa_tareas_por_entregable_sin_modificar_nada(
    tareas, entregables
):
    arbol = construir_edt(entregables, tareas)
    assert [(e.nombre, [t.id for t in ts]) for e, ts in arbol] == [
        ("Análisis", [1, 2]),
        ("Desarrollo", [3, 4]),
    ]
    assert len(tareas) == 4  # la entrada no cambió


def test_resumen_del_proyecto(tareas, entregables, integrantes):
    resumen = resumir_proyecto(integrantes, entregables, tareas)
    assert (resumen.integrantes, resumen.entregables, resumen.tareas) == (2, 2, 4)
