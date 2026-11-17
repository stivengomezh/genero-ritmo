# Reconocimiento de género musical por su ritmo

**Teoría de Señales** · Ingeniería de Sistemas y Telecomunicaciones · Universidad de Manizales

**Integrantes:** Manuel Leonardo Díaz Castaño · Stiven Gómez Henao · Juan José Arciniegas

---

## 1. Descripción

La señal que estudiamos es **audio musical**: una canción es una señal de presión acústica
x(t) que se graba, se muestrea y se guarda como una secuencia de números x[n].

El objetivo es un sistema que **identifique el género de una canción a partir de su ritmo**,
usando 10 s de audio. Se trabaja con ocho géneros y 64 canciones (8 por género): **salsa, reggaetón,
bachata, vallenato, cumbia, rock, electrónica y balada**.

El ritmo no se ve directamente en la forma de onda, porque está mezclado con la melodía y la
armonía. Lo que se repite son los **ataques**: los instantes en que empieza un golpe de bombo,
de caja, de güira o de campana. Por eso el sistema construye una señal nueva, la **envolvente
de ataques**, que vale mucho cuando empieza un golpe y casi cero en el resto, y estudia la
periodicidad de esa señal: con la autocorrelación obtiene el tempo, con la FFT su espectro
rítmico, y doblándola sobre una rejilla de 16 semicorcheas obtiene el **patrón del compás**
(el "dibujo" del ritmo: el dembow del reggaetón, el bombo en cada pulso de la electrónica, la
caja en 2 y 4 del rock, el contratiempo de la cumbia).

```
audio → mono, 22 050 Hz → fragmentos de 10 s → STFT → flujo espectral en 3 bandas (envolventes de ataques)
      → autocorrelación (tempo, subdivisión) + patrón de compás (16 pasos)
      + intensidad de los golpes (percusividad, fuerza, dinámica) → 57 características
      (en el entrenamiento, también con el tempo a la mitad y al doble) → k-NN → género
```

## 2. Estado actual

**Funciona y se puede reproducir:**

- Carga de MP3 o WAV de cualquier fs y número de canales, mezcla a mono, filtro antialiasing y
  remuestreo a 22 050 Hz, normalización y segmentación en fragmentos de 10 s.
- Análisis de la señal con las 64 canciones: forma de onda, caracterización, espectro (FFT),
  muestreo y aliasing, efecto del ruido y segmentación (`python main.py analizar`).
- Análisis rítmico: espectrograma, envolventes de ataques por banda, autocorrelación y tempo,
  espectro de la envolvente y patrón de compás.
- Clasificador por **k vecinos más cercanos**: **86 % de las canciones** (55 de 64) y 66 % de
  los fragmentos de 10 s bien clasificados en 8 géneros, con validación dejando una canción por
  fuera (azar: 12 %). Según el valor de k, entre 81 y 86 %.
- Al clasificar una canción que ya está en la base, se deja por fuera de su propio
  entrenamiento (si no, se reconocería a sí misma y el resultado no diría nada).
- Clasificación de un archivo o de una grabación con el micrófono, desde la terminal o desde
  una **página web** (`python main.py web`).
- Generador de ritmos sintéticos, para probar el código sin canciones.

**Cambios desde la Entrega 2:**

- La base pasó de 34 a **64 canciones: 8 por género**, con la **balada** como octavo género.
- 5 características nuevas de **intensidad de los golpes**: qué parte de la energía es percusiva
  (por bandas), qué tan fuertes son los ataques y el rango dinámico (7.10).
- **Tempo a la mitad y al doble:** cada fragmento de entrenamiento se guarda tres veces (con su
  tempo, con la mitad y con el doble). Resuelve buena parte de la ambigüedad de octava (7.6) y
  es el cambio que más mejoró el resultado: de 81 a 86 % por canción.
- Al clasificar una canción que ya está en la base, se deja por fuera de su entrenamiento.

**Falta para la entrega final:**

- **Vallenato y balada** siguen siendo los más difíciles (5 de 8 cada uno). El vallenato de la
  base es muy variado (paseo, merengue, vallenato romántico) y la balada casi no tiene percusión.
- Probar con grabaciones reales por micrófono (hasta ahora el ruido es simulado).
- Incorporar los temas que faltan del curso (diseño formal de filtros para separar las bandas,
  por ejemplo) y comparar el k-NN con otros clasificadores.

## 3. Datos y recursos

### 3.1 Canciones

| Archivo | Título | Artista |
|---|---|---|
| `salsa_01.mp3` | Periódico de Ayer | Héctor Lavoe |
| `salsa_02.mp3` | Vivir Mi Vida | Marc Anthony |
| `salsa_03.mp3` | Cali Pachanguero | Grupo Niche |
| `salsa_04.mp3` | La Cura | Frankie Ruiz |
| `salsa_05.mp3` | Pedro Navaja | Rubén Blades |
| `salsa_06.mp3` | La Rebelión | Joe Arroyo |
| `salsa_07.mp3` | La Vida Es un Carnaval | Celia Cruz |
| `salsa_08.mp3` | Oiga, Mire, Vea | Guayacán Orquesta |
| `reggaeton_01.mp3` | Gasolina | Daddy Yankee |
| `reggaeton_02.mp3` | Dale Don Dale | Don Omar |
| `reggaeton_03.mp3` | Mi Gente | J Balvin y Willy William |
| `reggaeton_04.mp3` | Tití Me Preguntó | Bad Bunny |
| `reggaeton_05.mp3` | Rakata | Wisin y Yandel |
| `reggaeton_06.mp3` | Pa' Que Retozen | Tego Calderón |
| `reggaeton_07.mp3` | Bichota | Karol G |
| `reggaeton_08.mp3` | El Perdón | Nicky Jam y Enrique Iglesias |
| `bachata_01.mp3` | Obsesión | Aventura |
| `bachata_02.mp3` | Propuesta Indecente | Romeo Santos |
| `bachata_03.mp3` | Corazón Sin Cara | Prince Royce |
| `bachata_04.mp3` | Princesa | Frank Reyes |
| `bachata_05.mp3` | Tengo un Amor | Toby Love |
| `bachata_06.mp3` | Burbujas de Amor | Juan Luis Guerra |
| `bachata_07.mp3` | Hoja en Blanco | Monchy y Alexandra |
| `bachata_08.mp3` | Dime Que Faltó | Zacarías Ferreira |
| `vallenato_01.mp3` | Los Caminos de la Vida | Los Diablitos |
| `vallenato_02.mp3` | La Gota Fría | Carlos Vives |
| `vallenato_03.mp3` | Olvídala | Binomio de Oro de América |
| `vallenato_04.mp3` | Las Locuras Mías | Silvestre Dangond |
| `vallenato_05.mp3` | Esta Vida | Jorge Celedón |
| `vallenato_06.mp3` | Tú Eres la Reina | Diomedes Díaz |
| `vallenato_07.mp3` | Vivo en el Limbo | Kaleth Morales |
| `vallenato_08.mp3` | Nunca Niegues Que Te Amo | Los Inquietos del Vallenato |
| `cumbia_01.mp3` | La Pollera Colorá | Wilson Choperena y Juan Bautista Madera |
| `cumbia_02.mp3` | Cómo Te Voy a Olvidar | Los Ángeles Azules |
| `cumbia_03.mp3` | Cumbia sobre el Río | Celso Piña |
| `cumbia_04.mp3` | El Pescador | Totó la Momposina |
| `cumbia_05.mp3` | Tabaco y Ron | Rodolfo Aicardi |
| `cumbia_06.mp3` | Se Me Perdió la Cadenita | La Sonora Dinamita |
| `cumbia_07.mp3` | La Pava Congona | Andrés Landero |
| `cumbia_08.mp3` | Colombia Tierra Querida | Lucho Bermúdez |
| `rock_01.mp3` | We Will Rock You | Queen |
| `rock_02.mp3` | Smells Like Teen Spirit | Nirvana |
| `rock_03.mp3` | Back in Black | AC/DC |
| `rock_04.mp3` | De Música Ligera | Soda Stereo |
| `rock_05.mp3` | Seven Nation Army | The White Stripes |
| `rock_06.mp3` | Sweet Child O' Mine | Guns N' Roses |
| `rock_07.mp3` | Smoke on the Water | Deep Purple |
| `rock_08.mp3` | Entre Dos Tierras | Héroes del Silencio |
| `electronica_01.mp3` | One More Time | Daft Punk |
| `electronica_02.mp3` | Titanium | David Guetta y Sia |
| `electronica_03.mp3` | Levels | Avicii |
| `electronica_04.mp3` | Summer | Calvin Harris |
| `electronica_05.mp3` | Don't You Worry Child | Swedish House Mafia |
| `electronica_06.mp3` | Animals | Martin Garrix |
| `electronica_07.mp3` | Clarity | Zedd |
| `electronica_08.mp3` | Heroes | Alesso |
| `balada_01.mp3` | Vivir Así Es Morir de Amor | Camilo Sesto |
| `balada_02.mp3` | El Triste | José José |
| `balada_03.mp3` | Me Va a Extrañar | Ricardo Montaner |
| `balada_04.mp3` | Amiga Mía | Alejandro Sanz |
| `balada_05.mp3` | La Soledad | Laura Pausini |
| `balada_06.mp3` | La Incondicional | Luis Miguel |
| `balada_07.mp3` | Amor Eterno | Rocío Dúrcal |
| `balada_08.mp3` | Te Amo | Franco de Vita |

- Las canciones tienen derechos de autor y **no se suben al repositorio** (`.gitignore`). La
  tabla dice cuáles son para que cualquiera pueda conseguirlas; las instrucciones para
  nombrarlas están en [`data/canciones/LEEME.md`](data/canciones/LEEME.md).
- El género de cada archivo se toma del inicio de su nombre (`salsa_01.mp3` → salsa).
- Son 64 canciones completas (de 2 a 7,4 minutos; 272 minutos en total), todas MP3 en estéreo:
  54 a 44,1 kHz y 10 a 48 kHz.
  El programa remuestrea todas a 22 050 Hz, así que la fs original no importa.

### 3.2 Ritmos sintéticos (control)

`python main.py sinteticos` genera 4 "canciones" de 30 s para cada uno de 8 géneros (44,1 kHz, WAV) en
`data/sinteticos/`. Cada una suma percusiones sintetizadas (bombo: senoide con barrido de 135 a
45 Hz; caja y güira: ruido filtrado pasabanda con caída exponencial; campana: dos ondas
cuadradas de 562 y 845 Hz; congas: senoides con caída), un bajo y acordes, sobre el patrón
típico de cada género, con variaciones aleatorias de tempo, ±4 ms de imprecisión, intensidad,
volumen por instrumento y notas omitidas. El tempo real de cada una queda en
`data/sinteticos/tempos_reales.csv`, lo que permite comprobar el estimador de tempo. Son un caso
de control (se sabe exactamente qué patrón tiene cada género), **no reemplazan a las canciones**.

### 3.3 Ruido

Se genera por código con parámetros documentados (`src/ruido.py`): ruido blanco gaussiano
(densidad espectral plana) y ruido rosa (densidad 1/f, parecido al ruido ambiente), escalados
para una SNR dada: **SNR = 10·log10(P_señal / P_ruido) dB**, con semilla fija (0).

## 4. Cómo ejecutar

**Software:** Python 3.10 o superior (probado con 3.13). Librerías: NumPy, SciPy, Matplotlib,
soundfile (lectura de WAV y MP3) y sounddevice (solo para el micrófono). Si soundfile no puede
leer un archivo, el programa intenta con librosa o con ffmpeg, si están instalados.

```bash
git clone <url-del-repositorio>
cd genero-ritmo
pip install -r requirements.txt     # en Windows: py -m pip install -r requirements.txt
# copiar las canciones en data/canciones/ (ver data/canciones/LEEME.md)

python main.py analizar          # forma de onda, caracterización, FFT, muestreo, ruido, segmentación → results/
python main.py evaluar           # clasificador k-NN con validación dejando una canción por fuera → results/
python main.py clasificar data/canciones/cumbia_02.mp3
python main.py ritmo data/canciones/reggaeton_01.mp3     # análisis rítmico de un archivo
python main.py grabar            # graba 10 s con el micrófono y predice el género
python main.py web               # abre la página web (Mini-Shazam) en el navegador
```

### Página web (Mini-Shazam)

![Página web](results/pagina_web.jpg)

`python main.py web` prepara la base de canciones y abre `http://127.0.0.1:8000` en el navegador.
En la página se puede **grabar con el micrófono** (10 a 30 s) o **subir un archivo** de audio
(también arrastrándolo), y se ve el género, los votos de cada género, el tempo, el género de
cada fragmento de 10 s y el patrón de compás.

- El análisis lo hace el mismo código del proyecto: la página solo envía el audio a
  `src/web.py` y dibuja la respuesta. No es una implementación aparte.
- No necesita instalar nada más: el servidor usa la biblioteca estándar de Python y la página
  es un solo archivo (`web/index.html`), sin conexión a internet.
- Solo atiende en `127.0.0.1`, es decir, en el computador donde se ejecuta. Para detenerla:
  `Ctrl + C` en la terminal. Si el puerto está ocupado: `python main.py web --puerto 8080`.
- La primera vez tarda varios minutos mientras calcula las características de las canciones
  (después quedan guardadas). Sin canciones en `data/canciones/` usa los ritmos sintéticos.
- El micrófono se captura sin cancelación de eco ni reducción de ruido del navegador: esos
  filtros están pensados para la voz y deforman la música.
- Si se sube una canción que ya está en la base (mismo nombre de archivo), se analiza sin usar
  sus propios fragmentos y la página lo avisa.

Sin canciones se puede probar todo con los ritmos sintéticos:

```bash
python main.py sinteticos        # genera data/sinteticos/
python main.py analizar          # si data/canciones/ está vacía, usa data/sinteticos/
python main.py evaluar
```

`python main.py` sin argumentos abre un menú. Con `--no-mostrar` las figuras se guardan en
`results/` sin abrir ventanas; con `--carpeta RUTA` se elige otra carpeta de canciones.

**Estructura:**

```
genero-ritmo/
├── main.py                 punto de entrada (llama a src/cli.py)
├── src/
│   ├── config.py           todos los parámetros: fs, STFT, bandas, tempo, segmentación, k
│   ├── carga.py            lectura, mono, remuestreo, normalización, fragmentos
│   ├── ritmo.py            espectrograma, envolventes de ataques, autocorrelación, tempo, patrón de compás
│   ├── caracteristicas.py  vector de 57 características rítmicas por fragmento
│   ├── clasificador.py     k-NN, validación, matriz de confusión
│   ├── analisis.py         análisis de la señal (Entrega 2)
│   ├── ruido.py            ruido blanco, rosa y filtro de micrófono
│   ├── sinteticos.py       generador de ritmos de prueba
│   ├── microfono.py        grabación
│   ├── web.py              servidor de la página web (biblioteca estándar)
│   ├── graficas.py         figuras
│   └── cli.py              comandos y menú
├── web/                    página web: index.html e imágenes (logo y campus)
├── data/                   canciones (no se suben), ritmos sintéticos (se generan)
├── results/                figuras y tablas generadas
├── docs/                   metodología y documentos de las entregas
└── requirements.txt
```

## 5. Conceptos de Teoría de Señales utilizados

| Concepto | Dónde se usa |
|---|---|
| Señal continua x(t) y discreta x[n] = x(n·Ts) | Lectura del archivo; figura 7.2 (c) |
| Muestreo: fs y Ts = 1/fs | Archivo: 44 100 Hz, Ts = 22,68 µs. Sistema: 22 050 Hz, Ts = 45,35 µs. Envolvente: 86,13 Hz, Ts = 11,6 ms |
| Teorema de Nyquist y aliasing | Justificación de fs (sección 6); filtro antialiasing antes de submuestrear (7.4) |
| Componente DC, energía, potencia, RMS, factor de cresta, saturación, dB | Caracterización (7.3); normalización |
| Transformada discreta de Fourier (FFT), resolución Δf = fs/N, método de Welch | Espectro de cada canción (7.4); espectro rítmico (7.5 d) |
| Ventana de Hann y fuga espectral | FFT, STFT y espectro rítmico |
| STFT, espectrograma, compromiso tiempo-frecuencia | Base de las envolventes (7.5) |
| Derivada discreta y rectificación de media onda | Flujo espectral: solo cuentan los aumentos de energía |
| Filtrado por bandas (pasabajos, pasabanda, pasaaltos) | Separación en graves, medios y agudos; media móvil para quitar la tendencia |
| Filtro de mediana (no lineal) | Separación de golpes y notas sostenidas en el espectrograma (percusividad, 7.10) |
| Periodicidad y **autocorrelación** | Tempo y subdivisión del pulso (7.5 c) |
| DFT de una secuencia periódica y propiedad de desplazamiento circular (\|X[k]\| no cambia si la secuencia se desplaza) | Forma del patrón de compás (7.7) |
| Ruido blanco y rosa, SNR | Degradación controlada (7.8) |
| Segmentación en tramas y fragmentos | STFT, ejemplos del clasificador (7.9) |
| Análisis de componentes principales (PCA) | Mapa de las características (7.10) |

La metodología completa, con todos los parámetros y las fórmulas, está en
[`docs/metodologia.md`](docs/metodologia.md).

## 6. Muestreo: valores y justificación

| | Archivo original | Sistema | Envolvente de ataques |
|---|---|---|---|
| fs | 44 100 Hz (típico de MP3) | **22 050 Hz** (44 100 / 2) | 22 050 / 256 = **86,13 Hz** |
| Ts = 1/fs | 22,68 µs | 45,35 µs | 11,61 ms |
| Nyquist fs/2 | 22 050 Hz | 11 025 Hz | 43 Hz |

**Por qué 22 050 Hz y no menos:** el ritmo lo marcan también los instrumentos agudos: hi-hat,
platillos, güira, guacharaca y maracas tienen su energía entre 3 y 10 kHz y son los que llevan
las subdivisiones (las semicorcheas de la güira en la bachata, el raspado continuo de la
guacharaca en el vallenato). Con 22 050 Hz el Nyquist queda en 11 025 Hz y la banda de agudos
(2–10 kHz) se conserva completa; con 11 025 Hz se perdería la mitad de esa banda. En las 64
canciones, por encima de 11 kHz queda en mediana el 0,3 % de la energía (2,3 % en el peor caso,
*Periódico de Ayer*), y bajar a la mitad reduce a la mitad el cálculo. Antes de bajar la tasa se
aplica un filtro pasabajos antialiasing (7.4).

**Por qué la envolvente puede ir a 86 Hz:** es una señal lenta. Un ritmo de 600 golpes por
minuto son 10 Hz, muy por debajo de su Nyquist de 43 Hz. La resolución temporal de 11,6 ms es
menor que la imprecisión normal de un músico (unos 10–20 ms).

## 7. Resultados actuales

Todos los resultados de esta sección se obtienen con las 64 canciones de la tabla 3.1 y se
regeneran con `python main.py analizar` y `python main.py evaluar` (unos 12 minutos la primera
vez; después las características quedan guardadas y `evaluar` tarda segundos).
Las figuras de detalle usan, de cada género, la canción con menos muestras saturadas (7.3).

### 7.1 Forma de onda x(t)

![Formas de onda](results/formas_de_onda.png)

Una canción por género, completa, con su valor RMS en ventanas de 100 ms (línea gris). Se ven la
amplitud, la duración y la estructura de cada canción:

- **Rock (*We Will Rock You*):** las ráfagas separadas por silencios cortos son el "pisotón,
  pisotón, palmada" que se repite en toda la canción: el ritmo se ve incluso a esta escala.
- **Electrónica y reggaetón:** subidas y caídas de intensidad (introducciones, cortes y
  "drops"), típicas de música producida para bailar.
- **Cumbia (*La Pollera Colorá*):** los últimos 25 s son casi silencio. Por eso el clasificador
  descarta los primeros y los últimos 15 s de cada canción (7.9).
- **Balada (*El Triste*):** el nivel más bajo de todas (−20,7 dBFS) y pausas cortas entre frases,
  sin golpes que se repitan: la voz y la orquesta llevan la canción, no la percusión.

En las demás, el ritmo apenas se intuye como una textura regular; para verlo hay que acercarse (7.2).

### 7.2 Ventanas a distintas escalas

![Ventanas temporales](results/ventana_temporal.png)

- **(a) 4 s de *Cali Pachanguero*:** los golpes son ráfagas de amplitud que se repiten. Los
  triángulos marcan los ataques detectados y las líneas punteadas el pulso estimado (100 BPM).
- **(b) La envolvente de ataques** de la misma ventana: una señal mucho más simple, con un pico
  por golpe. Es la señal cuyo periodo se mide.
- **(c) 3 ms:** cada punto es una muestra. A 44 100 Hz hay una cada 22,7 µs; a 22 050 Hz, una cada
  45,4 µs. Las muestras a 22 050 Hz siguen la forma de la señal porque casi no hay contenido por
  encima de 11 kHz.

### 7.3 Caracterización

Tabla completa en [`results/caracterizacion.md`](results/caracterizacion.md): duración, fs,
canales, número de muestras, mínimo, máximo, media, RMS, factor de cresta, muestras saturadas,
energía por banda, tempo y claridad del pulso de cada canción. Promedios por género
(`results/resumen_generos.csv`):

| Género | Tempo medido (BPM) | RMS (dBFS) | Cresta (dB) | Graves / medios / agudos | Claridad R[P] |
|---|---|---|---|---|---|
| Salsa | 90–105 | −12,6 | 13,0 | 30 / 55 / 13 % | 0,52 |
| Reggaetón | 82–111 | −11,8 | 13,2 | 56 / 37 / 6 % | 0,54 |
| Bachata | 120–135 | −15,1 | 15,2 | 36 / 54 / 9 % | 0,54 |
| Vallenato | 77–136 | −15,2 | 14,5 | 33 / 56 / 10 % | 0,49 |
| Cumbia | 83–103 | −15,8 | 15,1 | 46 / 41 / 12 % | 0,55 |
| Rock | 81–126 | −15,4 | 14,2 | 44 / 43 / 13 % | 0,43 |
| Electrónica | 123–129 | −13,1 | 13,8 | 48 / 40 / 10 % | 0,57 |
| Balada | 67–132 | −17,9 | 15,8 | 28 / 60 / 12 % | **0,31** |

- **Media ≈ 0** en todas (|media| < 0,015): no hay componente DC apreciable; igual se resta al
  normalizar.
- **Saturación:** *Periódico de Ayer* tiene el 1,8 % de las muestras en ±1 (recortadas), un RMS
  de −7,2 dBFS y un factor de cresta de solo 8,8 dB: es una remasterización muy comprimida. Su
  correlación entre canal izquierdo y derecho es 0,99, prácticamente mono (es una grabación de
  los años 70). Las demás canciones tienen 0,2 % o menos de muestras saturadas.
- **Energía por banda:** el reggaetón concentra la mayor parte en los graves (56 %, el bajo
  electrónico); la salsa y la balada en los medios (55 y 60 %: voz, piano, metales). Los agudos tienen
  poca energía en todos los géneros (6–13 %), aunque llevan muchos de los ataques.
- La **claridad del pulso** R[P] (autocorrelación de la envolvente en el periodo del pulso, de 0
  a 1) es parecida en los géneros bailables (0,43–0,57) y mucho más baja en la **balada (0,31)**:
  sin batería marcada, la envolvente de ataques casi no se repite de un pulso al siguiente.

### 7.4 Espectro (FFT) y aliasing

![Espectros](results/espectros_fft.png)

**Qué se calcula:** la densidad espectral de potencia de toda la canción por el **método de
Welch**: la señal se divide en bloques de 65 536 muestras (1,49 s) con 50 % de solapamiento, a
cada bloque se le aplica la ventana de Hann y la FFT, X_m[k] = Σ x[n + mH]·w[n]·e^(−j2πkn/N), y se
promedian los |X_m[k]|². La resolución es Δf = fs/N = 44 100 / 65 536 = 0,67 Hz; para poder leer
la curva, la potencia se promedia en bandas de 1/6 de octava. Se usa Welch en vez de una sola FFT
de toda la canción porque promediar reduce la varianza del estimador, y porque una FFT de 20
millones de muestras ocupa varios GB de memoria. **Eje x:** frecuencia en Hz en escala
logarítmica, de 20 Hz a fs/2 = 22 050 Hz. **Eje y:** potencia en dB respecto a la banda más fuerte.
Las franjas de color son las tres bandas que usa el sistema; la zona gris, lo que se descarta al
bajar a 22 050 Hz. La mayoría de las curvas caen bruscamente entre 15 y 20 kHz: es el filtro
pasabajos que aplica la compresión MP3.

![Aliasing](results/muestreo_aliasing.png)

Para mostrar el aliasing se usa la canción con más energía por encima de 11 kHz (*Periódico de
Ayer*). Si se baja de 44 100 a 22 050 Hz tomando una de cada dos muestras, sin filtro, el
contenido entre 11 y 16 kHz se refleja dentro de la banda útil en f' = 22 050 − f: en (b) la
curva punteada gris (el original reflejado) coincide con los picos de la curva sin filtro. Aparece
**energía falsa entre 8 y 11 kHz (+4,7 dB)**, justo en la banda de los platillos y la güira. Con
el filtro antialiasing esto no ocurre.

### 7.5 Análisis rítmico de un fragmento

![Análisis rítmico](results/analisis_ritmico.png)

- **(a) Espectrograma:** los golpes de percusión son líneas verticales, porque un golpe tiene
  energía en muchas frecuencias a la vez; las notas sostenidas son líneas horizontales.
- **(b) Envolventes de ataques:** flujo espectral e_b[m] = Σ_k máx(0, L[k,m] − L[k,m−1]) con
  L = log(1 + 100·|X|), en cada banda. Graves = bombo y bajo; medios = caja, congas, campana;
  agudos = güira, platillos, maracas.
- **(c) Autocorrelación:** los picos están en múltiplos del periodo del pulso P. El tempo es
  60/P (en BPM). Se refina con interpolación parabólica para no depender de la resolución de
  11,6 ms. Aquí P = 603 ms → 99,6 BPM.
- **(d) Espectro de la envolvente:** la FFT de e[m] muestra el pulso y sus múltiplos. En la salsa
  el pico más alto está en ×4 (~400 golpes por minuto): las corcheas de la campana y las congas.

Hay una figura por género en `results/analisis_ritmico_<genero>.png`.

### 7.6 Tempo por género

![Tempos](results/tempos_por_genero.png)

El tempo de cada canción es muy estable: entre los fragmentos de una misma canción varía en
promedio 3–6 BPM (11 BPM en el vallenato y 16 BPM en la balada, cuyo pulso es el menos claro).
Pero **el tempo solo no basta**: salsa, reggaetón y cumbia comparten el rango de 82–111 BPM, y
bachata, electrónica y buena parte del rock el de 115–135 BPM. Clasificar solo con el tempo
acierta el 39 % de las canciones (7.10).

**Ambigüedad de octava:** la autocorrelación tiene picos en P, 2P y P/2, todos correctos
matemáticamente. El sistema elige con una preferencia perceptual centrada en 110 BPM. Por eso:

- La **salsa** se mide a la mitad de su tempo escrito (~100 en vez de ~200 BPM: cuenta por
  blancas). Lo hace igual en las 8 canciones, así que no perjudica al clasificador.
- El **vallenato** se mide unas veces a la mitad (~77 BPM en *Los Caminos de la Vida* y *Las
  Locuras Mías*) y otras no (~132 BPM en *Olvídala*, ~136 en *Nunca Niegues Que Te Amo*).
- El **rock** igual: *Entre Dos Tierras* se mide a 83 BPM, la mitad de su tempo.
- La **balada** va de 67 a 132 BPM: con un pulso tan débil, el estimador a veces toma la
  subdivisión (las corcheas del piano o de la guitarra) como pulso.

**Cómo se resuelve.** No se intenta adivinar cuál de las tres octavas es la "correcta": como
todas lo son matemáticamente, cada fragmento de **entrenamiento** se describe tres veces, con el
periodo P estimado, con 2P (la mitad del tempo) y con P/2 (el doble). Solo hay que recalcular el
patrón de compás y las lecturas de la autocorrelación; el espectrograma y las envolventes son los
mismos. Un fragmento nuevo, medido en cualquiera de las tres octavas, encuentra así vecinos de su
género. Con esto *Entre Dos Tierras* pasó de clasificarse como cumbia a rock, y la exactitud por
canción subió de 81 a 86 % (7.10).

Con los ritmos sintéticos, donde se conoce el tempo real, el estimador acierta el pulso exacto en
el 83 % de los 160 fragmentos, y el pulso o su mitad/doble en el 96 %.

### 7.7 Patrón de compás

![Patrones](results/patrones_compas.png)

La envolvente de cada banda se divide en compases de 4 pulsos y cada compás en 16 casillas
(semicorcheas). Se promedia cada casilla sobre todos los compases del fragmento y se normaliza
entre 0 (la casilla más débil) y 1 (la más fuerte). El resultado es el dibujo del ritmo, y en
las canciones reales se reconocen los patrones de cada género:

- **Reggaetón:** en los medios (la caja), golpes en las semicorcheas 4, 7, 12 y 15: el **dembow**,
  agrupado 3 + 3 + 2.
- **Rock:** medios y agudos fuertes en los pulsos 2 y 4: la **caja en el contratiempo** del
  compás.
- **Electrónica:** graves iguales en los 4 pulsos: el bombo **"four on the floor"**.
- **Cumbia:** medios fuertes entre pulso y pulso (casillas 3, 7, 11 y 15): el **contratiempo** de
  la guitarra o el acordeón.
- **Bachata:** medios y agudos en cada pulso y en cada corchea: la **güira** y el bongó.
- **Salsa y vallenato:** ataques repartidos en casi todas las casillas (campana, congas,
  guacharaca), sin una posición dominante. Por eso el patrón los distingue menos.

Como no se sabe en qué casilla empieza el compás, además de la posición de los golpes se usa la
magnitud de la **DFT del patrón** de 16 pasos: |X[k]| no cambia si la secuencia se desplaza
circularmente, así que describe la forma del ritmo sin importar dónde empiece.

### 7.8 Efecto del ruido

![Ruido](results/ruido_comparacion.png)

Fragmento de 10 s de *Cali Pachanguero* con **ruido blanco gaussiano a SNR = 0 dB** (igual
potencia de ruido que de música):

- **(a) Tiempo:** los golpes casi no se distinguen en la forma de onda.
- **(b) Envolvente:** el ruido agrega picos pequeños en todas partes, pero los golpes fuertes
  siguen sobresaliendo. El ruido blanco tiene la misma potencia en todas las frecuencias y tapa
  sobre todo los agudos, donde la música tiene poca energía; en los graves y medios la música
  sigue por encima del ruido.
- **(c) Autocorrelación:** la claridad del pulso baja de 0,54 a 0,21, pero el máximo sigue en el
  mismo retardo: el tempo pasa de 99,6 a 99,4 BPM.
- **(d) Todas las canciones** (3 fragmentos por canción, 192 en total): porcentaje de fragmentos
  cuyo tempo no cambia más de 4 %:

| SNR | 20 dB | 10 dB | 5 dB | 0 dB | −5 dB |
|---|---|---|---|---|---|
| Ruido blanco | 97 % | 93 % | 89 % | 84 % | 71 % |
| Ruido rosa | 96 % | 94 % | 89 % | 86 % | 75 % |

Incluso con más ruido que música (−5 dB), siete de cada diez fragmentos conservan el tempo.
Para que el ruido no domine, la envolvente total suma las tres bandas **con el mismo peso** (cada
una dividida por su desviación estándar). Si se suman todas las frecuencias directamente, los
agudos (el 90 % de los bins de la FFT) dominan: en una prueba con los ritmos sintéticos y ruido
blanco a 0 dB, el tempo se conservó en el 65 % de los fragmentos con la suma directa y en el 85 %
con las bandas de igual peso.

### 7.9 Segmentación

![Segmentación](results/segmentacion.png)

1. **Fragmentos de 10 s** con solapamiento del 50 %. 10 s contienen entre 3 y 5 compases,
   suficientes para medir un patrón. Para el clasificador, cada canción aporta **como máximo 24
   fragmentos**, repartidos a lo largo de la canción y **sin los primeros ni los últimos 15 s**
   (introducción y final, que suelen no tener la percusión completa). Así una canción de 7 minutos
   no pesa el triple que una de 2: en total son 1526 fragmentos (24 por canción; 23 en tres
   canciones de unos 2,5 minutos y 17 en *We Will Rock You*, que dura 2).
2. **Tramas de la STFT** de 1 024 muestras (46,4 ms, Δf = 21,5 Hz) con ventana de Hann, que avanzan
   256 muestras (11,6 ms, solapamiento 75 %). Cada trama da una muestra de la envolvente. Se eligió
   una ventana corta porque aquí importa ubicar bien los golpes en el tiempo, más que separar
   frecuencias cercanas.
3. **Rejilla del compás:** 4 pulsos × 4 semicorcheas = 16 casillas.

### 7.10 Clasificación

![Clasificación](results/clasificacion.png)

Cada fragmento se describe con **57 características**: tempo; claridad y autocorrelación en
fracciones del pulso; energía, densidad y regularidad de ataques por banda; posición de los
golpes en el compás; |DFT| del patrón; dinámica; **percusividad** por banda; y **fuerza de los
ataques** con el rango dinámico (detalle en `docs/metodologia.md`). Se estandarizan con la media
y la desviación del conjunto de entrenamiento y se clasifican con **k-NN (k = 5)**: votan los 5
fragmentos más parecidos, con peso 1/distancia. El género de una canción es el más votado entre
sus fragmentos. Cada fragmento de entrenamiento se guarda también con el tempo a la mitad y al
doble (7.6).

La validación **deja una canción por fuera**: se entrena con las otras 63 y se prueba con esa,
para cada una de las 64. Así nunca hay fragmentos de la misma canción en entrenamiento y prueba
(si los hubiera, el clasificador reconocería la canción y no el género).

| Características | Cantidad | Por fragmento | Por canción |
|---|---|---|---|
| Solo tempo | 1 | 35 % | 39 % |
| Tempo y subdivisión (autocorrelación) | 9 | 52 % | 66 % |
| Energía, densidad y regularidad por banda | 9 | 36 % | 52 % |
| Patrón de compás | 33 | 50 % | 77 % |
| Intensidad (dinámica, percusividad, fuerza) | 6 | 28 % | 38 % |
| **Todas** | **57** | **66 %** | **86 %** |

Azar: 12 % (8 géneros). Ningún grupo basta solo, y juntos funcionan mejor que cualquiera por
separado. El patrón de compás es el grupo que más aporta.

**Por género** (canciones bien clasificadas, de 8): salsa 8, reggaetón 8, bachata 8, cumbia 7,
rock 7, electrónica 7, balada 5 y vallenato 5. Los 9 errores
(`results/clasificacion_canciones.csv`):

| Canción | Real | Predicho | Votos |
|---|---|---|---|
| La Gota Fría | vallenato | cumbia | 44 % |
| Las Locuras Mías | vallenato | bachata | 59 % |
| Esta Vida | vallenato | reggaetón | 36 % |
| Vivir Así Es Morir de Amor | balada | rock | 35 % |
| El Triste | balada | vallenato | 27 % |
| Amor Eterno | balada | bachata | 38 % |
| El Pescador | cumbia | rock | 42 % |
| Seven Nation Army | rock | electrónica | 55 % |
| Animals | electrónica | reggaetón | 28 % |

- **El vallenato** es el género más variado de la base: hay paseos lentos, merengues rápidos y
  vallenato romántico, con tempos medidos de 77 a 136 BPM. Por fragmento se reparte entre salsa,
  bachata, cumbia y reggaetón (matriz b).
- **La balada** casi no tiene percusión: su pulso es el menos claro (R[P] = 0,31) y sus
  fragmentos se parecen poco entre sí. Los errores tienen votos bajos (27–38 %): el clasificador
  "duda".
- *Seven Nation Army* tiene un bombo muy regular en cada pulso, como la electrónica. *Animals*
  tiene tramos largos sin bombo. *El Pescador* es una grabación con tambores tradicionales,
  distinta de las cumbias de orquesta de la base.

#### Qué cambió desde la Entrega 2 y cuánto aportó cada cambio

Todas las filas se midieron con las mismas 64 canciones y k = 5:

| Método | Por fragmento | Por canción |
|---|---|---|
| Entrega 2: 52 características | 61 % | 81 % (52) |
| + 5 características de intensidad (57) | 64 % | 81 % (52) |
| + entrenamiento con el tempo a la mitad y al doble | **66 %** | **86 %** (55) |

1. **Intensidad de los golpes** (5 valores). En el espectrograma, un golpe es una línea vertical
   y una nota sostenida es una línea horizontal. Un **filtro de mediana** a lo largo del tiempo
   conserva lo horizontal (H) y uno a lo largo de la frecuencia conserva lo vertical (P); la
   máscara P²/(H² + P²) dice qué fracción de la energía es golpe (Fitzgerald, 2010). Se calcula
   en las tres bandas. Además, la **fuerza de los ataques** (flujo espectral medio dividido entre
   el nivel medio) y el **rango dinámico** del RMS (percentil 90 − percentil 10, en dB). Mejoran
   la clasificación por fragmento; por canción no cambian el resultado.
2. **Tempo a la mitad y al doble** en el entrenamiento (7.6). Es el cambio que más aporta.

**Qué tan firme es el resultado.** Con 64 canciones, cada una vale 1,6 puntos. Repitiendo la
validación con k = 3, 5, 7 y 9, el método final da entre 52 y 55 canciones (81–86 %) y el de la
Entrega 2 entre 51 y 53 (80–83 %). La mejora por canción es pequeña y cercana al margen de
variación; la mejora por fragmento (de 61 a 66 %, sobre 1526 fragmentos) se mantiene con todos
los k.

**Lo que se probó y no se incluyó:**

- **Dar el mismo peso a cada grupo** de características (multiplicar cada una por 1/√n, con n el
  tamaño de su grupo, para que los 24 valores de |DFT| no dominen la distancia). Con 40 canciones
  mejoraba la balada; con 64 dio igual o peor que el peso uniforme (52–53 canciones), así que se
  retiró. Queda disponible en el código (`pesos_por_grupo`).
- **Timbre** (centroide espectral, planitud, energía en 8 bandas): sin mejora consistente, y el
  objetivo del proyecto es reconocer el género por el ritmo.
- **Descripciones que no dependen del tempo:** autocorrelación en retardos fijos (Dixon et al.,
  2003) y espectro de la envolvente en escala logarítmica (Peeters, 2005). Con 5 géneros dieron
  54–67 % por canción, frente a 79 % de las características de la Entrega 2.
- **Plegar el tempo a una sola octava** (por ejemplo 80–160 BPM): mejora menos que las variantes
  y depende de dónde se ponga el límite.

![Mapa de características](results/mapa_caracteristicas.png)

Proyección de los 57 valores a 2 dimensiones con análisis de componentes principales (PCA). La
**salsa** queda arriba; **reggaetón y cumbia** a la derecha, mezclados; **bachata y electrónica**
abajo a la derecha; el **rock** abajo en el centro y la **balada** a la izquierda, muy dispersa.
El **vallenato** no forma un grupo propio: se reparte entre la zona de la salsa y la del rock,
como en la matriz de confusión. En 2 de 57 dimensiones los grupos se superponen más de lo que los
ve el clasificador.

## 8. Referencias

1. G. Tzanetakis and P. Cook, "Musical genre classification of audio signals," *IEEE Trans.
   Speech and Audio Processing*, vol. 10, no. 5, pp. 293–302, 2002.
2. J. P. Bello, L. Daudet, S. Abdallah, C. Duxbury, M. Davies and M. Sandler, "A Tutorial on Onset
   Detection in Music Signals," *IEEE Trans. Speech and Audio Processing*, vol. 13, no. 5,
   pp. 1035–1047, 2005.
3. D. P. W. Ellis, "Beat Tracking by Dynamic Programming," *Journal of New Music Research*,
   vol. 36, no. 1, pp. 51–60, 2007.
4. S. Dixon, E. Pampalk and G. Widmer, "Classification of Dance Music by Periodicity Patterns," in
   *Proc. 4th Int. Conf. on Music Information Retrieval (ISMIR)*, 2003.
5. F. Gouyon and S. Dixon, "Dance Music Classification: A Tempo-Based Approach," in *Proc. 5th
   Int. Conf. on Music Information Retrieval (ISMIR)*, 2004.
6. G. Peeters, "Rhythm Classification Using Spectral Rhythm Patterns," in *Proc. 6th Int. Conf. on
   Music Information Retrieval (ISMIR)*, 2005.
7. M. Müller, *Fundamentals of Music Processing*, 2nd ed. Springer, 2021 (cap. 6: tempo y pulso).
8. A. V. Oppenheim and R. W. Schafer, *Discrete-Time Signal Processing*, 3rd ed. Pearson, 2010.
9. P. Virtanen et al., "SciPy 1.0: Fundamental Algorithms for Scientific Computing in Python,"
   *Nature Methods*, vol. 17, pp. 261–272, 2020.
10. C. R. Harris et al., "Array programming with NumPy," *Nature*, vol. 585, pp. 357–362, 2020.
11. J. D. Hunter, "Matplotlib: A 2D Graphics Environment," *Computing in Science & Engineering*,
    vol. 9, no. 3, pp. 90–95, 2007.
12. D. FitzGerald, "Harmonic/Percussive Separation using Median Filtering," in *Proc. 13th Int.
    Conf. on Digital Audio Effects (DAFx-10)*, Graz, 2010.

**Herramientas:** el código se escribió con apoyo de Claude (Anthropic) como asistente de programación.
