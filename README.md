# Gestor de Proyectos con EDT y Kanban

Aplicación web local desarrollada en Python para organizar, planificar y dar seguimiento al trabajo de un proyecto mediante una **Estructura de Desglose del Trabajo (EDT)** y un tablero **Kanban**.

El proyecto aplica principios de programación funcional mediante una arquitectura que separa las reglas de negocio puras de los efectos externos, como la persistencia en SQLite y la interfaz de usuario.

## Tabla de contenidos

- [Características](#características)
- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación y ejecución](#instalación-y-ejecución)
- [Pruebas](#pruebas)
- [Arquitectura](#arquitectura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Estructura de Desglose del Trabajo (EDT)](#estructura-de-desglose-del-trabajo-edt)
- [Tablero Kanban](#tablero-kanban)
- [Programación funcional](#programación-funcional)
- [Decisiones técnicas](#decisiones-técnicas)
- [Colaboración y contribuciones](#colaboración-y-contribuciones)

## Características

La aplicación permite:

- Crear y gestionar un proyecto.
- Registrar integrantes y asignar responsables.
- Organizar el trabajo en entregables y tareas mediante la EDT.
- Visualizar las tareas en un tablero Kanban.
- Asignar prioridades y responsables a las tareas.
- Cambiar el estado de las tareas respetando las transiciones permitidas.
- Filtrar tareas por estado, responsable, prioridad y entregable.
- Consultar el porcentaje de finalización de los entregables.
- Persistir los datos utilizando SQLite.
- Mostrar mensajes claros cuando existen errores, datos inválidos o listas vacías.
- Cargar datos de prueba para explorar las funcionalidades de la aplicación.

## Tecnologías

| Tecnología | Propósito |
|---|---|
| Python 3.10 o superior | Lógica de negocio y aplicación |
| ReactPy | Interfaz web basada en componentes Python |
| FastAPI | Servir e integrar la aplicación ReactPy |
| SQLite | Persistencia de los datos |
| `pytest` | Ejecución de pruebas automatizadas |

**Nota:** FastAPI se utiliza para servir la interfaz ReactPy. El proyecto no implementa una API REST propia ni endpoints CRUD independientes.

## Requisitos previos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

- Python 3.10 o una versión superior.
- Git, si deseas clonar el repositorio.
- Una terminal como PowerShell en Windows.

Puedes verificar tu versión de Python con:

```bash
python --version
```

## Instalación y ejecución

### 1. Obtener el proyecto

Si todavía no tienes una copia local, clona el repositorio:

```bash
git clone https://github.com/DonovanMatrix/gestor-proyectos.git
cd gestor-proyectos
```

Si ya tienes el proyecto descargado, entra directamente en su carpeta.

### 2. Crear un entorno virtual

```bash
python -m venv .venv
```

### 3. Activar el entorno virtual

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**

```bat
.venv\Scripts\activate.bat
```

**Linux o macOS:**

```bash
source .venv/bin/activate
```

### 4. Instalar las dependencias

```bash
python -m pip install -r requirements.txt
```

### 5. Iniciar la aplicación

Desde la raíz del proyecto, ejecuta:

```bash
python -m uvicorn app.main:app --reload
```

Abre la siguiente dirección en tu navegador:

**http://127.0.0.1:8000**

La aplicación se ejecuta localmente. Para que otras personas puedan acceder desde sus propios dispositivos, es necesario configurar el acceso de red o desplegarla en un servidor.

### Datos de prueba

En la pantalla principal, utiliza el botón **Cargar datos de prueba** para explorar un escenario de ejemplo con un proyecto denominado *Sistema de Biblioteca*, tres integrantes, cuatro entregables y cuatro tareas.

### Base de datos

La aplicación utiliza SQLite para guardar la información. La base de datos `gestor_proyectos.db` se crea en la carpeta desde la que se ejecuta el comando, según la configuración descrita en el proyecto.

La ruta puede modificarse mediante la variable de entorno `GESTOR_DB`.

## Pruebas

Para ejecutar las pruebas automatizadas, utiliza:

```bash
pytest
```

Las pruebas están diseñadas para comprobar el comportamiento del core funcional y los componentes de persistencia sin depender de la interfaz web.

Las pruebas de SQLite utilizan una base de datos en memoria (`:memory:`), evitando operar sobre la base de datos real de la aplicación.

## Arquitectura

El proyecto sigue el enfoque **Functional Core / Imperative Shell**.

### Functional Core

Contiene las reglas de negocio y las transformaciones de datos. Sus funciones buscan ser puras e inmutables: reciben datos, calculan un resultado y no realizan operaciones externas.

Entre sus responsabilidades están:

- Validar datos y reglas de negocio.
- Filtrar y ordenar tareas.
- Construir la EDT.
- Comprobar las transiciones del Kanban.
- Calcular resultados y representar errores mediante tipos explícitos.

### Imperative Shell

Coordina las operaciones que interactúan con el entorno externo:

- Recibir las acciones de la interfaz.
- Coordinar los casos de uso.
- Leer y escribir datos en SQLite.
- Registrar operaciones y manejar errores de persistencia.
- Integrar ReactPy con FastAPI.

### Flujo general

```text
Usuario
   |
   v
Interfaz ReactPy (app/ui/)
   |
   v
Casos de uso (app/shell.py)
   |
   v
Reglas de negocio (app/core/)
   |
   v
Resultados: Success / Failure
   |
   v
Shell y adaptadores: persistencia y mensajes
```

La interfaz presenta los resultados al usuario, mientras que el core mantiene separadas las reglas de negocio de los efectos externos.

## Estructura del proyecto

```text
gestor-proyectos/
├── app/
│   ├── domain/       # Modelos, Result y Option
│   ├── core/         # Reglas de negocio puras
│   ├── adapters/     # Persistencia SQLite y decoradores
│   ├── ui/           # Interfaz ReactPy
│   ├── shell.py      # Casos de uso y coordinación
│   └── main.py       # Integración FastAPI + ReactPy
├── tests/
│   ├── unit/         # Pruebas unitarias del core
│   └── integration/  # Pruebas de persistencia y shell
├── docs/             # Documentación adicional
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Estructura de Desglose del Trabajo (EDT)

La EDT responde a la pregunta: **¿qué trabajo hay que realizar?**

Organiza el proyecto jerárquicamente:

```text
Proyecto
└── Entregables
    └── Tareas
```

Cada entregable agrupa tareas relacionadas. La pantalla EDT permite crear y visualizar esta estructura, así como consultar el porcentaje de tareas terminadas de cada entregable.

La estructura se construye mediante `construir_edt`, una función del core que transforma los datos sin modificarlos.

## Tablero Kanban

El tablero Kanban responde a la pregunta: **¿en qué estado se encuentra el trabajo?**

Las tareas pueden encontrarse en cuatro estados:

1. **Pendiente**
2. **En progreso**
3. **En revisión**
4. **Terminada**

### Transiciones permitidas

| Estado actual | Estados permitidos |
|---|---|
| Pendiente | En progreso |
| En progreso | En revisión, Pendiente |
| En revisión | Terminada, En progreso |
| Terminada | En progreso |

Estas reglas evitan saltos de estado no permitidos. Por ejemplo, una tarea pendiente no puede pasar directamente a terminada, ya que debe pasar por las etapas intermedias definidas.

Cuando una transición no es válida, el core devuelve un resultado `Failure`. La tarea original permanece sin modificaciones y no se guarda un cambio inválido en la base de datos.

## Programación funcional

Uno de los objetivos académicos del proyecto es demostrar conceptos de programación funcional aplicados a un sistema de gestión de proyectos.

| Concepto | Ubicación principal | Evidencia |
|---|---|---|
| Funciones de orden superior | `app/core/filtros.py` | `filtrar_tareas` recibe un criterio funcional. |
| Lambdas | `app/core/filtros.py` | Funciones anónimas para criterios de ordenamiento y filtrado. |
| Closures | `app/core/filtros.py` | Filtros que conservan valores recibidos al crearse. |
| Pattern matching | `app/core/kanban.py` | Uso de `match/case` para estados y transiciones. |
| Inmutabilidad | `app/domain/models.py` | Modelos inmutables y creación de copias con `replace`. |
| Pureza | `app/core/` | Reglas de negocio que evitan efectos externos. |
| Efectos secundarios | `app/adapters/`, `app/shell.py`, `app/ui/` | Persistencia, coordinación y operaciones de interfaz. |
| Ausencia de valor | `app/domain/result.py` | Tipos `Some` y `Nothing` para representar presencia o ausencia. |
| Manejo funcional de errores | `app/domain/result.py` | Tipos `Success` y `Failure`. |
| Decoradores | `app/adapters/decoradores.py` | `registrar_operacion` registra y mide operaciones. |
| Composición funcional | `app/domain/result.py` | Operaciones como `mapear`, `encadenar` y `tuberia`. |

### Regla de separación

El core no debe depender directamente de SQLite, ReactPy, FastAPI, la lectura de archivos ni la impresión en consola. Los efectos externos se gestionan desde la shell y los adaptadores.

Esta separación facilita probar las reglas de negocio de manera aislada y mantener una arquitectura más organizada.

Para profundizar en los conceptos, su defensa académica y las posibles preguntas de evaluación, consulta [`docs/DEFENSA.md`](docs/DEFENSA.md).

## Decisiones técnicas

- **Result y Option tienen propósitos distintos.** `Success` y `Failure` representan el resultado de una operación; `Some` y `Nothing` representan la presencia o ausencia de un valor.
- **La lógica se separa de la interfaz.** Los callbacks de ReactPy delegan las reglas de negocio a la shell y al core.
- **Las tareas se identifican mediante IDs.** El filtro por responsable utiliza el identificador para evitar ambigüedades entre personas con nombres similares.
- **Las tareas nuevas comienzan en estado Pendiente.** Su identificador se asigna cuando SQLite las guarda.
- **Las escrituras utilizan transacciones.** Si una operación falla, se realiza rollback para evitar que queden cambios parciales.
- **El proyecto mantiene un único proyecto activo en la interfaz.** La base de datos admite almacenar varios proyectos.

## Colaboración y contribuciones

El proyecto puede desarrollarse de forma colaborativa utilizando Git y GitHub. Cada integrante debe realizar sus propios cambios y registrarlos con su identidad de Git configurada correctamente.

### Flujo de trabajo recomendado

1. Actualizar la copia local:

   ```bash
   git pull origin main
   ```

2. Crear una rama para una tarea específica:

   ```bash
   git checkout -b feature/descripcion-del-cambio
   ```

3. Realizar y probar los cambios.

4. Revisar los archivos modificados:

   ```bash
   git status
   ```

5. Preparar y registrar la contribución:

   ```bash
   git add README.md
   git commit -m "Mejora la documentación del proyecto"
   ```

6. Subir la rama:

   ```bash
   git push -u origin feature/descripcion-del-cambio
   ```

7. Abrir un Pull Request en GitHub para revisar e integrar los cambios.

Si se trabaja directamente sobre `main`, es necesario tener los permisos correspondientes y coordinar los cambios con el resto del equipo.

Los mensajes de commit deben describir los cambios realizados realmente. La autoría de cada contribución debe corresponder a la persona que la efectuó.

---

**Proyecto académico:** Gestor de Proyectos con EDT y Kanban.

**Repositorio:** https://github.com/DonovanMatrix/gestor-proyectos
