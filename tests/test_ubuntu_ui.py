"""Pruebas del filtro sin acceder al NAS ni abrir un reproductor."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('reprollc_ui', ROOT / 'accesidorectoporaños.py')
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


class MonthSelection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def video(self, path):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return path

    def test_multiple_months_and_originals(self):
        september = self.video('2026/09 septiembre/20260903_120000-LLC.mp4')
        october = self.video('2026/10 octubre/20261001_120000-llc.mkv')
        self.video('2026/09 septiembre/20260903_120000-original.mp4')
        self.video('2026/09 septiembre/20260903_120000-LLC.txt')
        self.assertEqual(ui.selected_videos(self.root, 2026, [9]), [september])
        self.assertEqual(ui.selected_videos(self.root, 2026, [9, 10]), [september, october])

    def test_filename_dates_and_nested_directories(self):
        expected = [self.video('2026/09 septiembre/camara/2026-09-02-LLC.mp4'),
                    self.video('2026/2026.09.01-LLC.mov'),
                    self.video('2026/2026_09_03-LLC.webm')]
        self.video('2026/20260931-fecha-invalida-LLC.mp4')
        self.video('2026/20250901-otro-año-LLC.mp4')
        self.video('2026/sin-fecha-LLC.mp4')
        self.assertCountEqual(ui.selected_videos(self.root, 2026, [9]), expected)

    def test_missing_year_has_actionable_error(self):
        with self.assertRaisesRegex(ValueError, 'carpeta 2026'):
            ui.selected_videos(self.root, 2026, [9])


if __name__ == '__main__':
    unittest.main()
