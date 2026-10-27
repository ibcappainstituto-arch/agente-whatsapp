"""Static integration checks only; NOT PowerShell parsing or Windows execution."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ViewerLauncherContracts(unittest.TestCase):
    def scripts(self):
        return [(ROOT / name).read_text(encoding='utf-8') for name in ('INICIAR.ps1', 'INICIAR_NODE.ps1')]

    def test_viewer_only_no_static_image_or_token_argument(self):
        for script in self.scripts():
            self.assertIn("$viewerArgs = @($script:kitPythonPrefix) + @('qr_viewer.py')", script)
            self.assertIn('-ArgumentList $viewerArgs', script)
            self.assertIn('$viewerProcess.HasExited', script)
            self.assertIn('Stop-Process -InputObject $viewerProcess', script)
            for forbidden in ('/qr.svg', 'qr-privado.svg', 'Invoke-Item', '-OutFile', '$openedAt', 'ExecutionPolicy'):
                self.assertNotIn(forbidden, script)

    def test_config_is_read_as_utf8_and_no_dependency_install(self):
        for script in self.scripts():
            self.assertIn('Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath', script)
            self.assertIn('Invoke-KitPython -c "import tkinter"', script)
            self.assertNotIn('npm install', script)
            self.assertNotIn('pip install', script)


if __name__ == '__main__':
    unittest.main()
