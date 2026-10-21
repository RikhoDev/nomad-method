"""Focused proof for plugin/scripts/nomad_review_packet.py.

Run: python3 -m unittest discover -s tests   (from the nomad-method root)
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PACKET = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "nomad_review_packet.py")


class ReviewPacketTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = self.dir.name
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "ada@example.com")
        self.git("config", "user.name", "Ada")
        self.write("AGENTS.md", "# Guide\n\nOne rule.\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Base guidance")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.write("AGENTS.md", "# Guide\n\nOne rule, amended.\n")
        self.git("commit", "-qam", "Amend the rule")
        self.write("docs/new-rule.md", "A brand new rule nobody has seen.\n")

    def tearDown(self):
        self.dir.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root, *args], check=True, capture_output=True, text=True).stdout

    def write(self, path, text):
        full = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def run_packet(self, *args, script=PACKET):
        return subprocess.run([sys.executable, script, *args], cwd=self.root, capture_output=True, text=True)

    def packet(self, *args):
        result = self.run_packet(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = result.stdout.strip()
        self.addCleanup(shutil.rmtree, path, True)
        read = lambda name: open(os.path.join(path, name), encoding="utf-8").read()
        return read

    def test_new_files_are_in_the_diff_with_their_contents(self):
        read = self.packet(self.base)
        self.assertIn("A brand new rule nobody has seen.", read("change.diff"))
        self.assertIn("docs/new-rule.md", read("untracked.txt"))

    def test_history_lets_the_judge_check_claims_without_git(self):
        read = self.packet(self.base)
        history = read("history.txt")
        self.assertIn("Amend the rule", history)
        self.assertIn("Base guidance", history)
        self.assertIn("Ada", history)
        self.assertIn("AGENTS.md", history)  # files touched, so "never existed" is checkable

    def test_readme_names_the_base_and_the_canon_in_use(self):
        read = self.packet(self.base)
        readme = read("README.txt")
        self.assertIn("Amend the rule", readme)
        self.assertIn("canon: built-in defaults", readme)
        self.write(".nomad-method/canon", "docs/*.md\n")
        self.assertIn("canon: .nomad-method/canon", self.packet(self.base)("README.txt"))

    def test_a_base_that_is_not_a_ref_is_refused_clearly(self):
        result = self.run_packet("review the canon change please")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a git revision", result.stderr)

    def test_default_base_is_found_without_arguments(self):
        read = self.packet()
        self.assertIn("base:", read("README.txt"))

    def test_survives_windows_line_endings(self):
        # The synced copy of v0.1.0 arrived with CRLF endings, which broke the
        # bash version of this script. The Python version must not care.
        with open(PACKET, encoding="utf-8") as f:
            crlf = f.read().replace("\n", "\r\n")
        copy = os.path.join(self.root, "packet_crlf.py")
        with open(copy, "w", encoding="utf-8", newline="") as f:
            f.write(crlf)
        result = self.run_packet(self.base, script=copy)
        self.assertEqual(result.returncode, 0, result.stderr)
        shutil.rmtree(result.stdout.strip(), True)


if __name__ == "__main__":
    unittest.main()
