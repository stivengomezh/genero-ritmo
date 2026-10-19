# Metodología detallada

Este documento amplía el README con todos los parámetros y fórmulas. Los valores están en
`src/config.py`.

## 1. Preprocesamiento (`src/carga.py`)

1. **Lectura:** el archivo se decodifica a muestras en coma flotante en [−1, 1] (con `soundfile`;
   si no está instalado o no reconoce el formato, con `librosa` o `ffmpeg`).
2. **Mono:** x_m[n] = (x_L[n] + x_R[n]) / 2.
3. **Remuestreo a 22 050 Hz:** `scipy.signal.resample_poly` (filtro FIR polifásico
   pasabajos en el nuevo Nyquist, 11 025 Hz, y diezmado por 2 si el original es 44 100 Hz).
4. **Normalización:** se resta la media (componente DC) y se divide por el máximo absoluto.
5. **Fragmentación:** bloques de 10 s (220 500 muestras) que avanzan 5 s.
6. **Selección para el clasificador** (`fragmentos_para_clasificar`): si la canción dura más de
   60 s, se descartan los fragmentos que tocan los primeros o los últimos 15 s; de los que quedan
   se toman como máximo 24, repartidos uniformemente (índices `round(linspace(0, n−1, 24))`).

## 1b. Espectro de la canción completa (`analisis.espectro`)

Densidad espectral de potencia por el método de Welch (`scipy.signal.welch`): bloques de
N = 65 536 muestras (1,49 s a 44,1 kHz) con ventana de Hann y 50 % de solapamiento;
P[k] = promedio de |X_m[k]|² sobre los bloques. Δf = fs/N = 0,67 Hz. Para las figuras se promedia
en bandas de 1/6 de octava. La energía por banda es la suma de P[k] en la banda dividida por la
suma total.

## 2. Espectrograma (`ritmo.espectrograma`)

X(m, k) = Σₙ x[n + m·H] · w[n] · e^(−j2πkn/N)

| Parámetro | Valor | Consecuencia |
|---|---|---|
| Ventana w[n] | Hann, N = 1 024 | 46,4 ms; Δf = 22 050 / 1 024 = 21,5 Hz |
| Salto H | 256 muestras | 11,6 ms; solapamiento 75 %; la envolvente queda muestreada a 86,13 Hz |

## 3. Envolventes de ataques (`ritmo.envolventes`)

1. Compresión logarítmica: L[k, m] = log(1 + γ·|X(m, k)|), γ = 100. Imita la percepción de
   intensidad del oído y evita que solo cuenten los golpes más fuertes.
2. Flujo espectral por banda b: e_b[m] = Σ_{k ∈ b} máx(0, L[k, m] − L[k, m−1]). Es una derivada
   discreta en el tiempo con rectificación de media onda: solo suman los aumentos de energía.
3. Se resta la media móvil de 0,5 s (43 tramas) y se vuelve a rectificar: queda solo lo que
   sobresale de su entorno.
4. Bandas: graves 30–200 Hz, medios 200–2 000 Hz, agudos 2 000–10 000 Hz.
5. Envolvente total: e[m] = Σ_b e_b[m] / σ_b (cada banda con el mismo peso).

## 4. Tempo (`ritmo.estimar_tempo`)

1. Autocorrelación normalizada e insesgada, calculada con la FFT:
   R[ℓ] = (1/(M−ℓ)) Σ_m ẽ[m]·ẽ[m+ℓ] / R₀, con ẽ = e − ē, hasta ℓ = 4 s.
2. Puntaje para cada periodo candidato ℓ (entre 50 y 220 BPM):
   S(ℓ) = w(ℓ) · (R⁺[ℓ] + ½·R⁺[2ℓ] + ½·R⁺[ℓ/2]),
   con R⁺ = máx(R, 0) y w(ℓ) = exp(−½·(log₂(BPM/110)/0,7)²) (preferencia perceptual).
3. P = argmax S, refinado con interpolación parabólica; tempo = 60·86,13/P BPM.
4. Claridad del pulso: R[P].

## 5. Patrón de compás (`ritmo.patron_compas`)

1. Fase del pulso: φ que maximiza el promedio de e en φ, φ+P, φ+2P, …
2. Compás = 4P; paso = P/4 (semicorchea). Para cada casilla j (0…15) de cada compás c se toma
   el máximo de e_b en ±½ paso alrededor de φ + (16c + j)·P/4.
3. Se promedia sobre los compases y se normaliza por banda entre 0 y 1.
4. Se rota de a un pulso para que la casilla 0 sea el pulso con más graves.

## 6. Características (`src/caracteristicas.py`)

| Grupo | Fórmula | Cant. |
|---|---|---|
| Tempo | log₂(BPM/110) | 1 |
| Claridad | R[P] | 1 |
| Subdivisión | R en P/4, P/3, P/2, 2P/3, 3P/4, 3P/2, 2P | 7 |
| Energía de ataques | Σe_b / Σ_b Σe_b | 3 |
| Densidad | picos de e_b > 30 % del máximo, separados ≥ 70 ms, por segundo | 3 |
| Regularidad | R_b[P] de cada banda | 3 |
| Posición | fracción del patrón en pulsos (0, 4, 8, 12), contratiempos (2, 6, 10, 14) y semicorcheas (impares) | 9 |
| Forma | \|DFT₁₆(patrón_b)\|[k] / \|DFT₁₆\|[0], k = 1…8 | 24 |
| Dinámica | desviación estándar del RMS en dB, ventanas de 0,5 s | 1 |

La |DFT| del patrón es invariante al desplazamiento circular: si p[n] → p[(n − n₀) mod 16],
entonces X[k] → X[k]·e^(−j2πkn₀/16) y |X[k]| no cambia.

## 7. Clasificador (`src/clasificador.py`)

- Estandarización z = (v − μ)/σ con μ y σ del entrenamiento.
- k-NN con distancia euclidiana, k = 5, voto ponderado por 1/(d + ε).
- Canción: suma de los votos normalizados de sus fragmentos.
- Validación dejando una canción por fuera; se reporta exactitud por fragmento y por canción,
  matriz de confusión y comparación por grupos de características.

## 8. Limitaciones observadas con las 34 canciones

- **Octava del tempo:** la salsa se mide siempre a la mitad (~100 en vez de ~200 BPM), lo que no
  afecta porque es consistente; el vallenato se mide unas veces a la mitad (~77 BPM) y otras no
  (~132 BPM), y esa inconsistencia contribuye a que sea el género peor clasificado (2 de 5).
- **Géneros con la misma base rítmica:** vallenato y cumbia (guacharaca en corcheas, 2/4) y rock
  y electrónica (4/4, bombo en el pulso, ~125 BPM) se confunden. Distinguirlos mejor requiere
  describir la subdivisión con más detalle o, para rock y electrónica, el timbre.
- **Compases que no son de 4 pulsos** (por ejemplo, música en 3/4 o 6/8) se describen con una
  rejilla incorrecta.
- **Canciones con cambios de ritmo** (por ejemplo *Tití Me Preguntó*, que cambia a mitad de la
  canción) tienen fragmentos de dos estilos; la votación por canción lo compensa en parte.
- **Grabaciones saturadas o antiguas** (*Periódico de Ayer*: 1,8 % de muestras recortadas, casi
  mono) no afectaron la clasificación, pero sí cambian la caracterización (RMS y cresta).
- **Tamaño de la base:** con 4–5 canciones por género, cada canción equivale a 3 puntos de
  exactitud; los resultados deben leerse con ese margen.
- **Formas alternativas probadas:** autocorrelación en retardos fijos (Dixon et al., 2003) y
  espectro de la envolvente en escala logarítmica (Peeters, 2005); con 5 géneros dieron 54–67 %
  por canción, frente al 79 % que dieron las 52 características actuales con esos mismos 5 géneros.
