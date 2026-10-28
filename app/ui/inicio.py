"""IMPERATIVE SHELL - componente raíz y pantalla principal."""

from reactpy import component, html, use_state

from app import shell
from app.core.proyectos import resumir_proyecto
from app.domain.result import Failure, Nothing, Some, Success
from app.ui.comunes import (
    ESTILO_BOTON,
    ESTILO_CAJA,
    ESTILO_FILA,
    ESTILO_PAGINA,
    ESTILO_VACIO,
    boton,
    mostrar_resultado,
    vista_aviso,
)
from app.ui.edt import PantallaEDT
from app.ui.integrantes import PantallaIntegrantes
from app.ui.kanban import PantallaKanban
from app.ui.proyecto import PantallaProyecto, vista_proyecto

PANTALLAS = (
    ("proyecto", "Proyecto"),
    ("integrantes", "Integrantes"),
    ("edt", "EDT"),
    ("kanban", "KANBAN"),
)


@component
def Inicio(conexion):
    """Guarda el estado visual (qué pantalla, qué datos, qué aviso) y reparte a las pantallas."""
    # La carga completa (un Result) se guarda como estado y se recalcula con `refrescar`.
    carga, set_carga = use_state(lambda: shell.cargar_datos(conexion))
    pantalla, set_pantalla = use_state("inicio")
    aviso, set_aviso = use_state(None)

    match carga:
        case Success(valor=datos):
            error_carga = None
        case Failure(error=error):
            datos = shell.DATOS_VACIOS
            error_carga = ("error", shell.texto_error(error))

    def refrescar():
        set_carga(shell.cargar_datos(conexion))

    def avisar(tipo, texto):
        set_aviso((tipo, texto))

    def ir_a(nombre):
        def manejar(evento):
            set_pantalla(nombre)
            set_aviso(None)

        return manejar

    def cargar_demo(evento):
        mostrar_resultado(
            shell.cargar_datos_demo(conexion),
            avisar,
            lambda _: "Datos de prueba cargados. ¡Revisa el EDT y el Kanban!",
            lambda _: refrescar(),
        )

    match pantalla:
        case "proyecto":
            contenido = PantallaProyecto(conexion, datos, refrescar, avisar)
        case "integrantes":
            contenido = PantallaIntegrantes(conexion, datos, refrescar, avisar)
        case "edt":
            contenido = PantallaEDT(conexion, datos, refrescar, avisar)
        case "kanban":
            contenido = PantallaKanban(conexion, datos, refrescar, avisar)
        case _:
            contenido = vista_inicio(datos, ir_a, cargar_demo)

    volver = (
        html.div({"style": ESTILO_FILA}, boton("← Volver al inicio", ir_a("inicio")))
        if pantalla != "inicio"
        else html.div()
    )

    return html.div(
        {"style": ESTILO_PAGINA},
        html.h1("GESTOR DE PROYECTOS"),
        vista_aviso(error_carga),
        vista_aviso(aviso),
        volver,
        contenido,
    )


def vista_inicio(datos, ir_a, cargar_demo):
    """Pantalla principal: proyecto actual, totales y botones de navegación."""
    resumen = resumir_proyecto(datos.integrantes, datos.entregables, datos.tareas)

    match datos.proyecto:
        case Some():
            demo = html.div()
        case Nothing():
            demo = html.div(
                {"style": ESTILO_CAJA},
                html.p("¿Quieres probar la aplicación rápido?"),
                html.button({"on_click": cargar_demo, "style": ESTILO_BOTON},
                            "Cargar datos de prueba"),
            )

    return html.div(
        html.div({"style": ESTILO_CAJA}, vista_proyecto(datos.proyecto)),
        html.div(
            {"style": ESTILO_CAJA},
            html.p(f"Integrantes: {resumen.integrantes}"),
            html.p(f"Entregables: {resumen.entregables}"),
            html.p(f"Tareas: {resumen.tareas}"),
        ),
        html.div({"style": ESTILO_FILA}, *[boton(texto, ir_a(clave), clave) for clave, texto in PANTALLAS]),
        demo,
        html.p({"style": ESTILO_VACIO},
               "La EDT dice QUÉ trabajo hay que hacer; el Kanban dice EN QUÉ ESTADO está."),
    )
