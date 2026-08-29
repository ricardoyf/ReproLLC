#!/usr/bin/env python3
"""
reproLLC PC simple.

Ejecuta este script desde la carpeta que quieras revisar. Busca en esa carpeta
y en sus subcarpetas SOLO fragmentos ya editados con VideoCortes o LosslessCut
PC, crea una playlist temporal y la abre con mpv/mpv.net.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ========= CONFIG =========
MPV_CANDIDATES = [
    r"C:\mpv\mpvnet.exe",
    r"C:\Program Files\mpv.net-v7.1.2.0-portable-x64\mpvnet.exe",
    r"C:\Program Files\mpv.net\mpvnet.exe",
]
PLAYER_NAMES = ("mpvnet.exe", "mpvnet", "mpv.exe", "mpv")
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".mts", ".m2ts", ".3gp"}
EDITED_TIME_RANGE = re.compile(
    r".*\d{2}\.\d{2}\.\d{2}\.\d{3}.*\d{2}\.\d{2}\.\d{2}\.\d{3}.*",
    re.IGNORECASE,
)
# ==========================


def find_player() -> str | None:
    for candidate in MPV_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    for name in PLAYER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def is_fragment(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS and bool(EDITED_TIME_RANGE.match(path.name))


def scan_fragments(root: Path) -> list[Path]:
    fragments: list[Path] = []
    for base, _, files in os.walk(root):
        for name in files:
            path = Path(base) / name
            if is_fragment(path):
                fragments.append(path)
    return sorted(fragments, key=lambda p: (p.name.lower(), str(p.parent).lower()))


def write_playlist(videos: list[Path]) -> str:
    fd, playlist = tempfile.mkstemp(suffix=".m3u", text=True)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        for video in videos:
            handle.write(str(video.resolve()) + "\n")
    return playlist


def write_input_conf() -> str:
    fd, input_conf = tempfile.mkstemp(suffix=".conf", text=True)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("MBTN_LEFT playlist-next\n")
    return input_conf


def main() -> int:
    base = Path.cwd()
    player = find_player()
    if not player:
        print("No encuentro mpv/mpv.net.")
        print(r"Rutas probadas: C:\mpv\mpvnet.exe y C:\Program Files\mpv.net-v7.1.2.0-portable-x64\mpvnet.exe")
        print("También busco mpvnet.exe/mpv.exe en el PATH.")
        return 1

    videos = scan_fragments(base)
    if not videos:
        print("No se encontraron fragmentos editados en esta carpeta ni subcarpetas.")
        print("Busco nombres con dos tiempos tipo 00.01.40.319-00.01.45.716")
        return 2

    print(f"Fragmentos encontrados: {len(videos)}")
    for index, video in enumerate(videos, start=1):
        print(f"{index:03d}. {video.relative_to(base)}")

    playlist = write_playlist(videos)
    input_conf = write_input_conf()

    cmd = [
        player,
        playlist,
        "--fullscreen",
        "--loop-playlist=inf",
        "--force-window=yes",
        "--keep-open=yes",
        "--hwdec=auto",
        "--vo=gpu",
        "--osc=no",
        f"--input-conf={input_conf}",
    ]
    subprocess.Popen(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
