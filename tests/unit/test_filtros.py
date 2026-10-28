"""Pruebas de filtros: función de orden superior, closures y lambdas."""

from app.core.filtros import (
    TODOS,
    acepta_todo,
    combinar_criterios,
    criterio_desde_textos,
    crear_filtro_por_entregable,
    crear_filtro_por_estado,
    crear_filtro_por_prioridad,
    crear_filtro_por_texto,
    crear_filtro_por_responsable,
    filtrar_tareas,
    ordenar_tareas,
)
from app.domain.models import Estado, Prioridad
from app.domain.result import Failure, Success


def ids(tareas):
    return [t.id for t in tareas]


# ------------------------------------------------------------ HOF
def test_filtrar_tareas_recibe_cualquier_funcion_como_criterio(tareas):
    assert ids(filtrar_tareas(tareas, lambda t: t.id > 2)) == [3, 4]
    assert ids(filtrar_tareas(tareas, lambda t: False)) == []
    assert ids(filtrar_tareas(tareas, acepta_todo)) == [1, 2, 3, 4]


def test_filtrar_devuelve_tupla_nueva_y_no_modifica_la_entrada(tareas):
    resultado = filtrar_tareas(tareas, lambda t: t.id == 1)
    assert isinstance(resultado, tuple)
    assert len(tareas) == 4


# ------------------------------------------------------------ filtros por campo
def test_filtrar_por_estado(tareas):
    assert ids(filtrar_tareas(tareas, crear_filtro_por_estado(Estado.PENDIENTE))) == [1]
    assert ids(filtrar_tareas(tareas, crear_filtro_por_estado(Estado.TERMINADA))) == [4]


def test_filtrar_por_responsable(tareas):
    assert ids(filtrar_tareas(tareas, crear_filtro_por_responsable(10))) == [1, 3]
    assert ids(filtrar_tareas(tareas, crear_filtro_por_responsable(20))) == [2]


def test_filtrar_por_prioridad(tareas):
    assert ids(filtrar_tareas(tareas, crear_filtro_por_prioridad(Prioridad.ALTA))) == [1, 4]


def test_filtrar_por_entregable(tareas):
    assert ids(filtrar_tareas(tareas, crear_filtro_por_entregable(2))) == [3, 4]


def test_filtro_sin_coincidencias_devuelve_tupla_vacia(tareas):
    assert filtrar_tareas(tareas, crear_filtro_por_responsable(999)) == ()


# ------------------------------------------------------------ closures
def test_el_filtro_generado_es_una_funcion_que_recuerda_su_criterio(tareas):
    filtro_ana = crear_filtro_por_responsable(10)
    filtro_carlos = crear_filtro_por_responsable(20)
    assert callable(filtro_ana)
    # Cada closure recuerda SU propio valor, sin interferir con la otra.
    assert [filtro_ana(t) for t in tareas] == [True, False, True, False]
    assert [filtro_carlos(t) for t in tareas] == [False, True, False, False]


def test_combinar_criterios_exige_cumplir_todos(tareas):
    criterio = combinar_criterios(
        crear_filtro_por_responsable(10), crear_filtro_por_prioridad(Prioridad.ALTA)
    )
    assert ids(filtrar_tareas(tareas, criterio)) == [1]


# ------------------------------------------------------------ filtros desde la interfaz
def test_criterio_desde_textos_con_todos_deja_pasar_todo(tareas):
    resultado = criterio_desde_textos(TODOS, TODOS, TODOS)
    assert isinstance(resultado, Success)
    assert ids(filtrar_tareas(tareas, resultado.valor)) == [1, 2, 3, 4]


def test_criterio_desde_textos_combina_los_tres_filtros(tareas):
    resultado = criterio_desde_textos("Pendiente", "10", "Alta")
    assert ids(filtrar_tareas(tareas, resultado.valor)) == [1]


def test_criterio_desde_textos_un_solo_filtro(tareas):
    resultado = criterio_desde_textos("En progreso", TODOS, TODOS)
    assert ids(filtrar_tareas(tareas, resultado.valor)) == [2]


def test_criterio_desde_textos_rechaza_valores_invalidos():
    assert isinstance(criterio_desde_textos("Archivada", TODOS, TODOS), Failure)
    assert isinstance(criterio_desde_textos(TODOS, "abc", TODOS), Failure)
    assert isinstance(criterio_desde_textos(TODOS, TODOS, "Urgente"), Failure)


# ------------------------------------------------------------ lambdas / ordenamiento
def test_ordenar_tareas_por_prioridad_y_luego_por_nombre(tareas):
    ordenadas = ordenar_tareas(tareas)
    # Altas primero (Levantar..., Realizar...), luego Media, luego Baja
    assert ids(ordenadas) == [1, 4, 2, 3]


def test_ordenar_no_modifica_la_entrada(tareas):
    antes = ids(tareas)
    ordenar_tareas(tareas)
    assert ids(tareas) == antes


def test_ordenar_lista_vacia():
    assert ordenar_tareas(()) == ()

# ------------------------------------------------------------ búsqueda por texto (closure)
def test_filtrar_por_texto_ignora_mayusculas_y_busca_en_el_nombre(tareas):
    assert ids(filtrar_tareas(tareas, crear_filtro_por_texto("INTERFAZ"))) == [3]
    assert ids(filtrar_tareas(tareas, crear_filtro_por_texto("  dise"))) == [2]


def test_filtrar_por_texto_sin_coincidencias_o_vacio(tareas):
    assert filtrar_tareas(tareas, crear_filtro_por_texto("zzz")) == ()
    assert ids(filtrar_tareas(tareas, crear_filtro_por_texto(""))) == [1, 2, 3, 4]


def test_criterio_desde_textos_combina_busqueda_con_los_selectores(tareas):
    resultado = criterio_desde_textos(TODOS, TODOS, "Alta", "pruebas")
    assert ids(filtrar_tareas(tareas, resultado.valor)) == [4]
    # Sin el cuarto argumento sigue funcionando igual que antes.
    assert ids(filtrar_tareas(tareas, criterio_desde_textos(TODOS, TODOS, "Alta").valor)) == [1, 4]
