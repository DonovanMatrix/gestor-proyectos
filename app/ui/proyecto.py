"""IMPERATIVE SHELL - pantalla Proyecto (crear y consultar)."""

from reactpy import component, html, use_state

from app import shell
from app.domain.result import Nothing, Some
from app.ui.comunes import ESTILO_CAJA, ESTILO_FILA, ESTILO_VACIO, boton, campo_texto, mostrar_resultado


def vista_proyecto(proyecto):
    """`proyecto` es Some(Proyecto) o Nothing(): se muestran los dos casos explícitamente."""
    match proyecto:
        case Some(valor=p):
            return html.div(html.h2(p.nombre), html.p(p.descripcion or "(sin descripción)"))
        case Nothing():
            return html.p({"style": ESTILO_VACIO},
                          "Todavía no hay un proyecto. Créalo en la pantalla Proyecto.")


@component
def PantallaProyecto(conexion, datos, refrescar, avisar):
    nombre, set_nombre = use_state("")
    descripcion, set_descripcion = use_state("")

    def limpiar_formulario(_proyecto):
        set_nombre("")
        set_descripcion("")
        refrescar()

    def guardar(evento):
        mostrar_resultado(
            shell.crear_proyecto(conexion, nombre, descripcion),
            avisar,
            lambda p: f"Proyecto '{p.nombre}' creado.",
            limpiar_formulario,
        )

    return html.div(
        html.h2("Proyecto actual"),
        html.div({"style": ESTILO_CAJA}, vista_proyecto(datos.proyecto)),
        html.h3("Crear proyecto"),
        html.p({"style": ESTILO_VACIO}, "El proyecto creado más recientemente pasa a ser el actual."),
        html.div(
            {"style": ESTILO_CAJA},
            html.div({"style": ESTILO_FILA}, campo_texto("Nombre", nombre, set_nombre)),
            html.div({"style": ESTILO_FILA},
                     campo_texto("Descripción", descripcion, set_descripcion, multilinea=True)),
            boton("Guardar proyecto", guardar),
        ),
    )
