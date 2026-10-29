#!/usr/bin/env bash
# Instala dependencias y accesos para el usuario actual; no copia ni modifica vídeos.
set -euo pipefail
if (( EUID == 0 )); then
    echo 'Ejecuta ./instalar-ubuntu.sh como tu usuario normal, sin sudo.' >&2
    echo 'El instalador pedirá la contraseña solo si necesita instalar paquetes.' >&2
    exit 1
fi
REPROLLC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
packages=(python3-gi gir1.2-gtk-3.0 gvfs-backends gvfs-fuse mpv xdg-user-dirs)
missing=()
for package in "${packages[@]}"; do
    if [[ "$package" == mpv ]] && command -v mpv >/dev/null 2>&1; then
        continue
    fi
    if [[ "$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true)" != 'install ok installed' ]]; then
        missing+=("$package")
    fi
done
if (( ${#missing[@]} )); then
    sudo apt-get install -y "${missing[@]}"
fi
export REPROLLC_DIR
/usr/bin/python3 - <<'PY'
import os
from pathlib import Path
import shutil
import subprocess
from gi.repository import GLib

root = Path(os.environ['REPROLLC_DIR'])

def desktop_quote(value):
    # Dos niveles de escape de Desktop Entry y su campo Exec; no se invoca un shell.
    out = ''
    for char in str(value):
        if char == '\\':
            out += '\\\\\\\\'
        elif char in '"`$':
            out += '\\\\' + char
        elif char == '%':
            out += '%%'
        else:
            out += char
    return '"' + out + '"'

entry = '\n'.join([
    '[Desktop Entry]', 'Version=1.0', 'Type=Application',
    'Name=ReproLLC · Vídeos del NAS',
    'Comment=Índice persistente: intervalo de años y reproducción rápida de clips LLC',
    'Exec=/usr/bin/python3 ' + desktop_quote(root / 'accesidorectoporaños.py'),
    'Icon=video-x-generic', 'Terminal=false', 'Categories=AudioVideo;Player;',
    'StartupNotify=true', '',
])
apps = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'applications'
apps.mkdir(parents=True, exist_ok=True)
(apps / 'reprollc.desktop').write_text(entry, encoding='utf-8')
desktop_value = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)
desktop = Path(desktop_value) if desktop_value else Path.home()
if desktop == Path.home():
    print('El escritorio está deshabilitado. Acceso creado en el menú de aplicaciones.')
else:
    desktop.mkdir(parents=True, exist_ok=True)
    shortcut = desktop / 'ReproLLC.desktop'
    shortcut.write_text(entry, encoding='utf-8')
    shortcut.chmod(0o755)
    result = subprocess.run(['gio', 'set', str(shortcut), 'metadata::trusted', 'true'], capture_output=True)
    if result.returncode:
        print('Si Ubuntu lo solicita, haz clic derecho en el acceso y elige «Permitir lanzar».')
    print('Acceso directo:', shortcut)
if shutil.which('update-desktop-database'):
    subprocess.run(['update-desktop-database', str(apps)], check=True)
print('Instalación completada. Abre «ReproLLC · Vídeos del NAS».')
print('El acceso apunta a este clon; si lo mueves, vuelve a ejecutar ./instalar-ubuntu.sh.')
PY
