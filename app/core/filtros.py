"""FUNCTIONAL CORE - filtros y ordenamientos.

Aquí viven tres conceptos funcionales:

* FUNCIÓN DE ORDEN SUPERIOR: `filtrar_tareas(tareas, criterio)` recibe una función.
* CLOSURES: `crear_filtro_por_estado(...)` etc. devuelven una función que "recuerda"
  el valor con el que fueron creadas (estado, responsable, prioridad...).
* LAMBDAS: criterios pequeños de una sola expresión.
"""

from app.core.validaciones import convertir_a_entero, convertir_a_enum
from app.domain.models import PESO_PRIORIDAD, Estado, Prioridad
from app.domain.result import Success, combinar, mapear

TODOS = "Todos"


# --------------------------------------------------------------------------
# Función de orden superior
# --------------------------------------------------------------------------
def filtrar_tareas(tareas, criterio):
    """Devuelve las tareas para las que `criterio(tarea)` es verdadero.

    DEL CÓMO AL QUÉ: no escribimos un bucle con `if` y `append`; describimos
    el resultado ("las tareas que cumplen el criterio") y devolvemos una tupla nueva.
    """
    return tuple(t for t in tareas if criterio(t))


# --------------------------------------------------------------------------
# Closures: cada función externa captura un valor y devuelve el criterio
# --------------------------------------------------------------------------
def crear_filtro_por_estado(estado: Estado):
    return lambda tarea: tarea.estado == estado


def crear_filtro_por_responsable(responsable_id: int):
    return lambda tarea: tarea.responsable_id == responsable_id


def crear_filtro_por_prioridad(prioridad: Prioridad):
    return lambda tarea: tarea.prioridad == prioridad


def crear_filtro_por_entregable(entregable_id: int):
    return lambda tarea: tarea.entregable_id == entregable_id

def crear_filtro_por_texto(texto: str):
    """Closure: la tarea cumple si su nombre o descripción contiene `texto`.

    No distingue mayúsculas de minúsculas. Un texto vacío deja pasar todo.
    """
    buscado = texto.strip().lower()
    return lambda tarea: (
        buscado in tarea.nombre.lower() or buscado in tarea.descripcion.lower()
    )


def acepta_todo(tarea) -> bool:
    """Criterio "sin filtro": toda tarea pasa."""
    return True


def combinar_criterios(*criterios):
    """Devuelve un criterio nuevo que exige cumplir TODOS los criterios dados."""
    return lambda tarea: all(criterio(tarea) for criterio in criterios)


# --------------------------------------------------------------------------
# Filtros que llegan desde la interfaz como texto ("Todos", "En progreso", "3")
# --------------------------------------------------------------------------
def _criterio_opcional(texto, convertir, crear_filtro):
    """Si el texto es "Todos" no se filtra; si no, se convierte y se crea el filtro.

    `convertir` y `crear_filtro` son funciones recibidas como parámetros (HOF).
    """
    if texto in (None, "", TODOS):
        return Success(acepta_todo)
    return mapear(convertir(texto), crear_filtro)


def criterio_desde_textos(estado, responsable, prioridad, busqueda=""):
    """Construye UN criterio a partir de los tres selectores y la búsqueda por texto.

    Devuelve Success(criterio) o Failure si algún texto no es válido.
    """
    return mapear(
        combinar(
            _criterio_opcional(
                estado,
                lambda t: convertir_a_enum(Estado, t, "estado"),
                crear_filtro_por_estado,
            ),
            _criterio_opcional(
                responsable,
                lambda t: convertir_a_entero(t, "responsable"),
                crear_filtro_por_responsable,
            ),
            _criterio_opcional(
                prioridad,
                lambda t: convertir_a_enum(Prioridad, t, "prioridad"),
                crear_filtro_por_prioridad,
            ),
            Success(crear_filtro_por_texto(busqueda or "")),
        ),
        lambda criterios: combinar_criterios(*criterios),
    )


# --------------------------------------------------------------------------
# Ordenamiento
# --------------------------------------------------------------------------
def ordenar_tareas(tareas):
    """Primero las más urgentes; a igual prioridad, por nombre.

    Se usa una lambda como `key` porque es una expresión corta y de un solo uso.
    """
    return tuple(
        sorted(tareas, key=lambda t: (PESO_PRIORIDAD[t.prioridad], t.nombre.lower()))
    )
