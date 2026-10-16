# Guía para subir el proyecto a GitHub desde Visual Studio Code

La rúbrica evalúa (0,4) que el historial muestre **trabajo progresivo y participación de los
tres**. Por eso cada integrante sube, desde su propia cuenta y su propio computador, los archivos
que le corresponden, en el orden de esta guía. Cada uno debe poder explicar en la sustentación
lo que subió.

Todo se hace desde **Visual Studio Code (VS Code)**: no hace falta escribir comandos de git,
salvo dos líneas de configuración al principio.

---

## Parte A. Preparar el computador (cada uno, una sola vez)

### A1. Instalar Git

VS Code usa Git por debajo; si no está instalado, los botones de Git no funcionan.

1. Descargar Git para Windows en <https://git-scm.com/download/win> e instalarlo con todas las
   opciones por defecto (siguiente, siguiente…). Incluye el "Git Credential Manager", que es lo
   que después abre el navegador para iniciar sesión en GitHub.
2. Cerrar y volver a abrir VS Code.
3. Comprobar: menú **Terminal → New Terminal** (o `Ctrl + ñ` en teclado español) y escribir:

   ```
   git --version
   ```

   Debe responder algo como `git version 2.4x.x`. Si dice que no reconoce el comando, reiniciar
   el computador.

### A2. Decirle a Git quién es usted

En esa misma terminal de VS Code, con **su** nombre y **el correo de su cuenta de GitHub**
(si el correo no coincide, GitHub no le atribuye los commits y parece que no participó):

```
git config --global user.name "Stiven Gómez Henao"
git config --global user.email "correo-de-su-cuenta@gmail.com"
```

### A3. Instalar Python y las librerías (para poder correr el proyecto)

1. Instalar Python 3.10 o superior desde <https://www.python.org/downloads/> (no desde la
   Microsoft Store). En la primera pantalla del instalador, **marcar "Add python.exe to PATH"**
   antes de dar *Install Now*.
2. **Cerrar VS Code por completo y volver a abrirlo.** Una terminal que ya estaba abierta no ve
   los programas instalados después.
3. En la terminal de VS Code, comprobar:

   ```
   py --version
   ```

   Debe responder `Python 3.1x.x`. Si dice que `py` no se reconoce, ver la Parte F.
4. En VS Code, pestaña de extensiones (`Ctrl + Shift + X`), instalar la extensión **Python**
   de Microsoft.
5. Las librerías se instalan después de clonar el repositorio (paso B4).

> En Windows se usa **`py`** (el lanzador de Python que trae el instalador de python.org) en vez
> de `python` o `pip`: funciona aunque Python no haya quedado en el PATH.

---

## Parte B. Crear el repositorio y clonarlo

### B1. Stiven crea el repositorio en GitHub

1. En <https://github.com>, botón verde **New** (o el **+** arriba a la derecha → *New repository*).
2. *Repository name*: `genero-ritmo`. Visibilidad: **Public** (o *Private* y agregar después a
   la docente como colaboradora).
3. **No marcar** "Add a README file", ni .gitignore, ni licencia: ya los tenemos y si GitHub los
   crea habrá conflicto.
4. **Create repository**.
5. En el repositorio: **Settings → Collaborators → Add people** → escribir el usuario de GitHub
   de Manuel y de Juan José.

### B2. Manuel y Juan José aceptan la invitación

Les llega un correo de GitHub ("invited you to collaborate"). Hay que abrirlo y dar **Accept
invitation**. Sin esto no pueden subir nada (el push falla con un error de permisos).

### B3. Cada uno clona el repositorio en VS Code

"Clonar" es descargar el repositorio de GitHub a su computador, conectado para poder subir cambios.

1. Abrir VS Code **sin ninguna carpeta abierta** (*File → Close Folder* si hay una abierta).
2. `Ctrl + Shift + P` → escribir **Git: Clone** → Enter → elegir **Clone from GitHub**.
3. La primera vez, VS Code abre el navegador para iniciar sesión en GitHub: **Authorize** /
   **Continue** y volver a VS Code.
4. Aparece la lista de repositorios: elegir `<usuario-de-stiven>/genero-ritmo`.
5. Elegir dónde guardarlo (por ejemplo `Documentos`). Se crea la carpeta `Documentos\genero-ritmo`.
6. Cuando pregunte *"Would you like to open the cloned repository?"* → **Open**.
   Si pregunta si confía en los autores de la carpeta → **Yes, I trust the authors**.

> El repositorio está vacío al principio; VS Code puede mostrar un aviso de que se clonó un
> repositorio vacío. Es normal.

### B4. Instalar las librerías (cuando ya estén los archivos de Stiven)

La terminal tiene que estar **dentro de la carpeta del proyecto**: la línea debe empezar con
`PS C:\Users\<usuario>\Documents\genero-ritmo>` (o donde lo haya clonado), no con
`PS C:\Users\<usuario>>`. Si VS Code tiene abierta la carpeta `genero-ritmo` (*File → Open Folder*),
cada terminal nueva (*Terminal → New Terminal*) ya se abre ahí.

Después del turno 1 de la Parte D (antes no existe `requirements.txt`), en la terminal de
VS Code (que se abre en la carpeta del proyecto):

```
py -m pip install -r requirements.txt
```

No escriba solo `pip install ...`: en Windows `pip` casi nunca queda en el PATH y PowerShell
responde *"El término 'pip' no se reconoce como nombre de un cmdlet…"*. Con `py -m pip` se
ejecuta el pip del Python instalado, sin depender del PATH.

Tarda unos minutos (descarga NumPy, SciPy, Matplotlib, soundfile y sounddevice). Al final debe decir
`Successfully installed ...`.

---

## Parte C. Cómo se usa Git en VS Code (lo que cada uno repite en su turno)

Todo pasa en el panel **Control de código fuente** (Source Control): el ícono de las tres bolitas
unidas por líneas en la barra izquierda, o `Ctrl + Shift + G`.

### C1. Traer lo último (pull) — SIEMPRE antes de empezar

**Sí, el `git pull` se hace desde VS Code**, de cualquiera de estas formas (hacen lo mismo):

- Panel de Control de código fuente → menú **`···`** (arriba del panel) → **Pull**.
- `Ctrl + Shift + P` → escribir **Git: Pull** → Enter.
- Abajo a la izquierda, en la barra azul, junto al nombre de la rama (`main`), el ícono de
  **flechas en círculo** (sincronizar): baja lo nuevo y sube lo suyo.

Hágalo **cada vez** que vaya a trabajar: así tiene en su computador lo que subieron los otros
dos y se evitan conflictos.

### C2. Poner los archivos en la carpeta

Cada turno tiene su propio zip (`turno1_stiven.zip`, `turno2_manuel.zip`, …) con **solo** los
archivos de ese turno, ya dentro de sus carpetas (`src\`, `data\canciones\`, `docs\`).

1. **Abra la carpeta clonada en el Explorador de Windows.** La forma más fácil: en la terminal de
   VS Code escriba

   ```
   explorer .
   ```

   (con el punto) y Enter. Se abre la carpeta `genero-ritmo` que clonó. Al principio está vacía:
   la carpeta oculta `.git` es la que la conecta con GitHub; no la toque.
2. **Abra el zip de su turno** con doble clic (en Descargas, o donde lo guardó). Windows muestra
   lo que tiene adentro.
3. Dentro del zip: `Ctrl + A` (seleccionar todo) y `Ctrl + C` (copiar).
4. Vaya a la ventana de la carpeta `genero-ritmo` y `Ctrl + V` (pegar).

Si la carpeta `src` ya existe (desde el turno 2), Windows **combina** las carpetas: agrega los
archivos nuevos sin borrar los que ya estaban. Si pregunta por reemplazar un archivo con el mismo
nombre, algo está mal: cancele y pregunte.

Los archivos aparecen enseguida en el panel izquierdo de VS Code.

### C3. Elegir qué se sube (stage)

En el panel de Control de código fuente aparecen los archivos nuevos o cambiados, bajo **Changes**
(Cambios), con una **U** (nuevo) o una **M** (modificado) al lado.

- Pase el mouse sobre cada archivo que quiere subir y haga clic en el **`+`**.
  El archivo pasa a **Staged Changes** (cambios preparados).
- Solo lo que está en *Staged Changes* entra en el commit.

### C4. Hacer el commit

1. En la caja de texto de arriba del panel (*Message*), escriba el mensaje del commit
   (los mensajes sugeridos están en la Parte D).
2. Clic en el botón azul **Commit** (Confirmar), o `Ctrl + Enter`.

> **Ojo:** si no hay nada en *Staged Changes*, VS Code pregunta *"There are no staged changes to
> commit. Would you like to stage all your changes and commit them directly?"*. Responda
> **Cancel** y vuelva a C3: si dice *Yes* sube todo lo que haya en la carpeta.

### C5. Subir a GitHub (push)

Después del commit, el botón azul cambia a **Sync Changes ↑1** (Sincronizar cambios): clic.
Esto hace pull y push a la vez. Si pregunta si quiere hacerlo siempre → **OK**.

> **Solo la primera vez en el repositorio vacío** (Stiven, paso 1 de la Parte D), el botón dice
> **Publish Branch** en vez de *Sync Changes*: clic ahí.

### C6. Comprobar

Abra el repositorio en GitHub y recargue la página: deben aparecer los archivos, y en
**Commits** (arriba de la lista de archivos) el commit con su nombre.

---

## Parte D. Turnos: quién sube qué

Hagan los turnos **en orden** y, si se puede, **en días distintos**: la rúbrica premia el trabajo
progresivo, y un historial con todo subido en diez minutos no lo muestra. Cada uno, en su turno:
**C1 (pull) → C2 → C3 → C4 → C5 → C6**.

### Turno 1 — Stiven: estructura y carga de la señal

| Archivos a copiar | Mensaje del commit |
|---|---|
| `turno1_stiven.zip`: `.gitignore`, `requirements.txt`, `main.py`, `src/config.py`, `src/carga.py`, `data/canciones/LEEME.md`, `docs/GUIA_GITHUB.md` | `Estructura del repositorio, parámetros y carga de audio (mono, remuestreo a 22 050 Hz, fragmentos de 10 s)` |

En C3 debe ver los 7 archivos en *Changes*: déle `+` a todos. `.gitignore` es el que impide que
las canciones se suban; no lo deje por fuera. Al terminar este turno, los tres pueden hacer el paso B4.

### Turno 2 — Manuel: análisis rítmico (dos commits)

Zip: `turno2_manuel.zip`.

| Archivos | Mensaje |
|---|---|
| `src/ritmo.py` | `Envolvente de ataques por bandas (flujo espectral), autocorrelación, tempo y patrón de compás` |
| `src/caracteristicas.py` | `Vector de 52 características rítmicas por fragmento` |

Haga C3–C5 dos veces: primero solo `ritmo.py`, luego `caracteristicas.py`.

### Turno 3 — Juan José: ruido, ritmos sintéticos y figuras (dos commits)

Zip: `turno3_juanjose.zip`.

| Archivos | Mensaje |
|---|---|
| `src/ruido.py`, `src/sinteticos.py` | `Ruido blanco y rosa con SNR controlada; generador de ritmos sintéticos por género` |
| `src/graficas.py` | `Figuras: análisis rítmico, patrones de compás, matriz de confusión y PCA` |

### Turno 4 — Stiven: análisis de la Entrega 2

Zip: `turno4_stiven.zip`.

| Archivos | Mensaje |
|---|---|
| `src/analisis.py` | `Análisis de la señal: forma de onda, caracterización, FFT, aliasing, ruido y segmentación` |

### Turno 5 — Juan José: clasificador y comandos (dos commits)

Zip: `turno5_juanjose.zip`.

| Archivos | Mensaje |
|---|---|
| `src/clasificador.py` | `Clasificador k-NN con validación dejando una canción por fuera` |
| `src/cli.py`, `src/microfono.py` | `Comandos de terminal, menú y grabación por micrófono` |

Después de este turno el programa ya corre completo. Cada uno puede probarlo (Parte E).

### Turno 6 — Manuel: resultados y metodología

| Archivos | Mensaje |
|---|---|
| carpeta `results/` completa, `docs/metodologia.md` | `Resultados con las canciones reales y metodología detallada` |

En C3, en vez de dar `+` archivo por archivo, se puede dar `+` sobre la carpeta `results`.
Los archivos `.npz` no aparecen porque el `.gitignore` los excluye (son copias temporales).

### Turno 7 — Los tres: README (uno a la vez)

1. **Stiven** sube `README.md` → `README: descripción, estado, ejecución y resultados`.
2. **Manuel** hace pull, abre `README.md` en VS Code, completa la tabla de canciones
   (sección 3.1) y sube → `README: tabla de canciones (título y artista)`.
3. **Juan José** hace pull, completa o revisa la interpretación de la clasificación
   (sección 7.10) y sube → `README: interpretación de los resultados de clasificación`.

**Uno a la vez** y siempre con pull antes: si dos editan el README al mismo tiempo habrá conflicto.

### Turno 8 — Documentos de las entregas

Quien los tenga sube a `docs/` el documento de la Entrega 1 y el documento de avance en PDF →
`Documentos de la Entrega 1 y del avance`.

---

## Parte E. Correr el proyecto en VS Code

1. Copie sus canciones en `data/canciones/` (no se suben a GitHub; el `.gitignore` lo impide).
2. Terminal de VS Code, en la carpeta del proyecto:

   ```
   py main.py analizar --no-mostrar
   py main.py evaluar --no-mostrar
   ```

   Las figuras quedan en `results/` y se abren con doble clic desde el panel de archivos de VS Code.
3. Sin canciones se puede probar con los ritmos sintéticos:

   ```
   py main.py sinteticos
   py main.py evaluar --no-mostrar
   ```

En el README los comandos aparecen como `python main.py ...`; en Windows escríbalos con `py`.

---

## Parte F. Problemas comunes

| Qué pasa | Qué hacer |
|---|---|
| *"El término 'pip' no se reconoce…"* | Use `py -m pip install -r requirements.txt` (paso B4). |
| *"El término 'py' no se reconoce…"* | Python no está instalado, o se instaló con VS Code abierto. Cierre VS Code del todo, ábralo y pruebe otra vez `py --version`. Si sigue igual, instale Python desde python.org (paso A3) marcando *Add python.exe to PATH*, y vuelva a cerrar y abrir VS Code. |
| `python` abre la Microsoft Store o dice *"No se encontró Python"* | Es un acceso directo de Windows, no Python. Use `py` en lugar de `python`. Si `py` tampoco funciona, instale Python (paso A3). |
| *"No module named numpy"* (o scipy, matplotlib) al correr `py main.py` | Faltan las librerías: `py -m pip install -r requirements.txt`. |
| *"Could not open requirements file"* | La terminal no está en la carpeta del proyecto, o todavía no se ha hecho el turno 1. Abra la carpeta `genero-ritmo` en VS Code (*File → Open Folder*) y abra una terminal nueva. |
| El push dice *"rejected… fetch first"* o *"Updates were rejected"* | Otro subió algo antes que usted. Haga **Pull** (C1) y luego **Sync Changes** otra vez. |
| *"Permission denied"* o *"403"* al subir | No aceptó la invitación de colaborador (B2), o inició sesión en VS Code con otra cuenta. Revise abajo a la izquierda el ícono de cuentas (la persona) → cerrar sesión y volver a entrar. |
| Aparece un archivo con marcas `<<<<<<<` y `>>>>>>>` (conflicto) | Dos personas cambiaron las mismas líneas. VS Code muestra encima de cada conflicto: **Accept Current Change** (lo suyo), **Accept Incoming Change** (lo de GitHub) o **Accept Both Changes**. Elija, guarde (`Ctrl + S`), dé `+` al archivo, commit y Sync. Si no está seguro, pregunte antes de elegir. |
| Subió un archivo que no era | No lo borre en GitHub a mano. Avise al grupo: se corrige con otro commit que lo quita. |
| Las canciones aparecen en *Changes* | No les dé `+`. Revise que `.gitignore` esté en la raíz del repositorio y que contenga `data/canciones/*`. |
| Los commits no salen con su foto/nombre en GitHub | El correo de A2 no es el de su cuenta. Corríjalo con el mismo comando y, en GitHub, *Settings → Emails*, agregue ese correo. |

---

## Antes de entregar

- [ ] En GitHub, **Insights → Contributors** muestra a los tres.
- [ ] Las canciones **no** están en el repositorio (revisar la carpeta `data/canciones` en la web:
      solo debe estar `LEEME.md`).
- [ ] El README se ve bien en la página principal del repositorio y las imágenes de `results/` cargan.
- [ ] La docente tiene acceso (repositorio público, o agregada como colaboradora).
- [ ] Descripción de 5 líneas para la plataforma:

> Sistema que identifica el género musical (salsa, reggaetón, bachata, vallenato, cumbia, rock,
> electrónica, balada) a partir del ritmo. Implementado: carga y remuestreo a 22 050 Hz, forma de
> onda, caracterización, FFT, aliasing, ruido, segmentación en fragmentos de 10 s, envolvente de
> ataques por bandas, tempo por autocorrelación, patrón de compás y un primer clasificador k-NN.
> Pendiente: ampliar la base de canciones, resolver la ambigüedad de octava del tempo y validar con micrófono.
