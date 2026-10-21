"""Focused proof for plugin/scripts/canon_check.py.

Run: python3 -m unittest discover -s tests   (from the nomad-method root)
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "canon_check.py")

RULE = (
    "Agents may map evidence and propose a bounded change; new canonical policy "
    "requires explicit human authorization before it is applied anywhere."
)
OTHER = "Prefer a coherent semantic neighbourhood over fewer files or a convenient bucket."


def run_hook(cwd, command="git commit -m x"):
    payload = json.dumps({"cwd": cwd, "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True
    )
    return result.returncode, result.stderr


class CanonCheckTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = self.dir.name
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.write("AGENTS.md", f"# Guide\n\n## Change\n\n{RULE}\n\n## Other\n\n{OTHER}\n")
        self.write("notes.md", "Scratch.\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")

    def tearDown(self):
        self.dir.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", self.root, *args], check=True, capture_output=True)

    def write(self, path, text):
        full = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def test_restating_an_existing_rule_blocks(self):
        self.write(
            "AGENTS.md",
            f"# Guide\n\n## Both modes\n\n- {RULE}\n\n## Change\n\n{RULE}\n\n## Other\n\n{OTHER}\n",
        )
        code, err = run_hook(self.root)
        self.assertEqual(code, 2)
        self.assertIn("AGENTS.md:5", err)
        self.assertIn("restates AGENTS.md:9", err)

    def test_restatement_in_a_new_canon_file_blocks(self):
        self.write("docs/adr/0001-x.md", f"# ADR\n\n{RULE}\n")
        code, err = run_hook(self.root)
        self.assertEqual(code, 2)
        self.assertIn("docs/adr/0001-x.md", err)

    def test_moving_a_rule_is_not_a_restatement(self):
        self.write("AGENTS.md", f"# Guide\n\n## Both modes\n\n{RULE}\n\n## Other\n\n{OTHER}\n")
        self.assertEqual(run_hook(self.root)[0], 0)

    def test_new_wording_passes(self):
        self.write(
            "AGENTS.md",
            f"# Guide\n\n## Change\n\n{RULE}\n\nAsk what kind of answer is wanted when an open request does not say.\n\n## Other\n\n{OTHER}\n",
        )
        self.assertEqual(run_hook(self.root)[0], 0)

    def test_link_only_index_lines_are_ignored(self):
        link = "- [ADRs/0002-explicit-ontology-pack-and-proof-status-schema.md](ADRs/0002-explicit-ontology-pack-and-proof-status-schema.md)"
        self.write("AGENTS.md", f"# Guide\n\n{link}\n\n## Change\n\n{RULE}\n\n## Other\n\n{OTHER}\n")
        self.git("commit", "-qam", "index")
        self.write("CLAUDE.md", f"# Index\n\n{link}\n")
        self.assertEqual(run_hook(self.root)[0], 0)

    def test_non_canon_files_are_not_checked(self):
        self.write("notes.md", f"{RULE}\n")
        self.assertEqual(run_hook(self.root)[0], 0)

    def test_reviewed_trailer_lets_the_commit_through(self):
        self.write("CLAUDE.md", f"{RULE}\n")
        command = f"git commit -m 'Repeat on purpose' -m 'Canon-Check: reviewed'"
        self.assertEqual(run_hook(self.root, command)[0], 0)

    def test_project_canon_config_replaces_defaults(self):
        self.write(".nomad-method/canon", "# only docs\ndocs/*.md\n")
        self.git("add", ".")
        self.git("commit", "-qm", "config")
        self.write("CLAUDE.md", f"{RULE}\n")
        self.assertEqual(run_hook(self.root)[0], 0)  # CLAUDE.md no longer canon
        self.write("docs/rules.md", f"{OTHER} It also says more words here.\n")
        self.git("add", "docs/rules.md")
        self.git("commit", "-qm", "docs")
        self.write("docs/more.md", f"{OTHER}\n")
        self.assertEqual(run_hook(self.root)[0], 2)

    def test_other_commands_and_non_repositories_pass(self):
        self.write("CLAUDE.md", f"{RULE}\n")
        self.assertEqual(run_hook(self.root, "git status")[0], 0)
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(run_hook(empty)[0], 0)

    def test_compound_command_checks_the_repository_it_enters(self):
        # The agent's shell often runs `cd <repo> && git add -A && git commit`,
        # from a session whose own working directory is somewhere else.
        self.write("CLAUDE.md", f"{RULE}\n")
        with tempfile.TemporaryDirectory() as elsewhere:
            command = f"cd {self.root} && git add -A && git commit -q -m x"
            code, err = run_hook(elsewhere, command)
        self.assertEqual(code, 2)
        self.assertIn("CLAUDE.md", err)

    def test_git_dash_c_checks_the_named_repository(self):
        self.write("CLAUDE.md", f"{RULE}\n")
        with tempfile.TemporaryDirectory() as elsewhere:
            code, _ = run_hook(elsewhere, f"git -C {self.root} commit -m x")
        self.assertEqual(code, 2)

    def test_hook_is_not_limited_to_commands_that_start_with_git_commit(self):
        # Claude Code matches `if: Bash(git commit*)` against the start of the
        # command, so compound commands skipped the check (observed live with
        # Claude Code 2.1.306). The script does its own filtering.
        hooks = os.path.join(os.path.dirname(HOOK), "..", "hooks", "hooks.json")
        with open(hooks, encoding="utf-8") as f:
            entries = json.load(f)["hooks"]["PreToolUse"]
        canon = [h for e in entries for h in e["hooks"] if "canon_check.py" in " ".join(h.get("args", []))]
        self.assertEqual(len(canon), 1)
        self.assertNotIn("if", canon[0])

    def test_bad_input_fails_open(self):
        result = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
