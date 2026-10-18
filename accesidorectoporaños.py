#!/usr/bin/python3
"""Interfaz Ubuntu para ReproLLC: año, meses y reproducción local/NAS con mpv."""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, Gtk

import reproLLC_pc as player

DEFAULT_URI = 'smb://dsplay214.local/video/home%20video'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'reprollc/interfaz.json'
MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def selected_videos(root, year, months):
    """La fecha procede del nombre del vídeo, nunca de su última modificación."""
    year_root = root / str(year)
    if not year_root.is_dir():
        raise ValueError(f'No se encuentra la carpeta {year} en la carpeta de vídeos elegida.')
    candidates = []
    # Examinar solo las carpetas de los meses elegidos; incluir archivos en la raíz anual.
    for item in year_root.iterdir():
        if item.is_file():
            candidates.append(item)
        elif item.is_dir():
            prefix = re.match(r'^(\d{1,2})(?:\D|$)', item.name)
            if prefix and 1 <= int(prefix[1]) <= 12 and int(prefix[1]) not in months:
                continue
            def scan_error(error):
                raise error
            for base, _, files in os.walk(item, onerror=scan_error):
                candidates.extend(Path(base) / name for name in files
                                  if 'llc' in name.lower() and Path(name).suffix.lower() in player.VIDEO_EXTS)
    result = []
    for path in candidates:
        if 'llc' not in path.name.lower() or path.suffix.lower() not in player.VIDEO_EXTS:
            continue
        date = re.match(r'^(\d{4})[-_.]?(\d{2})[-_.]?(\d{2})', path.name)
        if not date:
            continue
        try:
            day = datetime.date(*map(int, date.groups()))
        except ValueError:
            continue
        if day.year == year and day.month in months:
            result.append(path)
    return sorted(set(result), key=lambda p: (p.name.lower(), str(p)))


class ReproLLC(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='local.ricardo.ReproLLC')
        self.window = None

    def do_activate(self):
        if self.window:
            self.window.present()
            return
        try:
            saved = json.loads(CONFIG.read_text())
        except (OSError, ValueError):
            saved = {}
        self.window = Gtk.ApplicationWindow(application=self, title='ReproLLC · Vídeos del NAS')
        self.window.set_default_size(630, 410)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, margin=22)
        self.window.add(box)
        title = Gtk.Label(xalign=0)
        title.set_markup('<big><b>Elige los meses que quieres ver</b></big>')
        box.pack_start(title, False, False, 0)
        box.pack_start(Gtk.Label(label='Solo vídeos editados cuyo nombre incluya LLC.', xalign=0), False, False, 0)
        row = Gtk.Box(spacing=8)
        self.source = Gtk.Entry()
        self.source.set_text(saved.get('source', DEFAULT_URI))
        self.source.set_tooltip_text('Carpeta que contiene las subcarpetas de cada año')
        row.pack_start(self.source, True, True, 0)
        change = Gtk.Button(label='Elegir carpeta…')
        change.connect('clicked', self.choose_folder)
        row.pack_start(change, False, False, 0)
        box.pack_start(row, False, False, 0)
        row = Gtk.Box(spacing=10)
        row.pack_start(Gtk.Label(label='Año:'), False, False, 0)
        self.year = Gtk.SpinButton.new_with_range(1900, 2100, 1)
        self.year.set_value(saved.get('year', datetime.date.today().year))
        row.pack_start(self.year, False, False, 0)
        all_button = Gtk.Button(label='Todos los meses')
        all_button.connect('clicked', lambda _: [c.set_active(True) for c in self.months])
        row.pack_end(all_button, False, False, 0)
        box.pack_start(row, False, False, 0)
        grid = Gtk.Grid(column_spacing=24, row_spacing=12)
        self.months = []
        for i, name in enumerate(MONTHS):
            check = Gtk.CheckButton(label=name)
            check.set_active(i + 1 in saved.get('months', [datetime.date.today().month]))
            self.months.append(check)
            grid.attach(check, i % 3, i // 3, 1, 1)
        box.pack_start(grid, False, False, 0)
        self.shuffle = Gtk.CheckButton(label='Reproducir en orden aleatorio')
        self.shuffle.set_active(saved.get('shuffle', True))
        box.pack_start(self.shuffle, False, False, 0)
        self.status = Gtk.Label(label='Selecciona uno o varios meses y pulsa Reproducir.', xalign=0)
        self.status.set_line_wrap(True)
        box.pack_start(self.status, True, True, 0)
        self.play = Gtk.Button(label='▶ Reproducir en mpv')
        self.play.get_style_context().add_class('suggested-action')
        self.play.connect('clicked', self.prepare)
        box.pack_start(self.play, False, False, 0)
        box.pack_start(Gtk.Label(label='En mpv: clic izquierdo = siguiente · Espacio = pausa · Q = salir', xalign=0), False, False, 0)
        self.window.show_all()

    def choose_folder(self, _):
        dialog = Gtk.FileChooserDialog(title='Carpeta de vídeos (contiene los años)', parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Elegir', Gtk.ResponseType.OK)
        dialog.set_local_only(False)
        dialog.set_current_folder_uri(self.source.get_text())
        if dialog.run() == Gtk.ResponseType.OK:
            self.source.set_text(dialog.get_uri())
        dialog.destroy()

    def prepare(self, _):
        months = [i + 1 for i, c in enumerate(self.months) if c.get_active()]
        if not months:
            self.status.set_text('Selecciona al menos un mes.')
            return
        self.selection = dict(source=self.source.get_text().strip(), year=self.year.get_value_as_int(),
                              months=months, shuffle=self.shuffle.get_active())
        self.play.set_sensitive(False)
        self.status.set_text('Conectando con la carpeta de vídeos…')
        file = Gio.File.new_for_commandline_arg(self.selection['source'])
        if file.get_uri_scheme() == 'file':
            self.start_scan(file)
        else:
            op = Gtk.MountOperation.new(self.window)
            file.mount_enclosing_volume(Gio.MountMountFlags.NONE, op, None, self.mounted)

    def mounted(self, file, result):
        try:
            file.mount_enclosing_volume_finish(result)
        except GLib.Error as error:
            if not error.matches(Gio.io_error_quark(), Gio.IOErrorEnum.ALREADY_MOUNTED):
                self.error(f'No se pudo conectar al NAS: {error.message}')
                return
        self.start_scan(file)

    def start_scan(self, file):
        path = file.get_path()
        if not path:
            self.error('La carpeta no está disponible como unidad local. Ábrela en Archivos y vuelve a intentarlo.')
            return
        selection = self.selection.copy()
        self.status.set_text('Buscando los clips LLC de los meses seleccionados…')
        def worker():
            try:
                videos = selected_videos(Path(path), selection['year'], selection['months'])
                GLib.idle_add(self.start_player, videos, selection)
            except Exception as error:
                GLib.idle_add(self.error, str(error))
        threading.Thread(target=worker, daemon=True).start()

    def error(self, message):
        self.status.set_text(message)
        self.play.set_sensitive(True)
        return False

    def start_player(self, videos, selection):
        if not videos:
            return self.error('No se encontraron vídeos LLC para esos meses. Se buscan fechas en el nombre, como 20260903_…')
        executable = player.find_player()
        if not executable:
            return self.error('No se encuentra mpv instalado.')
        try:
            playlist = player.write_playlist(videos)
            conf = player.write_input_conf()
            cmd = [executable, f'--playlist={playlist}', '--fullscreen', '--loop-playlist=inf',
                   '--hwdec=auto', '--osc=no', f'--input-conf={conf}']
            if selection['shuffle']:
                cmd.append('--shuffle')
            CONFIG.parent.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + '\n')
            logdir = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'reprollc'
            logdir.mkdir(parents=True, exist_ok=True)
            with (logdir / 'mpv.log').open('w') as log:
                proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            self.status.set_text(f'Reproduciendo {len(videos)} clips LLC en mpv. Puedes volver aquí para elegir otros meses.')
            self.play.set_sensitive(True)
            GLib.timeout_add(1200, self.check_player, proc)
        except Exception as error:
            return self.error(str(error))
        return False

    def check_player(self, proc):
        code = proc.poll()
        if code not in (None, 0):
            self.error('mpv no pudo iniciar la reproducción. Consulta ~/.local/state/reprollc/mpv.log.')
        return False


if __name__ == '__main__':
    raise SystemExit(ReproLLC().run(sys.argv))
