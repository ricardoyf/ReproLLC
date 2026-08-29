# reproLLC v1

App Android independiente para reproducir fragmentos de video editados con VideoCortes o LosslessCut PC.

## Flujo

- Abre siempre en horizontal.
- Pulsa `Carpeta` y elige la carpeta de trabajo.
- Pulsa `Fechas` y selecciona fecha inicial y final con ruedas separadas de año, mes y día.
- Busca recursivamente en subcarpetas.
- Reproduce a pantalla completa los fragmentos editados que caen dentro del rango.
- Los videos pasan solos en orden por nombre de archivo.

## Detector de fragmentos

Incluye archivos de video cuyo nombre contiene dos marcas de tiempo tipo:

```text
00.01.40.319-00.01.45.716
```

Esto cubre los fragmentos creados por VideoCortes y los exportados desde LosslessCut PC.

## Identidad Android

- Paquete: `com.ricardo.reprollc`
- Version code: `1`
- Version name: `1.0`
- Android minimo: API 26
- Target: API 34

## PC con mpv/mpv.net

Archivos:

- `reproLLC.py`
- `reproLLC_pc.py`
- `reproLLC_pc.bat`

Uso:

1. Copia los scripts en la carpeta que quieras revisar o ejecútalos desde ella.
2. Doble clic en `reproLLC_pc.bat`.
3. Reproduce solo fragmentos editados detectados por dos marcas de tiempo en el nombre.

No pide fechas ni carpeta. Busca en la carpeta actual y subcarpetas. Usa `mpvnet.exe` si está en `C:\mpv\mpvnet.exe`, en `C:\Program Files\mpv.net-v7.1.2.0-portable-x64\mpvnet.exe` o en el PATH.
