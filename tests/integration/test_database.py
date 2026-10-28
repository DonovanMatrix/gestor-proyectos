"""Pruebas de integración del adaptador SQLite.

Usan una base EN MEMORIA (":memory:"): no tocan la base real del proyecto.
"""

import logging

import pytest

from app import shell
from app.adapters import database as db
from app.adapters.decoradores import registrar_operacion
from app.domain.models import Entregable, Estado, Integrante, Prioridad, Proyecto, Tarea
from app.domain.result import CodigoError, Failure, Nothing, Some, Success


@pytest.fixture
def conexion():
    conexion = db.abrir_conexion(":memory:")
    assert db.inicializar_esquema(conexion) == Success(None)
    yield conexion
    conexion.close()


@pytest.fixture
def proyecto(conexion):
    return db.crear_proyecto(conexion, Proyecto(None, "Biblioteca", "desc")).valor


@pytest.fixture
def entregable(conexion, proyecto):
    return db.crear_entregable(conexion, Entregable(None, "Análisis", "", proyecto.id)).valor


@pytest.fixture
def integrante(conexion):
    return db.crear_integrante(conexion, Integrante(None, "Ana")).valor


def nueva_tarea(entregable_id, responsable_id=None, nombre="Tarea"):
    return Tarea(None, nombre, "", entregable_id, responsable_id, Prioridad.ALTA, Estado.PENDIENTE)


# ------------------------------------------------------------ esquema
def test_se_crean_las_cuatro_tablas(conexion):
    tablas = {
        f["name"]
        for f in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"proyectos", "integrantes", "entregables", "tareas"} <= tablas


def test_inicializar_el_esquema_dos_veces_es_seguro(conexion):
    assert db.inicializar_esquema(conexion) == Success(None)


# ------------------------------------------------------------ proyecto
def test_insertar_y_consultar_proyecto(conexion):
    creado = db.crear_proyecto(conexion, Proyecto(None, "Biblioteca", "Préstamos")).valor
    assert creado.id == 1
    assert db.consultar_proyecto(conexion, creado.id) == Success(Some(creado))


def test_consultar_proyecto_inexistente_devuelve_nothing(conexion):
    assert db.consultar_proyecto(conexion, 99) == Success(Nothing())


def test_proyecto_actual_es_el_ultimo_creado(conexion):
    assert db.proyecto_actual(conexion) == Success(Nothing())
    db.crear_proyecto(conexion, Proyecto(None, "Uno", ""))
    segundo = db.crear_proyecto(conexion, Proyecto(None, "Dos", "")).valor
    assert db.proyecto_actual(conexion) == Success(Some(segundo))


# ------------------------------------------------------------ integrantes
def test_insertar_y_listar_integrantes(conexion):
    db.crear_integrante(conexion, Integrante(None, "Carlos"))
    db.crear_integrante(conexion, Integrante(None, "Ana"))
    nombres = [i.nombre for i in db.listar_integrantes(conexion).valor]
    assert nombres == ["Ana", "Carlos"]  # ordenados por nombre


def test_integrante_duplicado_devuelve_failure_y_no_se_guarda(conexion, integrante):
    resultado = db.crear_integrante(conexion, Integrante(None, "ANA"))
    assert isinstance(resultado, Failure)
    assert len(db.listar_integrantes(conexion).valor) == 1


# ------------------------------------------------------------ entregables
def test_insertar_y_listar_entregables(conexion, proyecto):
    db.crear_entregable(conexion, Entregable(None, "Análisis", "", proyecto.id))
    db.crear_entregable(conexion, Entregable(None, "Diseño", "", proyecto.id))
    nombres = [e.nombre for e in db.listar_entregables(conexion, proyecto.id).valor]
    assert nombres == ["Análisis", "Diseño"]


def test_entregable_de_proyecto_inexistente_falla(conexion):
    resultado = db.crear_entregable(conexion, Entregable(None, "Huérfano", "", 99))
    assert isinstance(resultado, Failure)  # la clave foránea lo impide


# ------------------------------------------------------------ tareas
def test_insertar_y_consultar_tareas(conexion, proyecto, entregable, integrante):
    creada = db.crear_tarea(conexion, nueva_tarea(entregable.id, integrante.id)).valor
    assert creada.id == 1
    tareas = db.listar_tareas(conexion, proyecto.id).valor
    assert tareas == (creada,)
    assert tareas[0].prioridad is Prioridad.ALTA and tareas[0].estado is Estado.PENDIENTE


def test_tarea_sin_responsable_se_guarda_con_none(conexion, proyecto, entregable):
    db.crear_tarea(conexion, nueva_tarea(entregable.id))
    assert db.listar_tareas(conexion, proyecto.id).valor[0].responsable_id is None


def test_tarea_con_entregable_inexistente_falla(conexion):
    assert isinstance(db.crear_tarea(conexion, nueva_tarea(99)), Failure)


def test_listar_tareas_solo_trae_las_del_proyecto(conexion, proyecto, entregable):
    otro = db.crear_proyecto(conexion, Proyecto(None, "Otro", "")).valor
    otro_entregable = db.crear_entregable(conexion, Entregable(None, "X", "", otro.id)).valor
    db.crear_tarea(conexion, nueva_tarea(entregable.id, nombre="De biblioteca"))
    db.crear_tarea(conexion, nueva_tarea(otro_entregable.id, nombre="De otro"))
    nombres = [t.nombre for t in db.listar_tareas(conexion, proyecto.id).valor]
    assert nombres == ["De biblioteca"]


def test_actualizar_estado_de_la_tarea(conexion, proyecto, entregable):
    tarea = db.crear_tarea(conexion, nueva_tarea(entregable.id)).valor
    assert db.actualizar_estado(conexion, tarea.id, Estado.EN_PROGRESO) == Success(Estado.EN_PROGRESO)
    guardada = db.listar_tareas(conexion, proyecto.id).valor[0]
    assert guardada.estado is Estado.EN_PROGRESO


def test_actualizar_estado_de_tarea_inexistente_devuelve_no_existe(conexion):
    resultado = db.actualizar_estado(conexion, 999, Estado.EN_PROGRESO)
    assert isinstance(resultado, Failure)
    assert resultado.error.codigo == CodigoError.NO_EXISTE


def test_una_escritura_fallida_no_deja_cambios_parciales(conexion, proyecto, entregable):
    """Si una transacción falla se hace rollback: no queda nada guardado a medias."""

    def insertar_y_fallar(c):
        c.execute("INSERT INTO integrantes (nombre) VALUES ('Fantasma')")
        c.execute("INSERT INTO integrantes (nombre) VALUES ('Fantasma')")  # duplicado -> error

    assert isinstance(db._en_transaccion(conexion, insertar_y_fallar), Failure)
    assert db.listar_integrantes(conexion).valor == ()  # ni siquiera el primero se guardó


# ------------------------------------------------------------ shell completa (core + SQLite)
def test_cambio_de_estado_valido_se_guarda(conexion):
    assert shell.cargar_datos_demo(conexion) == Success(None)
    datos = shell.cargar_datos(conexion).valor
    pendiente = next(t for t in datos.tareas if t.estado is Estado.PENDIENTE)
    resultado = shell.cambiar_estado_tarea(conexion, pendiente.id, Estado.EN_PROGRESO)
    assert resultado.valor.estado is Estado.EN_PROGRESO
    despues = shell.cargar_datos(conexion).valor
    assert next(t for t in despues.tareas if t.id == pendiente.id).estado is Estado.EN_PROGRESO


def test_transicion_invalida_no_cambia_lo_guardado(conexion):
    shell.cargar_datos_demo(conexion)
    antes = shell.cargar_datos(conexion).valor.tareas
    pendiente = next(t for t in antes if t.estado is Estado.PENDIENTE)
    resultado = shell.cambiar_estado_tarea(conexion, pendiente.id, Estado.TERMINADA)
    assert resultado.error.codigo == CodigoError.TRANSICION_INVALIDA
    assert shell.cargar_datos(conexion).valor.tareas == antes


def test_cambiar_estado_de_tarea_inexistente(conexion):
    shell.cargar_datos_demo(conexion)
    resultado = shell.cambiar_estado_tarea(conexion, 999, Estado.EN_PROGRESO)
    assert resultado.error.mensaje == "No existe la tarea."


def test_crear_tarea_por_la_shell_valida_antes_de_guardar(conexion):
    shell.cargar_datos_demo(conexion)
    cantidad = len(shell.cargar_datos(conexion).valor.tareas)
    assert isinstance(shell.crear_tarea(conexion, "", "", "1", "", "Alta"), Failure)
    assert isinstance(shell.crear_tarea(conexion, "X", "", "99", "", "Alta"), Failure)
    assert isinstance(shell.crear_tarea(conexion, "X", "", "1", "99", "Alta"), Failure)
    assert isinstance(shell.crear_tarea(conexion, "X", "", "", "", "Alta"), Failure)
    assert len(shell.cargar_datos(conexion).valor.tareas) == cantidad  # nada se guardó


def test_crear_entregable_sin_proyecto_falla(conexion):
    resultado = shell.crear_entregable(conexion, "Análisis", "")
    assert resultado.error.codigo == CodigoError.NO_EXISTE


def test_datos_de_prueba_no_se_cargan_dos_veces(conexion):
    shell.cargar_datos_demo(conexion)
    segunda = shell.cargar_datos_demo(conexion)
    assert isinstance(segunda, Failure)
    assert "Ya existe un proyecto" in segunda.error.mensaje
    assert len(shell.cargar_datos(conexion).valor.integrantes) == 3  # sin duplicar


def test_datos_de_prueba_muestran_el_kanban_repartido(conexion):
    shell.cargar_datos_demo(conexion)
    datos = shell.cargar_datos(conexion).valor
    assert len(datos.entregables) == 4 and len(datos.integrantes) == 3
    assert {t.estado for t in datos.tareas} == {
        Estado.PENDIENTE, Estado.EN_PROGRESO, Estado.EN_REVISION, Estado.TERMINADA,
    }


# ------------------------------------------------------------ decorador
def test_registrar_operacion_registra_y_no_cambia_el_resultado(caplog):
    @registrar_operacion
    def suma(a, b):
        """Suma dos números."""
        return Success(a + b)

    with caplog.at_level(logging.INFO, logger="gestor_proyectos"):
        assert suma(2, 3) == Success(5)
    assert "suma terminó en" in caplog.text
    assert suma.__name__ == "suma" and suma.__doc__ == "Suma dos números."


def test_registrar_operacion_avisa_cuando_hay_failure(caplog):
    @registrar_operacion
    def siempre_falla():
        return db.dato_invalido("algo salió mal")

    with caplog.at_level(logging.WARNING, logger="gestor_proyectos"):
        resultado = siempre_falla()
    assert isinstance(resultado, Failure)
    assert "algo salió mal" in caplog.text
