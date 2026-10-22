"""Focused proof for the SessionStart hook: the discipline reaches the session
without its status header.

Run: python3 -m unittest discover -s tests   (from the nomad-method root)
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

PLUGIN = os.path.join(os.path.dirname(__file__), "..", "plugin")
PRINT = os.path.join(PLUGIN, "scripts", "print_document.py")


def run(path):
    return subprocess.run([sys.executable, PRINT, path], capture_output=True, text=True)


class SessionStartTest(unittest.TestCase):
    def test_hook_prints_the_discipline_through_the_header_stripper(self):
        with open(os.path.join(PLUGIN, "hooks", "hooks.json"), encoding="utf-8") as f:
            start = json.load(f)["hooks"]["SessionStart"][0]["hooks"][0]
        self.assertEqual(start["command"], "python3")
        self.assertTrue(start["args"][0].endswith("scripts/print_document.py"))
        self.assertTrue(start["args"][1].endswith("discipline.md"))

    def test_the_discipline_carries_a_header_that_the_session_never_sees(self):
        with open(os.path.join(PLUGIN, "discipline.md"), encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("---\nstatus: "))
        out = run(os.path.join(PLUGIN, "discipline.md"))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(out.stdout.startswith("# Working discipline"))
        self.assertNotIn("status:", out.stdout.split("\n", 3)[0])

    def test_a_file_without_a_header_is_printed_whole(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Plain\n\n---\n\nA rule line above is not a header.\n")
        try:
            self.assertEqual(run(f.name).stdout, "# Plain\n\n---\n\nA rule line above is not a header.\n")
        finally:
            os.unlink(f.name)

    def test_windows_line_endings_are_handled(self):
        with tempfile.NamedTemporaryFile("wb", suffix=".md", delete=False) as f:
            f.write(b"---\r\nstatus: canon\r\n---\r\n\r\n# Title\r\n")
        try:
            self.assertEqual(run(f.name).stdout.strip(), "# Title")
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
