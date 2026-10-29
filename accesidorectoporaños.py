#!/usr/bin/python3
"""ReproLLC Linux v1.3: índice persistente y reproducción por intervalo de años."""
import concurrent.futures
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

APP_VERSION = '1.3'
DEFAULT_URI = 'smb://dsplay214.local/video/home%20video'
CONFIG_DIR = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'reprollc'
CONFIG = CONFIG_DIR / 'interfaz.json'
INDEX_FILE = CONFIG_DIR / 'indice-videos.json'
MONTHS = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
DATE_RE = re.compile(r'^(\d{4})[-_.]?(\d{2})[-_.]?(\d{2})')
MPV_ARGS = ['--fullscreen','--loop-playlist=inf','--hwdec=auto-safe','--vo=gpu','--profile=fast',
            '--scale=bilinear','--dscale=bilinear','--cscale=bilinear','--interpolation=no',
            '--deband=no','--correct-downscaling=no','--sigmoid-upscaling=no','--video-unscaled=no',
            '--autofit-larger=1920x1080','--framedrop=decoder','--video-sync=audio','--osc=no']


def video_date(path):
    match = DATE_RE.match(path.name)
    if not match:
        return None
    try:
        return datetime.date(*map(int, match.groups()))
    except ValueError:
        return None


def selected_videos(root, year, months):
    year_root = root / str(year)
    if not year_root.is_dir():
        raise ValueError(f'No se encuentra la carpeta {year} en la carpeta de vídeos elegida.')
    rows = create_index(year_root, roots_are_years=True)
    return [Path(row['path']) for row in rows if int(row['date'][:4]) == year and int(row['date'][5:7]) in months]


def create_index(root, roots_are_years=False):
    if roots_are_years:
        roots = [root] if root.is_dir() else []
    else:
        roots = [p for p in root.iterdir() if p.is_dir() and re.fullmatch(r'(?:19|20)\d{2}', p.name)]
        if not roots:
            roots = [root]
    def scan(scan_root):
        batch = []
        for base, _, files in os.walk(scan_root):
            for name in files:
                path = Path(base) / name
                if 'llc' not in name.lower() or path.suffix.lower() not in player.VIDEO_EXTS:
                    continue
                day = video_date(path)
                if day:
                    batch.append({'path': str(path), 'date': day.isoformat()})
        return batch
    rows = []
    if roots:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(roots))) as pool:
            for batch in pool.map(scan, roots):
                rows.extend(batch)
    rows.sort(key=lambda row: (row['date'], row['path'].casefold()))
    return rows


def save_index(source, rows):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = INDEX_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps({'source': source, 'created': datetime.datetime.now().isoformat(),
                               'videos': rows}, ensure_ascii=False), encoding='utf-8')
    tmp.replace(INDEX_FILE)


def load_index(source):
    try:
        data = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return data.get('videos') if data.get('source') == source else None


class ReproLLC(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='local.ricardo.ReproLLC')
        self.window = None
        self.rebuild = False

    def do_activate(self):
        if self.window:
            self.window.present(); return
        try: saved = json.loads(CONFIG.read_text())
        except (OSError, ValueError): saved = {}
        today = datetime.date.today().year
        self.window = Gtk.ApplicationWindow(application=self, title=f'ReproLLC · Vídeos del NAS v{APP_VERSION}')
        self.window.set_default_size(680, 460)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=20); self.window.add(box)
        title = Gtk.Label(xalign=0); title.set_markup('<big><b>Reproducir clips LLC desde un índice rápido</b></big>'); box.pack_start(title, False, False, 0)
        row = Gtk.Box(spacing=8); self.source = Gtk.Entry(text=saved.get('source', DEFAULT_URI)); row.pack_start(self.source, True, True, 0)
        choose = Gtk.Button(label='Elegir carpeta…'); choose.connect('clicked', self.choose_folder); row.pack_start(choose, False, False, 0); box.pack_start(row, False, False, 0)
        years = Gtk.Box(spacing=10); years.pack_start(Gtk.Label(label='Desde:'), False, False, 0)
        self.year_from = Gtk.SpinButton.new_with_range(1900,2100,1); self.year_from.set_value(saved.get('year_from', saved.get('year', today))); years.pack_start(self.year_from, False, False, 0)
        years.pack_start(Gtk.Label(label='Hasta (incluido):'), False, False, 0)
        self.year_to = Gtk.SpinButton.new_with_range(1900,2100,1); self.year_to.set_value(saved.get('year_to', saved.get('year', today))); years.pack_start(self.year_to, False, False, 0)
        box.pack_start(years, False, False, 0)
        grid = Gtk.Grid(column_spacing=22,row_spacing=9); self.months=[]
        for i,name in enumerate(MONTHS):
            c=Gtk.CheckButton(label=name); c.set_active(i+1 in saved.get('months', list(range(1,13)))); self.months.append(c); grid.attach(c,i%3,i//3,1,1)
        box.pack_start(grid,False,False,0)
        self.shuffle=Gtk.CheckButton(label='Reproducir en orden aleatorio'); self.shuffle.set_active(saved.get('shuffle',True)); box.pack_start(self.shuffle,False,False,0)
        self.status=Gtk.Label(label='El índice guardado permite empezar en pocos segundos.',xalign=0); self.status.set_line_wrap(True); box.pack_start(self.status,True,True,0)
        buttons=Gtk.Box(spacing=10); self.index_button=Gtk.Button(label='⟳ Crear nuevo índice'); self.index_button.connect('clicked',self.prepare_index); buttons.pack_start(self.index_button,False,False,0)
        self.play=Gtk.Button(label='▶ Reproducir'); self.play.get_style_context().add_class('suggested-action'); self.play.connect('clicked',self.prepare_play); buttons.pack_end(self.play,False,False,0); box.pack_start(buttons,False,False,0)
        box.pack_start(Gtk.Label(label=f'Versión {APP_VERSION} · Crea un índice nuevo solo cuando añadas vídeos.',xalign=1),False,False,0)
        self.window.show_all()

    def choose_folder(self,_):
        d=Gtk.FileChooserDialog(title='Carpeta de vídeos',parent=self.window,action=Gtk.FileChooserAction.SELECT_FOLDER)
        d.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Elegir',Gtk.ResponseType.OK); d.set_local_only(False); d.set_current_folder_uri(self.source.get_text())
        if d.run()==Gtk.ResponseType.OK: self.source.set_text(d.get_uri())
        d.destroy()

    def selection(self):
        return {'source':self.source.get_text().strip(),'year_from':self.year_from.get_value_as_int(),
                'year_to':self.year_to.get_value_as_int(),'months':[i+1 for i,c in enumerate(self.months) if c.get_active()],
                'shuffle':self.shuffle.get_active()}

    def prepare_play(self,_):
        sel=self.selection()
        if sel['year_from']>sel['year_to'] or not sel['months']:
            self.status.set_text('Revisa el intervalo de años y selecciona al menos un mes.'); return
        self.rebuild=False; self.connect_source(sel)

    def prepare_index(self,_):
        self.rebuild=True; self.connect_source(self.selection())

    def connect_source(self,sel):
        self.current=sel; self.play.set_sensitive(False); self.index_button.set_sensitive(False); self.status.set_text('Conectando con el NAS…')
        f=Gio.File.new_for_commandline_arg(sel['source'])
        if f.get_uri_scheme()=='file': self.ready(f)
        else: f.mount_enclosing_volume(Gio.MountMountFlags.NONE,Gtk.MountOperation.new(self.window),None,self.mounted)

    def mounted(self,f,result):
        try: f.mount_enclosing_volume_finish(result)
        except GLib.Error as e:
            if not e.matches(Gio.io_error_quark(),Gio.IOErrorEnum.ALREADY_MOUNTED): return self.error('No se pudo conectar al NAS: '+e.message)
        self.ready(f)

    def ready(self,f):
        root=f.get_path()
        if not root: return self.error('Abre primero la carpeta del NAS en Archivos.')
        rows=None if self.rebuild else load_index(self.current['source'])
        if rows is not None:
            return self.use_index(rows)
        self.status.set_text('Creando el índice completo. La primera vez puede tardar; las siguientes serán inmediatas.')
        def worker():
            try:
                rows=create_index(Path(root)); save_index(self.current['source'],rows); GLib.idle_add(self.index_done,rows)
            except Exception as e: GLib.idle_add(self.error,str(e))
        threading.Thread(target=worker,daemon=True).start()

    def index_done(self,rows):
        if self.rebuild:
            self.status.set_text(f'Índice nuevo creado: {len(rows)} clips. Ya puedes reproducir al instante.'); self.enable(); return False
        return self.use_index(rows)

    def use_index(self,rows):
        sel=self.current; videos=[Path(r['path']) for r in rows if sel['year_from']<=int(r['date'][:4])<=sel['year_to'] and int(r['date'][5:7]) in sel['months']]
        if not videos: return self.error('El índice no contiene clips LLC para ese intervalo. Si añadiste vídeos, pulsa Crear nuevo índice.')
        self.status.set_text(f'Índice recuperado: {len(videos)} clips. Iniciando MPV…'); return self.start_player(videos,sel)

    def enable(self):
        self.play.set_sensitive(True); self.index_button.set_sensitive(True)

    def error(self,msg):
        self.status.set_text(msg); self.enable(); return False

    def start_player(self,videos,sel):
        executable=player.find_player()
        if not executable: return self.error('No se encuentra MPV.')
        playlist=player.write_playlist(videos); conf=player.write_input_conf(); cmd=[executable,f'--playlist={playlist}',*MPV_ARGS,f'--input-conf={conf}']
        if sel['shuffle']: cmd.append('--shuffle')
        CONFIG_DIR.mkdir(parents=True,exist_ok=True); CONFIG.write_text(json.dumps(sel,ensure_ascii=False,indent=2)+'\n')
        logdir=Path(os.environ.get('XDG_STATE_HOME',Path.home()/'.local/state'))/'reprollc'; logdir.mkdir(parents=True,exist_ok=True)
        with (logdir/'mpv.log').open('w') as log: subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        self.status.set_text(f'Reproduciendo {len(videos)} clips LLC.'); self.enable(); return False


if __name__=='__main__':
    raise SystemExit(ReproLLC().run(sys.argv))
