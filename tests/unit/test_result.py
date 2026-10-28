"""Pruebas de Result (Success/Failure) y de ausencia de valor (Some/Nothing)."""

from app.domain.result import (
    CodigoError,
    Failure,
    Nothing,
    Some,
    Success,
    buscar_primero,
    combinar,
    de_opcion,
    dato_invalido,
    encadenar,
    mapear,
    no_existe,
    tuberia,
)


def test_success_guarda_el_valor():
    assert Success(5).valor == 5


def test_failure_guarda_el_error():
    fallo = dato_invalido("mal")
    assert isinstance(fallo, Failure)
    assert fallo.error.codigo == CodigoError.DATO_INVALIDO
    assert fallo.error.mensaje == "mal"


def test_mapear_transforma_un_success_y_respeta_un_failure():
    assert mapear(Success(2), lambda x: x * 10) == Success(20)
    fallo = dato_invalido("x")
    assert mapear(fallo, lambda x: x * 10) is fallo


def test_encadenar_se_detiene_en_el_primer_failure():
    llamadas = []

    def paso(valor):
        llamadas.append(valor)
        return Success(valor + 1)

    fallo = dato_invalido("falló antes")
    assert encadenar(fallo, paso) is fallo
    assert llamadas == []  # el siguiente paso NO se ejecutó
    assert encadenar(Success(1), paso) == Success(2)


def test_tuberia_ejecuta_los_pasos_en_orden():
    resultado = tuberia(Success(1), lambda x: Success(x + 1), lambda x: Success(x * 10))
    assert resultado == Success(20)


def test_combinar_junta_valores_o_devuelve_el_primer_fallo():
    assert combinar(Success(1), Success("a")) == Success((1, "a"))
    primero = dato_invalido("uno")
    assert combinar(Success(1), primero, dato_invalido("dos")) is primero


# ------------------------------------------------------------ ausencia de valor
def test_buscar_primero_encuentra_algo():
    assert buscar_primero([1, 2, 3], lambda n: n > 1) == Some(2)


def test_busqueda_sin_resultados_devuelve_nothing_y_no_un_objeto_vacio():
    resultado = buscar_primero([1, 2, 3], lambda n: n > 10)
    assert resultado == Nothing()
    assert not isinstance(resultado, Some)


def test_de_opcion_convierte_nothing_en_failure_no_existe():
    fallo = de_opcion(Nothing(), "la tarea")
    assert fallo.error.codigo == CodigoError.NO_EXISTE
    assert fallo.error.mensaje == "No existe la tarea."
    assert de_opcion(Some(7), "la tarea") == Success(7)


def test_no_existe_arma_el_mensaje():
    assert no_existe("el proyecto").error.mensaje == "No existe el proyecto."
