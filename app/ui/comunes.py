"""IMPERATIVE SHELL - piezas de interfaz reutilizables (estilos y ayudas).

No contiene reglas de negocio. Solo arma elementos HTML con ReactPy.
"""

from reactpy import html

from app.domain.result import Failure, Success
from app.shell import texto_error

# ---------------------------------------------------------------- estilos
ESTILO_PAGINA = {"fontFamily": "Arial, sans-serif", "maxWidth": "1100px", "margin": "0 auto",
                 "padding": "16px"}
ESTILO_CAJA = {"border": "1px solid #ccc", "borderRadius": "8px", "padding": "12px",
               "marginBottom": "12px", "backgroundColor": "#fafafa"}
ESTILO_FILA = {"display": "flex", "gap": "8px", "flexWrap": "wrap", "alignItems": "flex-end",
               "marginBottom": "8px"}
ESTILO_ETIQUETA = {"display": "flex", "flexDirection": "column", "fontSize": "14px",
                   "minWidth": "160px"}
ESTILO_BOTON = {"padding": "6px 12px", "cursor": "pointer", "borderRadius": "4px",
                "border": "1px solid #555", "backgroundColor": "#fff"}
ESTILO_VACIO = {"color": "#666", "fontStyle": "italic"}

COLORES_AVISO = {"ok": ("#e6f4ea", "#1b7f3b"), "error": ("#fdecea", "#b3261e")}


def boton(texto, al_click, clave=None):
    propiedades = {"on_click": al_click, "style": ESTILO_BOTON}
    if clave is not None:
        propiedades["key"] = clave
    return html.button(propiedades, texto)


def campo_texto(etiqueta, valor, al_cambiar, multilinea=False):
    """Campo controlado: `al_cambiar` recibe el texto nuevo."""
    propiedades = {
        "value": valor,
        "on_change": lambda evento: al_cambiar(evento["target"]["value"]),
    }
    if multilinea:
        entrada = html.textarea(propiedades)
    else:
        entrada = html.input({**propiedades, "type": "text"})
    return html.label({"style": ESTILO_ETIQUETA}, etiqueta, entrada)


def selector(etiqueta, valor, opciones, al_cambiar):
    """`opciones` es una lista de (valor, texto_visible)."""
    return html.label(
        {"style": ESTILO_ETIQUETA},
        etiqueta,
        html.select(
            {"value": valor, "on_change": lambda evento: al_cambiar(evento["target"]["value"])},
            *[html.option({"value": v, "key": v}, texto) for v, texto in opciones],
        ),
    )


def vista_aviso(aviso):
    """`aviso` es None o una tupla (tipo, texto) con tipo "ok" o "error"."""
    if aviso is None:
        return html.div()
    tipo, texto = aviso
    fondo, borde = COLORES_AVISO[tipo]
    return html.div(
        {"style": {"backgroundColor": fondo, "border": f"1px solid {borde}", "color": borde,
                   "padding": "8px 12px", "borderRadius": "6px", "marginBottom": "12px"}},
        texto,
    )


def mostrar_resultado(resultado, avisar, mensaje_ok, al_exito):
    """Maneja un Result de la shell: si salió bien avisa y refresca; si falló muestra el error.

    PATTERN MATCHING sobre las dos variantes del resultado. Recibe funciones (HOF).
    """
    match resultado:
        case Success(valor):
            al_exito(valor)
            avisar("ok", mensaje_ok(valor))
        case Failure(error):
            avisar("error", texto_error(error))
