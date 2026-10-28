"""IMPERATIVE SHELL - pantalla Kanban.

El Kanban responde: ¿EN QUÉ ESTADO está el trabajo?

Esta pantalla NO decide nada: filtra, ordena y agrupa con funciones del core,
y para mover una tarea llama a la shell, que le pregunta al core si el cambio es válido.
"""

from reactpy import component, html, use_state

from app import shell
from app.core.filtros import TODOS, criterio_desde_textos, filtrar_tareas, ordenar_tareas
from app.core.integrantes import nombre_integrante
from app.core.kanban import agrupar_por_estado
from app.domain.models import ESTADOS_KANBAN, Estado, Prioridad
from app.domain.result import Failure, Success
from app.ui.comunes import (
    ESTILO_BOTON,
    ESTILO_CAJA,
    ESTILO_FILA,
    ESTILO_VACIO,
    campo_texto,
    mostrar_resultado,
    selector,
)

ESTILO_COLUMNAS = {"display": "flex", "gap": "10px", "alignItems": "flex-start"}
ESTILO_COLUMNA = {"flex": "1", "minWidth": "0", "border": "1px solid #bbb", "borderRadius": "8px",
                  "padding": "8px", "backgroundColor": "#f3f6fb"}
ESTILO_TARJETA = {"border": "1px solid #999", "borderRadius": "6px", "padding": "8px",
                  "marginBottom": "8px", "backgroundColor": "#fff", "fontSize": "14px"}
ESTILO_BOTON_CHICO = {**ESTILO_BOTON, "padding": "2px 6px", "fontSize": "12px", "margin": "2px 2px 0 0"}


@component
def PantallaKanban(conexion, datos, refrescar, avisar):
    filtro_estado, set_filtro_estado = use_state(TODOS)
    filtro_responsable, set_filtro_responsable = use_state(TODOS)
    filtro_prioridad, set_filtro_prioridad = use_state(TODOS)
    busqueda, set_busqueda = use_state("")

    def crear_manejador_mover(tarea_id, estado):
        """Closure: recuerda qué tarea y a qué estado moverla cuando se haga clic."""

        def manejar(evento):
            mostrar_resultado(
                shell.cambiar_estado_tarea(conexion, tarea_id, estado),
                avisar,
                lambda t: f"'{t.nombre}' ahora está en '{t.estado.value}'.",
                lambda _t: refrescar(),
            )

        return manejar

    # 1) El CORE arma el criterio de filtrado a partir de los tres selectores y la búsqueda.
    match criterio_desde_textos(
        filtro_estado, filtro_responsable, filtro_prioridad, busqueda
    ):
        case Success(valor=criterio):
            visibles = ordenar_tareas(filtrar_tareas(datos.tareas, criterio))
            error_filtro = None
        case Failure(error=error):
            visibles = ()
            error_filtro = shell.texto_error(error)

    # 2) El CORE agrupa las tareas visibles por estado = columnas del tablero.
    columnas = agrupar_por_estado(visibles)

    def vista_tarjeta(tarea):
        otros_estados = [e for e in ESTADOS_KANBAN if e != tarea.estado]
        return html.div(
            {"key": tarea.id, "style": ESTILO_TARJETA},
            html.strong(tarea.nombre),
            html.div(f"Responsable: {nombre_integrante(datos.integrantes, tarea.responsable_id)}"),
            html.div(f"Prioridad: {tarea.prioridad.value}"),
            html.div(f"Estado: {tarea.estado.value}"),
            html.div(
                {"style": {"marginTop": "6px"}},
                *[
                    html.button(
                        {"key": e.value, "style": ESTILO_BOTON_CHICO,
                         "on_click": crear_manejador_mover(tarea.id, e)},
                        f"→ {e.value}",
                    )
                    for e in otros_estados
                ],
            ),
        )

    def vista_columna(estado):
        tareas = columnas[estado]
        contenido = (
            [vista_tarjeta(t) for t in tareas]
            if tareas
            else [html.div({"style": ESTILO_VACIO}, "Sin tareas")]
        )
        return html.div(
            {"key": estado.value, "style": ESTILO_COLUMNA},
            html.h3(f"{estado.value.upper()} ({len(tareas)})"),
            *contenido,
        )

    opciones_estado = [(TODOS, "Todos")] + [(e.value, e.value) for e in Estado]
    opciones_responsable = [(TODOS, "Todos")] + [(str(i.id), i.nombre) for i in datos.integrantes]
    opciones_prioridad = [(TODOS, "Todos")] + [(p.value, p.value) for p in Prioridad]

    if error_filtro is not None:
        mensaje = html.p({"style": ESTILO_VACIO}, error_filtro)
    elif not datos.tareas:
        mensaje = html.p({"style": ESTILO_VACIO},
                         "Aún no hay tareas. Créalas en la pantalla EDT.")
    elif not visibles:
        mensaje = html.p({"style": ESTILO_VACIO}, "Ninguna tarea coincide con los filtros elegidos.")
    else:
        mensaje = html.div()

    return html.div(
        html.h2("KANBAN — ¿En qué estado está el trabajo?"),
        html.div(
            {"style": {**ESTILO_CAJA, **ESTILO_FILA}},
            selector("Estado", filtro_estado, opciones_estado, set_filtro_estado),
            selector("Responsable", filtro_responsable, opciones_responsable, set_filtro_responsable),
            selector("Prioridad", filtro_prioridad, opciones_prioridad, set_filtro_prioridad),
            campo_texto("Buscar (nombre o descripción)", busqueda, set_busqueda),
        ),
        mensaje,
        html.div({"style": ESTILO_COLUMNAS}, *[vista_columna(e) for e in ESTADOS_KANBAN]),
    )
