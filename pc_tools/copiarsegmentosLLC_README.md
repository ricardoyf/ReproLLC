# copiarsegmentosLLC

Herramienta PC para copiar a una carpeta destino los fragmentos editados con VideoCortes o LosslessCut PC.

## Uso

```bat
python copiarsegmentosLLC.py
```

No requiere librerías externas.

## Detección

Detecta vídeos cuyo nombre contiene dos marcas de tiempo, por ejemplo:

```text
00.01.40.319-00.01.45.716
```

Esto cubre:

- Fragmentos de VideoCortes: `nombre-LLC-00.00.00.000-00.00.07.464.mp4`
- Fragmentos de LosslessCut PC: `nombre-00.01.40.319-00.01.45.716-seg3.mp4`
- Extensiones: `.mp4`, `.mov`, `.mkv`, `.3gp`, `.webm`, `.m4v`, `.mts`, `.m2ts`, `.avi`

## Comportamiento

- Escanea recursivamente la carpeta origen.
- Ordena por nombre de archivo.
- Permite seleccionar todos o solo algunos.
- Copia con `shutil.copy2`, conservando fecha de modificación.
- Si el archivo ya existe en destino, lo omite.
