import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_synthetic_demo_is_explicit(self):
        run = subprocess.run([sys.executable, '-m', 'atlas', '--demo'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        report = json.loads(run.stdout)
        self.assertEqual(report['portfolio']['mode'], 'synthetic')
        self.assertEqual(report['hypothetical_put']['expiration_pnl'], '-2801')

    def test_invalid_input_rejected_without_content_or_path_leak(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private-account.json'
            path.write_text('{private-sensitive-test-value')
            run = subprocess.run([sys.executable, '-m', 'atlas', '--snapshot', str(path)],
                                 capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, '')
        self.assertNotIn('private-sensitive-test-value', run.stderr)
        self.assertNotIn('private-account', run.stderr)
