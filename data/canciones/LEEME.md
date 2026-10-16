# Canciones

Esta carpeta debe contener los audios etiquetados. **No se suben a GitHub** porque tienen
derechos de autor; el README principal lista qué canción es cada archivo.

## Cómo armar la carpeta

1. Conseguir las canciones de la tabla del README (sección 3.1) en MP3 o WAV.
2. Basta un fragmento de 30 a 60 s del cuerpo de cada canción (sin la introducción ni el final).
3. Nombrar cada archivo con el género al inicio, seguido de un número:

```
salsa_01.mp3  salsa_02.mp3 ...
reggaeton_01.mp3 ...
bachata_01.mp3 ...
vallenato_01.mp3 ...
cumbia_01.mp3 ...
rock_01.mp3 ...
electronica_01.mp3 ...
balada_01.mp3 ...
```

El programa toma el género del nombre del archivo (`src/carga.py`, función `genero_de_archivo`).

## Recomendaciones

- 4 o 5 canciones por género, de **artistas distintos**. Si todas son del mismo artista, el
  clasificador aprende el estilo de ese artista y no el del género.
- Si la carpeta está vacía, los comandos usan los ritmos sintéticos de `data/sinteticos/`
  (se generan con `python main.py sinteticos`).
