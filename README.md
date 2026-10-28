# Gestor de Proyectos con EDT y Kanban

## Descripción

Aplicación web **local** para planificar y dar seguimiento a un proyecto.

* La **EDT** (Estructura de Desglose del Trabajo) responde: **¿qué trabajo hay que realizar?**
  Se organiza como `Proyecto → Entregable → Tarea`.
* El **Kanban** responde: **¿en qué estado está ese trabajo?**
  Cada tarea está en una columna: Pendiente, En progreso, En revisión o Terminada.

Permite crear un proyecto, registrar integrantes, crear entregables y tareas, asignar responsable y
prioridad, mover tareas por el tablero con transiciones válidas, filtrar por estado / responsable /
prioridad, y guardar todo en SQLite. Los errores, datos inválidos y listas vacías se comunican con
mensajes claros.

El objetivo académico es demostrar programación funcional: un **Functional Core** de reglas puras
y una **Imperative Shell** que se encarga de la interfaz y de los efectos externos.

## Tecnologías

Python 3.10 o superior (se usa `match/case`), ReactPy, FastAPI, SQLite (módulo `sqlite3`) y pytest.

FastAPI solo **sirve la aplicación ReactPy**. No hay API REST propia ni endpoints CRUD.

## Instalación

Desde la carpeta del proyecto:

```bash
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activarlo
#    Windows (PowerShell):   .venv\Scripts\Activate.ps1
#    Windows (cmd):          .venv\Scripts\activate.bat
#    Linux / macOS:          source .venv/bin/activate

# 3. Instalar las dependencias
pip install -r requirements.txt
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000> en el navegador. La base de datos `gestor_proyectos.db` se crea sola
en la carpeta desde la que ejecutas el comando (puedes cambiar la ruta con la variable de entorno
`GESTOR_DB`).

Para probar rápido, en la pantalla principal pulsa **Cargar datos de prueba** (proyecto
"Sistema de Biblioteca", 3 integrantes, 4 entregables y 4 tareas repartidas por el Kanban).

## Pruebas

```bash
pytest
```

Las pruebas **no necesitan** ReactPy ni FastAPI: prueban el core puro y el adaptador SQLite con una
base **en memoria** (`:memory:`), nunca con la base real.

## Arquitectura

```text
app/
  domain/      Modelos inmutables (models.py) y Result/Option (result.py)
  core/        FUNCTIONAL CORE: reglas puras
  adapters/    SQLite (database.py) y decorador (decoradores.py)
  shell.py     Casos de uso: coordinan core + SQLite
  ui/          Pantallas ReactPy
  main.py      Ensamble: FastAPI + ReactPy
tests/
  unit/        Pruebas del core (sin SQLite, ReactPy ni FastAPI)
  integration/ Pruebas de SQLite y de la shell
```

```text
Usuario → ReactPy (ui/) → Shell (shell.py) → Core (core/) → Success / Failure
                                      ↓
                      Shell guarda en SQLite o muestra el mensaje de error
```

| | FUNCTIONAL CORE (`app/core/`, `app/domain/`) | IMPERATIVE SHELL (`app/adapters/`, `app/shell.py`, `app/ui/`, `app/main.py`) |
|---|---|---|
| Qué hace | Reglas puras: validar, cambiar estado, filtrar, ordenar, calcular | Efectos externos: SQLite, ReactPy, FastAPI, logs |
| Misma entrada | Siempre la misma salida | Depende del entorno (base de datos, usuario) |
| Importa | Solo la biblioteca estándar y `app.domain` | `sqlite3`, `reactpy`, `fastapi`, `logging` |
| Errores | Devuelve `Failure`, no lanza excepciones | Convierte errores de SQLite en `Failure` y los muestra al usuario |

**Regla de oro:** el core nunca importa `sqlite3`, `reactpy`, `fastapi`, ni lee archivos ni imprime.

## EDT

Es el árbol del trabajo a realizar: el proyecto se descompone en **entregables** (paquetes de
trabajo) y cada entregable en **tareas**. La pantalla EDT crea y muestra esta estructura con el
porcentaje terminado de cada entregable. Se arma con `construir_edt` (core) sin modificar los datos.

## Kanban

Estados (en este orden): **Pendiente → En progreso → En revisión → Terminada**.

| Desde | Transiciones permitidas | Justificación |
|---|---|---|
| Pendiente | En progreso | Se empieza a trabajar |
| En progreso | En revisión, Pendiente | Avance normal / se pausa y vuelve a la cola |
| En revisión | Terminada, En progreso | Se aprueba / la revisión se rechaza y hay que corregir |
| Terminada | En progreso | Se reabre porque apareció un error |

Todo lo demás se rechaza (por ejemplo, `Pendiente → Terminada`: no puede saltarse la revisión).
Si la transición no es válida, el core devuelve un `Failure` con un mensaje y **la tarea original no
se modifica ni se guarda nada**. Los botones de cada tarjeta ofrecen *todos* los otros estados a
propósito, para poder demostrar el rechazo de transiciones inválidas.

## Programación funcional: evidencias

| Concepto | Archivo | Función | Evidencia |
|---|---|---|---|
| Del cómo al qué | `app/core/filtros.py` | `filtrar_tareas`, `ordenar_tareas` | Se describe el resultado ("las tareas que cumplen X", "ordenadas por Y") con expresiones generadoras y `sorted`, sin bucles con `append`. También `construir_edt` en `core/entregables.py` y `tuberia` en `domain/result.py`. |
| Pattern matching | `app/core/kanban.py` | `estados_siguientes`, `validar_transicion` | `match estado:` con un `case` por estado y `match (actual, nuevo):` sobre el par. También se usa `match` sobre `Success/Failure` y `Some/Nothing` (`ui/comunes.py`, `core/integrantes.py`). |
| Funciones de orden superior | `app/core/filtros.py` | `filtrar_tareas(tareas, criterio)` | Recibe una función como criterio; la usa el Kanban. También `mapear`, `encadenar`, `tuberia` (`domain/result.py`) y `_criterio_opcional`. |
| Lambdas | `app/core/filtros.py` | `ordenar_tareas`, `crear_filtro_por_*` | `key=lambda t: (PESO_PRIORIDAD[t.prioridad], t.nombre.lower())`. Se usan en expresiones cortas; las funciones con varias líneas llevan nombre. |
| Closures | `app/core/filtros.py` | `crear_filtro_por_estado`, `crear_filtro_por_responsable`, `crear_filtro_por_prioridad`, `crear_filtro_por_entregable` | La función devuelta recuerda el valor recibido (no hay estado mutable). Se usan en el Kanban y en `construir_edt`. Otra closure: `crear_manejador_mover` en `ui/kanban.py`. |
| Inmutabilidad | `app/domain/models.py`, `app/core/kanban.py` | `Tarea` (`frozen=True`), `cambiar_estado` | `replace(tarea, estado=nuevo)` crea una copia; la original no cambia. Probado en `tests/unit/test_kanban.py` y `test_tareas.py`. |
| Pureza | `app/core/` | `validar_tarea`, `cambiar_estado`, `filtrar_tareas`, `ordenar_tareas`, `contar_pendientes` | Sin imports de efectos. Misma entrada → misma salida. Se prueba sin SQLite ni ReactPy. |
| Efectos secundarios | `app/adapters/database.py`, `app/shell.py`, `app/ui/` | `crear_tarea` (SQLite), `cambiar_estado_tarea`, componentes ReactPy | Toda lectura/escritura de SQLite, logs y estado de pantalla están fuera del core. |
| Ausencia de valor | `app/domain/result.py`, `app/core/tareas.py` | `Some`, `Nothing`, `buscar_primero`, `buscar_tarea` | `buscar_tarea(tareas, 100)` devuelve `Nothing()`, nunca una tarea vacía. Igual `buscar_proyecto/integrante/entregable`. `de_opcion` lo convierte en "No existe la tarea.". |
| Manejo funcional de errores | `app/domain/result.py` | `Success`, `Failure`, `Error`, `CodigoError` | Las reglas de negocio devuelven `Success/Failure`, sin excepciones. La shell traduce cada error a un mensaje (`shell.texto_error`). |
| Decoradores | `app/adapters/decoradores.py` | `registrar_operacion` | Decora cada función de `database.py`: mide y registra el tiempo y avisa si devuelve `Failure`. No contiene reglas de negocio y devuelve el mismo resultado. |

Una explicación más detallada, con cómo presentarlo al profesor y preguntas de práctica, está en
[`docs/DEFENSA.md`](docs/DEFENSA.md).

## Decisiones técnicas

* **`Result` y `Option` son distintos.** `Success/Failure` = ¿salió bien la operación?
  `Some/Nothing` = ¿existe lo que se buscó? En SQLite, una consulta correcta que no encuentra nada
  es `Success(Nothing())`.
* **Archivos añadidos a la estructura sugerida:** `app/shell.py` (casos de uso, para que los
  callbacks de ReactPy no contengan reglas) y `app/core/validaciones.py` (validaciones compartidas).
  No se creó `ports/` porque no hacía falta.
* **Los closures devuelven un criterio** (`tarea → bool`) y se combinan con `filtrar_tareas`.
  El responsable se filtra por **id**, no por nombre, para evitar ambigüedades.
* **"Pendientes" por integrante** = tareas asignadas que todavía no están Terminadas.
* **Un solo proyecto activo:** el último creado es el "proyecto actual". La base admite varios.
* **Las tareas nuevas** empiezan en *Pendiente* y su `id` es `None` hasta que SQLite lo asigna.
* **Transacciones:** cada escritura va dentro de una transacción; si falla se hace rollback y no
  queda nada guardado a medias.

## Subir el proyecto a GitHub

El historial debe mostrar el aporte de **cada integrante**: cada persona debe hacer sus propios
commits con su nombre y correo.

```bash
git init
git add .
git commit -m "Proyecto inicial: gestor de proyectos con EDT y Kanban"
git branch -M main
git remote add origin https://github.com/USUARIO/NOMBRE-DEL-REPO.git
git push -u origin main
```

Antes, crea en GitHub un repositorio **vacío** (sin README ni .gitignore) y reemplaza la URL.
Cada integrante puede trabajar en una rama (`git checkout -b feature/mi-parte`) y abrir un Pull Request.
