<!-- app-release:start -->
[**Descargar APK v1**](https://github.com/ricardoyf/ReproLLC/raw/refs/tags/v1/release-artifacts/v1/reproLLC-v1.apk) · [SHA-256](https://github.com/ricardoyf/ReproLLC/raw/refs/tags/v1/release-artifacts/v1/reproLLC-v1.apk.sha256)

`292a6dd38a868a12f59fa577699fc1abbd12963880e3f6bd0f49551f3d7e3d04`
<!-- app-release:end -->

# reproLLC · Ubuntu v1.3 / Android v1

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

## Ubuntu: interfaz por años y meses

La versión Ubuntu v1.3 guarda un índice local persistente de los clips LLC. Permite elegir
un intervalo inclusivo de año inicial y final y empezar a reproducir en pocos segundos sin
volver a recorrer el NAS. El botón **Crear nuevo índice** fuerza un escaneo completo cuando
se añaden o eliminan vídeos; los archivos del NAS nunca se modifican.

La interfaz **`accesidorectoporaños`** permite elegir un año y uno o varios meses,
reproducir en orden aleatorio o por nombre, y abrir carpetas locales o de un NAS SMB.
Usa las funciones de playlist y controles del reproductor PC existente. No cambia
el funcionamiento de Android ni del script PC original.

### Instalar en otro PC Ubuntu

En una terminal, clona el repositorio y ejecuta el instalador **sin sudo**:

```bash
git clone https://github.com/ricardoyf/ReproLLC.git
cd ReproLLC
./instalar-ubuntu.sh
```

El instalador pide tu contraseña si faltan paquetes (`mpv`, GTK/Python o soporte
SMB). Crea **ReproLLC · Vídeos del NAS** en el escritorio y en el menú de
aplicaciones. No requiere pip ni rutas de un usuario concreto. Conserva la carpeta
del repositorio: el acceso apunta a ese clon. Si lo mueves, ejecuta de nuevo el
instalador desde su nueva ubicación.

Con las dependencias instaladas, también se puede abrir directamente:

```bash
./accesidorectoporaños
```

### Elegir los vídeos

1. La carpeta inicial es `smb://dsplay214.local/video/home%20video`.
   Puedes cambiarla escribiendo otra ruta o pulsando **Elegir carpeta…**.
   Debe contener carpetas por año (`2026`, `2025`, etc.).
2. Elige año, marca uno o varios meses y pulsa **Reproducir en mpv**.
3. **Orden aleatorio** está activado de inicio; puedes desmarcarlo.

El NAS debe ser accesible desde ese PC. Al conectarse, Ubuntu puede pedir sus
credenciales; las gestiona Ubuntu, no el repositorio. No se incluyen contraseñas.
Se reproduce directamente desde la carpeta, sin copiar ni modificar los vídeos.

La interfaz incluye archivos de vídeo con **LLC** en el nombre (sin distinguir
mayúsculas) y fecha inicial `AAAAMMDD` o `AAAA-MM-DD` (también admite separadores
`.` y `_`). Usa esa fecha, no la fecha de modificación. Por ejemplo:

```text
2026/09 septiembre/20260903_180817-LLC-00.00.00.000-00.00.08.672.mp4
```

Recuerda la carpeta, el año, los meses y el orden de la última reproducción en
`~/.config/reprollc/interfaz.json`. En una instalación nueva selecciona el mes y
año actuales. El filtro LLC de esta interfaz es independiente del detector de dos
marcas de tiempo del script PC original.

**Controles de mpv:** clic izquierdo = siguiente clip; Espacio = pausa; Q = salir.
La lista se repite automáticamente. Los errores de reproducción quedan en
`~/.local/state/reprollc/mpv.log`.

## PC con mpv/mpv.net (script original sin interfaz)

Archivos:

- `reproLLC.py`
- `reproLLC_pc.py`
- `reproLLC_pc.bat`

Uso:

1. Copia los scripts en la carpeta que quieras revisar o ejecútalos desde ella.
2. Doble clic en `reproLLC_pc.bat`.
3. Reproduce solo fragmentos editados detectados por dos marcas de tiempo en el nombre.

No pide fechas ni carpeta. Busca en la carpeta actual y subcarpetas. Usa `mpvnet.exe` si está en `C:\mpv\mpvnet.exe`, en `C:\Program Files\mpv.net-v7.1.2.0-portable-x64\mpvnet.exe` o en el PATH.
