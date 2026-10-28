"""FUNCTIONAL CORE - validaciones reutilizables.

Todas son funciones PURAS: reciben un dato y devuelven Success(dato_limpio) o Failure.
Nunca lanzan excepciones ni tocan SQLite, archivos ni la interfaz.
"""

from enum import Enum

from app.domain.result import Success, dato_invalido


def validar_texto_obligatorio(valor, campo: str, maximo: int = 100):
    limpio = (valor or "").strip()
    if not limpio:
        return dato_invalido(f"El campo '{campo}' es obligatorio.")
    if len(limpio) > maximo:
        return dato_invalido(f"El campo '{campo}' no puede superar {maximo} caracteres.")
    return Success(limpio)


def validar_texto_opcional(valor, campo: str, maximo: int = 500):
    limpio = (valor or "").strip()
    if len(limpio) > maximo:
        return dato_invalido(f"El campo '{campo}' no puede superar {maximo} caracteres.")
    return Success(limpio)


def validar_id_obligatorio(valor, campo: str):
    # bool es subclase de int en Python; se excluye explícitamente.
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        return dato_invalido(f"Debe seleccionar un valor válido para '{campo}'.")
    return Success(valor)


def convertir_a_entero(texto, campo: str):
    """Convierte el texto de un selector (por ejemplo "3") a entero."""
    try:
        return Success(int(texto))
    except (TypeError, ValueError):
        return dato_invalido(f"Debe seleccionar un valor válido para '{campo}'.")


def convertir_id_obligatorio(texto, campo: str):
    return convertir_a_entero(texto, campo)


def convertir_id_opcional(texto, campo: str):
    """Texto vacío o None significa "sin valor" -> Success(None)."""
    if texto is None or str(texto).strip() == "":
        return Success(None)
    return convertir_a_entero(texto, campo)


def convertir_a_enum(tipo_enum: type[Enum], valor, campo: str):
    """Acepta un miembro del enum o su texto ("En progreso"). Si no existe -> Failure."""
    if isinstance(valor, tipo_enum):
        return Success(valor)
    for miembro in tipo_enum:
        if miembro.value == valor:
            return Success(miembro)
    opciones = ", ".join(m.value for m in tipo_enum)
    return dato_invalido(
        f"Valor desconocido para '{campo}': '{valor}'. Opciones válidas: {opciones}."
    )
