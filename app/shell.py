"""IMPERATIVE SHELL - casos de uso.

Este módulo coordina el flujo:

    evento de la interfaz -> shell -> función pura del core -> resultado -> shell -> SQLite / interfaz

La shell lee los datos que hacen falta, le pide al CORE que decida (validar,
cambiar estado...) y, solo si el core devolvió Success, guarda en SQLite.
Si el core devuelve Failure, NO se guarda nada: el estado queda intacto.

Las pantallas (ReactPy) llaman a estas funciones y no contienen reglas de negocio.
"""

from dataclasses import dataclass

from app.adapters import database as db
from app.core.entregables import crear_entregable as core_crear_entregable
from app.core.integrantes import crear_integrante as core_crear_integrante
from app.core.kanban import cambiar_estado
from app.core.proyectos import crear_proyecto as core_crear_proyecto
from app.core.tareas import buscar_tarea, crear_tarea as core_crear_tarea, verificar_referencias
from app.core.validaciones import convertir_id_obligatorio, convertir_id_opcional
from app.domain.models import Estado
from app.domain.result import (
    CodigoError,
    Failure,
    Nothing,
    Some,
    Success,
    combinar,
    dato_invalido,
    de_opcion,
    encadenar,
    mapear,
    tuberia,
)


@dataclass(frozen=True)
class Datos:
    """Foto de todo lo que la interfaz necesita mostrar en un momento dado."""

    proyecto: object  # Some(Proyecto) o Nothing()
    integrantes: tuple
    entregables: tuple
    tareas: tuple


DATOS_VACIOS = Datos(proyecto=Nothing(), integrantes=(), entregables=(), tareas=())


# --------------------------------------------------------------------------
# Conversión de errores del core a mensajes para el usuario
# --------------------------------------------------------------------------
def texto_error(error) -> str:
    match error.codigo:
        case CodigoError.DATO_INVALIDO:
            return f"Dato inválido. {error.mensaje}"
        case CodigoError.NO_EXISTE:
            return f"No encontrado. {error.mensaje}"
        case CodigoError.TRANSICION_INVALIDA:
            return f"Movimiento no permitido. {error.mensaje}"
        case CodigoError.ERROR_PERSISTENCIA:
            return f"Problema con la base de datos. {error.mensaje}"
        case _:
            return error.mensaje


# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------
def cargar_datos(conexion):
    """Lee de SQLite todo lo necesario. Devuelve Success(Datos) o Failure."""

    def con_proyecto(proyecto):
        match proyecto:
            case Some(valor=p):
                entregables = db.listar_entregables(conexion, p.id)
                tareas = db.listar_tareas(conexion, p.id)
            case Nothing():
                # Sin proyecto todavía no hay entregables ni tareas.
                entregables = Success(())
                tareas = Success(())
        return mapear(
            combinar(db.listar_integrantes(conexion), entregables, tareas),
            lambda v: Datos(proyecto=proyecto, integrantes=v[0], entregables=v[1], tareas=v[2]),
        )

    return encadenar(db.proyecto_actual(conexion), con_proyecto)


# --------------------------------------------------------------------------
# Escritura: cada caso de uso = validar con el core + guardar con SQLite
# --------------------------------------------------------------------------
def crear_proyecto(conexion, nombre, descripcion):
    return encadenar(
        core_crear_proyecto(nombre, descripcion),
        lambda proyecto: db.crear_proyecto(conexion, proyecto),
    )


def registrar_integrante(conexion, nombre):
    return tuberia(
        db.listar_integrantes(conexion),
        lambda existentes: core_crear_integrante(nombre, existentes),
        lambda integrante: db.crear_integrante(conexion, integrante),
    )


def crear_entregable(conexion, nombre, descripcion):
    return tuberia(
        db.proyecto_actual(conexion),
        lambda opcion: de_opcion(opcion, "el proyecto (cree uno primero)"),
        lambda proyecto: core_crear_entregable(nombre, descripcion, proyecto.id),
        lambda entregable: db.crear_entregable(conexion, entregable),
    )


def crear_tarea(conexion, nombre, descripcion, entregable_texto, responsable_texto, prioridad):
    """Los ids llegan como texto desde los selectores de la interfaz."""

    def validar_y_guardar(valores):
        entregable_id, responsable_id, datos = valores
        return tuberia(
            core_crear_tarea(nombre, descripcion, entregable_id, responsable_id, prioridad),
            lambda tarea: verificar_referencias(tarea, datos.entregables, datos.integrantes),
            lambda tarea: db.crear_tarea(conexion, tarea),
        )

    return encadenar(
        combinar(
            convertir_id_obligatorio(entregable_texto, "entregable"),
            convertir_id_opcional(responsable_texto, "responsable"),
            cargar_datos(conexion),
        ),
        validar_y_guardar,
    )


def cambiar_estado_tarea(conexion, tarea_id, nuevo_estado):
    """Mueve una tarea en el Kanban respetando las transiciones válidas.

    1) Se leen las tareas.  2) Se busca la tarea (Some/Nothing).
    3) El CORE decide si el cambio es válido (Success/Failure).
    4) Solo si fue Success se guarda en SQLite.
    """

    def buscar(datos):
        return de_opcion(buscar_tarea(datos.tareas, tarea_id), "la tarea")

    def cambiar(tarea):
        return cambiar_estado(tarea, nuevo_estado)

    def guardar(tarea_nueva):
        return mapear(
            db.actualizar_estado(conexion, tarea_nueva.id, tarea_nueva.estado),
            lambda _: tarea_nueva,
        )

    return tuberia(cargar_datos(conexion), buscar, cambiar, guardar)


# --------------------------------------------------------------------------
# Datos de prueba (para demostrar el Kanban rápido)
# --------------------------------------------------------------------------
DEMO_INTEGRANTES = ("Ana", "Carlos", "María")
DEMO_ENTREGABLES = ("Análisis", "Diseño", "Desarrollo", "Pruebas")
# (nombre, entregable, responsable, prioridad, estados por los que se mueve)
DEMO_TAREAS = (
    ("Levantar requisitos", "Análisis", "Ana", "Alta",
     (Estado.EN_PROGRESO, Estado.EN_REVISION, Estado.TERMINADA)),
    ("Diseñar base de datos", "Diseño", "Carlos", "Alta", (Estado.EN_PROGRESO,)),
    ("Crear interfaz", "Desarrollo", "María", "Media", (Estado.EN_PROGRESO, Estado.EN_REVISION)),
    ("Realizar pruebas", "Pruebas", "Ana", "Baja", ()),
)


def cargar_datos_demo(conexion):
    """Crea un proyecto de ejemplo. Se niega si ya existe un proyecto."""
    match db.proyecto_actual(conexion):
        case Success(Some()):
            return dato_invalido(
                "Ya existe un proyecto; los datos de prueba solo se cargan en una base vacía."
            )
        case Failure() as fallo:
            return fallo

    pasos = [lambda: crear_proyecto(
        conexion, "Sistema de Biblioteca", "Gestión de préstamos y catálogo de libros.")]
    pasos += [lambda n=n: registrar_integrante(conexion, n) for n in DEMO_INTEGRANTES]
    pasos += [lambda n=n: crear_entregable(conexion, n, "") for n in DEMO_ENTREGABLES]

    for paso in pasos:
        resultado = paso()
        if isinstance(resultado, Failure):
            return resultado

    return _crear_tareas_demo(conexion)


def _crear_tareas_demo(conexion):
    match cargar_datos(conexion):
        case Failure() as fallo:
            return fallo
        case Success(datos):
            pass
    id_entregable = {e.nombre: e.id for e in datos.entregables}
    id_integrante = {i.nombre: i.id for i in datos.integrantes}

    for nombre, entregable, responsable, prioridad, movimientos in DEMO_TAREAS:
        creada = crear_tarea(
            conexion, nombre, "", str(id_entregable[entregable]),
            str(id_integrante[responsable]), prioridad,
        )
        if isinstance(creada, Failure):
            return creada
        for estado in movimientos:
            movida = cambiar_estado_tarea(conexion, creada.valor.id, estado)
            if isinstance(movida, Failure):
                return movida
    return Success(None)
