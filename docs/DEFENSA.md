# Guía para la defensa

Cómo explicar cada concepto y respuestas cortas a preguntas probables.
Recuerden: **cada integrante debe poder explicar el código que presenta.** Lean el archivo indicado
antes de la defensa; son funciones cortas.

## Dónde está cada cosa

| Concepto | Archivo | Función | Cómo explicarlo |
|---|---|---|---|
| Functional Core | `app/core/`, `app/domain/` | todo el paquete | "Aquí están las reglas. Son funciones puras: misma entrada, misma salida, sin base de datos ni pantalla." |
| Imperative Shell | `app/adapters/`, `app/shell.py`, `app/ui/`, `app/main.py` | — | "Todo lo que toca el mundo exterior: SQLite, ReactPy, FastAPI y logs." |
| Del cómo al qué | `app/core/filtros.py` | `filtrar_tareas` | "No recorro la lista con un bucle y `append`; digo *qué* quiero: las tareas que cumplen el criterio." |
| Pattern matching | `app/core/kanban.py` | `estados_siguientes`, `validar_transicion` | "Un `match` con un `case` por estado define las transiciones; otro `match` sobre el par (actual, nuevo) decide si se permite." |
| Función de orden superior | `app/core/filtros.py` | `filtrar_tareas(tareas, criterio)` | "Recibe una función. Cambiando el criterio, el mismo filtro sirve para estado, responsable o prioridad." |
| Lambda | `app/core/filtros.py` | `ordenar_tareas` | "La lambda de `key` expresa el orden en una línea: prioridad y luego nombre." |
| Closure | `app/core/filtros.py` | `crear_filtro_por_responsable(id)` | "Devuelve una función que *recuerda* el id con el que fue creada. No guarda estado mutable." |
| Inmutabilidad | `app/domain/models.py`, `app/core/kanban.py` | `Tarea(frozen=True)`, `cambiar_estado` | "No se modifica la tarea: `replace` crea una copia con el estado nuevo. Hay una prueba que lo demuestra." |
| Pureza | `app/core/*.py` | `validar_tarea`, `cambiar_estado`, ... | "No importan `sqlite3`, `reactpy` ni `fastapi`; se prueban sin levantar nada." |
| Efectos secundarios | `app/adapters/database.py` | `crear_tarea`, `actualizar_estado` | "Escribir en la base cambia el mundo exterior, por eso está fuera del core." |
| Ausencia de valor | `app/domain/result.py` | `Some`, `Nothing`, `buscar_tarea` | "Si no existe la tarea devuelve `Nothing()`, no una tarea vacía, y la shell lo convierte en 'No existe la tarea.'" |
| Errores funcionales | `app/domain/result.py` | `Success`, `Failure` | "Las reglas devuelven un resultado explícito en vez de lanzar excepciones." |
| Decorador | `app/adapters/decoradores.py` | `registrar_operacion` | "Envuelve las funciones de SQLite para medir tiempo y registrar fallos. No cambia el resultado ni contiene reglas." |

## Preguntas y respuestas

**1. ¿Dónde está el Functional Core?**
En `app/core/` (reglas) y `app/domain/` (modelos y `Result`). Son funciones puras sin efectos externos.

**2. ¿Qué es la Imperative Shell y dónde está?**
Es la capa que coordina lo externo: `app/ui/` (ReactPy), `app/adapters/` (SQLite), `app/shell.py` (casos de uso) y `app/main.py` (FastAPI).

**3. ¿Por qué SQLite no está en el core?**
Porque leer y escribir en la base produce efectos secundarios. Si estuviera en el core, las reglas dejarían de ser puras y no se podrían probar sin base de datos.

**4. ¿Cuál es el flujo cuando el usuario mueve una tarea?**
El botón (ReactPy) llama a `shell.cambiar_estado_tarea`. La shell lee las tareas, busca la tarea, el core decide con `cambiar_estado`, y solo si devuelve `Success` la shell guarda en SQLite y refresca la pantalla.

**5. ¿Qué diferencia hay entre la EDT y el Kanban?**
La EDT dice *qué* trabajo hay que hacer (proyecto → entregables → tareas). El Kanban dice *en qué estado* está cada tarea. El tablero no reemplaza la descomposición del proyecto.

**6. ¿Dónde usan pattern matching?**
En `core/kanban.py`: `estados_siguientes` hace `match` sobre el estado y `validar_transicion` sobre el par (actual, nuevo). También sobre `Success/Failure` y `Some/Nothing`.

**7. ¿Qué transiciones permiten y por qué?**
Pendiente→En progreso; En progreso→En revisión o Pendiente; En revisión→Terminada o En progreso; Terminada→En progreso. Se puede retroceder una etapa (pausar, rechazar revisión, reabrir), pero no saltarse la revisión.

**8. ¿Qué pasa si la transición es inválida?**
El core devuelve un `Failure` con un mensaje explicando qué se permite. La tarea original no se modifica y no se guarda nada en SQLite.

**9. ¿Dónde hay una función de orden superior?**
`filtrar_tareas(tareas, criterio)`: `criterio` es una función. Se usa en el Kanban y en `construir_edt`. También `encadenar` y `tuberia` en `result.py`.

**10. ¿Dónde está la closure?**
En `crear_filtro_por_responsable` (y las otras `crear_filtro_por_*`). La función externa recibe un valor y devuelve una función interna que lo recuerda.

**11. ¿Por qué esa closure no esconde estado mutable?**
Solo captura un valor que no cambia (un id, un estado o una prioridad). No modifica nada.

**12. ¿Cuándo usaron lambda y cuándo una función con nombre?**
Lambda en expresiones cortas de un solo uso (el `key` del ordenamiento, los criterios de filtro). Función con nombre cuando hay varios pasos o conviene darle un nombre, como `validar_transicion`.

**13. ¿Cómo demuestran la inmutabilidad?**
Los modelos son `@dataclass(frozen=True)`: asignar `tarea.estado = ...` lanza `FrozenInstanceError`. Y `cambiar_estado` usa `replace` para crear una copia. Hay pruebas en `test_tareas.py` y `test_kanban.py`.

**14. ¿Cómo se maneja un error sin excepciones?**
Con `Success(valor)` o `Failure(error)`. Los pasos se encadenan con `encadenar`/`tuberia`: si uno falla, los siguientes no se ejecutan y se propaga el `Failure`.

**15. ¿Qué diferencia hay entre `Failure` y `Nothing`?**
`Failure` es que la operación salió mal (dato inválido, transición no permitida). `Nothing` es que lo buscado no existe. Son preguntas distintas y por eso son tipos distintos.

**16. ¿Para qué sirve el decorador y por qué no oculta reglas de negocio?**
`@registrar_operacion` mide y registra cuánto tarda cada operación de SQLite y avisa si devuelve `Failure`. Solo observa: devuelve exactamente el mismo resultado. Es una preocupación transversal, no una regla del dominio.

**17. ¿Qué papel tiene FastAPI? ¿Hicieron una API REST?**
No hay API REST. FastAPI solo sirve y monta la aplicación ReactPy (`configure(app, Raiz)` en `main.py`).

**18. ¿Qué papel tiene ReactPy y dónde están las reglas?**
ReactPy dibuja la interfaz y recibe los eventos. Los callbacks solo llaman a la shell; las reglas (validar, transiciones, filtros) están en el core.

**19. ¿Cómo prueban sin ReactPy ni base real?**
`tests/unit/` prueba el core sin importar `sqlite3`, `reactpy` ni `fastapi`. `tests/integration/` usa SQLite en memoria (`:memory:`).

**20. ¿Qué garantiza que no queden datos a medias si algo falla?**
Cada escritura va en una transacción (`with conexion:`): si hay un error se hace rollback. Además, el core valida antes de que la shell guarde nada.
