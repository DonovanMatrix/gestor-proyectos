"""IMPERATIVE SHELL - persistencia en SQLite.

Aquí están TODOS los efectos secundarios de base de datos. El Functional Core
no importa este archivo (ni `sqlite3`).

Convenciones:
* Toda función devuelve un Result: Success(valor) o Failure(error_persistencia / ...).
  Los errores de SQLite se convierten en Failure; no se propagan como excepciones.
* Las consultas por id devuelven Success(Some(x)) si existe y Success(Nothing()) si no:
  "la consulta funcionó" (Success) es distinto de "el dato no existe" (Nothing).
* Cada escritura corre dentro de una transacción: si falla, se hace rollback
  y no queda nada guardado a medias.
"""

import sqlite3
from dataclasses import replace

from app.adapters.decoradores import registrar_operacion
from app.domain.models import Entregable, Estado, Integrante, Prioridad, Proyecto, Tarea
from app.domain.result import (
    Nothing,
    Some,
    Success,
    dato_invalido,
    encadenar,
    error_persistencia,
    no_existe,
)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS proyectos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS integrantes (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS entregables (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    proyecto_id INTEGER NOT NULL REFERENCES proyectos(id)
);

CREATE TABLE IF NOT EXISTS tareas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT NOT NULL,
    descripcion    TEXT NOT NULL DEFAULT '',
    entregable_id  INTEGER NOT NULL REFERENCES entregables(id),
    responsable_id INTEGER REFERENCES integrantes(id),
    prioridad      TEXT NOT NULL CHECK (prioridad IN ('Alta', 'Media', 'Baja')),
    estado         TEXT NOT NULL CHECK (
        estado IN ('Pendiente', 'En progreso', 'En revisión', 'Terminada')
    )
);
"""


# --------------------------------------------------------------------------
# Conexión y ayudas internas
# --------------------------------------------------------------------------
def abrir_conexion(ruta: str = ":memory:") -> sqlite3.Connection:
    """Abre la base de datos. Para pruebas se usa ":memory:" (no toca el disco)."""
    conexion = sqlite3.connect(ruta, check_same_thread=False)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")  # SQLite no valida relaciones por defecto
    return conexion


def _en_transaccion(conexion, accion):
    """Ejecuta `accion(conexion)` dentro de una transacción y devuelve un Result.

    `with conexion:` hace COMMIT si todo sale bien y ROLLBACK si hay una excepción.
    """
    try:
        with conexion:
            return Success(accion(conexion))
    except sqlite3.IntegrityError:
        return dato_invalido(
            "No se pudo guardar: el dato está duplicado o hace referencia a algo que no existe."
        )
    except sqlite3.Error as error:
        return error_persistencia(f"No se pudo guardar en la base de datos: {error}")


def _leer(conexion, accion):
    """Ejecuta una consulta de solo lectura y devuelve un Result."""
    try:
        return Success(accion(conexion))
    except sqlite3.Error as error:
        return error_persistencia(f"No se pudo leer la base de datos: {error}")


def _a_proyecto(fila) -> Proyecto:
    return Proyecto(id=fila["id"], nombre=fila["nombre"], descripcion=fila["descripcion"])


def _a_integrante(fila) -> Integrante:
    return Integrante(id=fila["id"], nombre=fila["nombre"])


def _a_entregable(fila) -> Entregable:
    return Entregable(
        id=fila["id"],
        nombre=fila["nombre"],
        descripcion=fila["descripcion"],
        proyecto_id=fila["proyecto_id"],
    )


def _a_tarea(fila) -> Tarea:
    return Tarea(
        id=fila["id"],
        nombre=fila["nombre"],
        descripcion=fila["descripcion"],
        entregable_id=fila["entregable_id"],
        responsable_id=fila["responsable_id"],
        prioridad=Prioridad(fila["prioridad"]),
        estado=Estado(fila["estado"]),
    )


def _a_opcion(fila, convertir):
    return Nothing() if fila is None else Some(convertir(fila))


# --------------------------------------------------------------------------
# Esquema
# --------------------------------------------------------------------------
@registrar_operacion
def inicializar_esquema(conexion):
    """Crea las tablas si no existen. Es seguro llamarla varias veces."""
    try:
        conexion.executescript(ESQUEMA)
        return Success(None)
    except sqlite3.Error as error:
        return error_persistencia(f"No se pudo inicializar la base de datos: {error}")


# --------------------------------------------------------------------------
# Proyectos
# --------------------------------------------------------------------------
@registrar_operacion
def crear_proyecto(conexion, proyecto: Proyecto):
    def insertar(c):
        cursor = c.execute(
            "INSERT INTO proyectos (nombre, descripcion) VALUES (?, ?)",
            (proyecto.nombre, proyecto.descripcion),
        )
        return replace(proyecto, id=cursor.lastrowid)

    return _en_transaccion(conexion, insertar)


@registrar_operacion
def consultar_proyecto(conexion, proyecto_id: int):
    def consulta(c):
        fila = c.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
        return _a_opcion(fila, _a_proyecto)

    return _leer(conexion, consulta)


@registrar_operacion
def proyecto_actual(conexion):
    """El proyecto actual es el último que se creó."""

    def consulta(c):
        fila = c.execute("SELECT * FROM proyectos ORDER BY id DESC LIMIT 1").fetchone()
        return _a_opcion(fila, _a_proyecto)

    return _leer(conexion, consulta)


# --------------------------------------------------------------------------
# Integrantes
# --------------------------------------------------------------------------
@registrar_operacion
def crear_integrante(conexion, integrante: Integrante):
    def insertar(c):
        cursor = c.execute("INSERT INTO integrantes (nombre) VALUES (?)", (integrante.nombre,))
        return replace(integrante, id=cursor.lastrowid)

    return _en_transaccion(conexion, insertar)


@registrar_operacion
def listar_integrantes(conexion):
    def consulta(c):
        filas = c.execute("SELECT * FROM integrantes ORDER BY nombre COLLATE NOCASE").fetchall()
        return tuple(_a_integrante(f) for f in filas)

    return _leer(conexion, consulta)


# --------------------------------------------------------------------------
# Entregables
# --------------------------------------------------------------------------
@registrar_operacion
def crear_entregable(conexion, entregable: Entregable):
    def insertar(c):
        cursor = c.execute(
            "INSERT INTO entregables (nombre, descripcion, proyecto_id) VALUES (?, ?, ?)",
            (entregable.nombre, entregable.descripcion, entregable.proyecto_id),
        )
        return replace(entregable, id=cursor.lastrowid)

    return _en_transaccion(conexion, insertar)


@registrar_operacion
def listar_entregables(conexion, proyecto_id: int):
    def consulta(c):
        filas = c.execute(
            "SELECT * FROM entregables WHERE proyecto_id = ? ORDER BY id", (proyecto_id,)
        ).fetchall()
        return tuple(_a_entregable(f) for f in filas)

    return _leer(conexion, consulta)


# --------------------------------------------------------------------------
# Tareas
# --------------------------------------------------------------------------
@registrar_operacion
def crear_tarea(conexion, tarea: Tarea):
    def insertar(c):
        cursor = c.execute(
            "INSERT INTO tareas "
            "(nombre, descripcion, entregable_id, responsable_id, prioridad, estado) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                tarea.nombre,
                tarea.descripcion,
                tarea.entregable_id,
                tarea.responsable_id,
                tarea.prioridad.value,
                tarea.estado.value,
            ),
        )
        return replace(tarea, id=cursor.lastrowid)

    return _en_transaccion(conexion, insertar)


@registrar_operacion
def listar_tareas(conexion, proyecto_id: int):
    """Tareas de todos los entregables del proyecto."""

    def consulta(c):
        filas = c.execute(
            "SELECT t.* FROM tareas t "
            "JOIN entregables e ON e.id = t.entregable_id "
            "WHERE e.proyecto_id = ? ORDER BY t.id",
            (proyecto_id,),
        ).fetchall()
        return tuple(_a_tarea(f) for f in filas)

    return _leer(conexion, consulta)


@registrar_operacion
def actualizar_estado(conexion, tarea_id: int, nuevo_estado: Estado):
    """Guarda el nuevo estado. Si la tarea no existe devuelve Failure(NO_EXISTE)."""

    def actualizar(c):
        cursor = c.execute(
            "UPDATE tareas SET estado = ? WHERE id = ?", (nuevo_estado.value, tarea_id)
        )
        return cursor.rowcount  # cuántas filas cambió

    return encadenar(
        _en_transaccion(conexion, actualizar),
        lambda filas: Success(nuevo_estado) if filas else no_existe("la tarea"),
    )
