"""IMPERATIVE SHELL - pantalla EDT (Estructura de Desglose del Trabajo).

La EDT responde: ¿QUÉ trabajo hay que realizar?   Proyecto -> Entregable -> Tarea
"""

from reactpy import component, html, use_state

from app import shell
from app.core.entregables import construir_edt
from app.core.integrantes import nombre_integrante
from app.core.tareas import porcentaje_terminado
from app.domain.models import Prioridad
from app.domain.result import Nothing, Some
from app.ui.comunes import (
    ESTILO_CAJA,
    ESTILO_FILA,
    ESTILO_VACIO,
    boton,
    campo_texto,
    mostrar_resultado,
    selector,
)


def vista_edt(datos):
    """Dibuja el árbol usando `construir_edt` del core (que no modifica nada)."""
    match datos.proyecto:
        case Nothing():
            return html.p({"style": ESTILO_VACIO}, "Primero crea un proyecto.")
        case Some(valor=proyecto):
            pass

    arbol = construir_edt(datos.entregables, datos.tareas)
    if not arbol:
        return html.p({"style": ESTILO_VACIO}, "El proyecto aún no tiene entregables.")

    def vista_tarea(tarea):
        responsable = nombre_integrante(datos.integrantes, tarea.responsable_id)
        return html.li(
            {"key": tarea.id},
            f"{tarea.nombre} — {responsable} — prioridad {tarea.prioridad.value} "
            f"— estado: {tarea.estado.value}",
        )

    def vista_entregable(entregable, tareas):
        contenido = (
            html.ul(*[vista_tarea(t) for t in tareas])
            if tareas
            else html.p({"style": ESTILO_VACIO}, "Sin tareas todavía.")
        )
        return html.div(
            {"key": entregable.id, "style": ESTILO_CAJA},
            html.strong(f"{entregable.nombre} ({porcentaje_terminado(tareas)}% terminado)"),
            html.div(entregable.descripcion) if entregable.descripcion else html.div(),
            contenido,
        )

    return html.div(
        html.h3(f"Proyecto: {proyecto.nombre}"),
        *[vista_entregable(e, tareas) for e, tareas in arbol],
    )


@component
def PantallaEDT(conexion, datos, refrescar, avisar):
    nombre_entregable, set_nombre_entregable = use_state("")
    desc_entregable, set_desc_entregable = use_state("")
    nombre_tarea, set_nombre_tarea = use_state("")
    desc_tarea, set_desc_tarea = use_state("")
    entregable_sel, set_entregable_sel = use_state("")
    responsable_sel, set_responsable_sel = use_state("")
    prioridad_sel, set_prioridad_sel = use_state(Prioridad.MEDIA.value)

    def limpiar_entregable(_e):
        set_nombre_entregable("")
        set_desc_entregable("")
        refrescar()

    def guardar_entregable(evento):
        mostrar_resultado(
            shell.crear_entregable(conexion, nombre_entregable, desc_entregable),
            avisar,
            lambda e: f"Entregable '{e.nombre}' creado.",
            limpiar_entregable,
        )

    def limpiar_tarea(_t):
        set_nombre_tarea("")
        set_desc_tarea("")
        refrescar()

    def guardar_tarea(evento):
        # Si no se eligió entregable y solo hay uno, se usa ese (comodidad de la interfaz).
        entregable = entregable_sel or (
            str(datos.entregables[0].id) if len(datos.entregables) == 1 else ""
        )
        mostrar_resultado(
            shell.crear_tarea(
                conexion, nombre_tarea, desc_tarea, entregable, responsable_sel, prioridad_sel
            ),
            avisar,
            lambda t: f"Tarea '{t.nombre}' creada en estado '{t.estado.value}'.",
            limpiar_tarea,
        )

    opciones_entregables = [("", "— elige un entregable —")] + [
        (str(e.id), e.nombre) for e in datos.entregables
    ]
    opciones_responsables = [("", "Sin asignar")] + [
        (str(i.id), i.nombre) for i in datos.integrantes
    ]
    opciones_prioridad = [(p.value, p.value) for p in Prioridad]

    return html.div(
        html.h2("EDT — ¿Qué trabajo hay que realizar?"),
        html.div(
            {"style": ESTILO_CAJA},
            html.h3("Nuevo entregable"),
            html.div({"style": ESTILO_FILA},
                     campo_texto("Nombre", nombre_entregable, set_nombre_entregable),
                     campo_texto("Descripción", desc_entregable, set_desc_entregable)),
            boton("Crear entregable", guardar_entregable),
        ),
        html.div(
            {"style": ESTILO_CAJA},
            html.h3("Nueva tarea"),
            html.div({"style": ESTILO_FILA},
                     campo_texto("Nombre", nombre_tarea, set_nombre_tarea),
                     campo_texto("Descripción", desc_tarea, set_desc_tarea)),
            html.div({"style": ESTILO_FILA},
                     selector("Entregable", entregable_sel, opciones_entregables, set_entregable_sel),
                     selector("Responsable", responsable_sel, opciones_responsables, set_responsable_sel),
                     selector("Prioridad", prioridad_sel, opciones_prioridad, set_prioridad_sel)),
            boton("Crear tarea", guardar_tarea),
        ),
        vista_edt(datos),
    )
