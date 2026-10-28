"""IMPERATIVE SHELL - pantalla Integrantes (registrar y listar)."""

from reactpy import component, html, use_state

from app import shell
from app.core.tareas import contar_pendientes_por_integrante
from app.ui.comunes import ESTILO_CAJA, ESTILO_FILA, ESTILO_VACIO, boton, campo_texto, mostrar_resultado


@component
def PantallaIntegrantes(conexion, datos, refrescar, avisar):
    nombre, set_nombre = use_state("")

    def limpiar_formulario(_integrante):
        set_nombre("")
        refrescar()

    def guardar(evento):
        mostrar_resultado(
            shell.registrar_integrante(conexion, nombre),
            avisar,
            lambda i: f"Integrante '{i.nombre}' registrado.",
            limpiar_formulario,
        )

    # Cálculo puro del core: cuántas tareas sin terminar tiene cada integrante.
    pendientes = contar_pendientes_por_integrante(datos.tareas)

    if datos.integrantes:
        lista = html.ul(
            *[
                html.li({"key": i.id}, f"{i.nombre} — tareas pendientes: {pendientes.get(i.id, 0)}")
                for i in datos.integrantes
            ]
        )
    else:
        lista = html.p({"style": ESTILO_VACIO}, "Aún no hay integrantes registrados.")

    return html.div(
        html.h2("Integrantes"),
        html.div(
            {"style": ESTILO_CAJA},
            html.div({"style": ESTILO_FILA}, campo_texto("Nombre", nombre, set_nombre)),
            boton("Registrar integrante", guardar),
        ),
        html.div({"style": ESTILO_CAJA}, lista),
    )
