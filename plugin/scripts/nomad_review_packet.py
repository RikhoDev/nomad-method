#!/usr/bin/env python3
"""Write a review packet (the change and nothing about the author's reasoning)
and print its directory.

usage: nomad_review_packet.py [base-ref]
The base defaults to the merge base with origin/HEAD, then origin/main, main,
origin/master, master.

The packet holds:
  README.txt     repository, base, head, commit subjects, the canon in use
  stat.txt       git diff --stat against the base
  change.diff    the diff against the base, including the full contents of
                 new (untracked) files
  untracked.txt  the new files, by name
  history.txt    commits on every local ref (hash, date, author, subject,
                 files touched), so the judge can check claims about history
                 without running git. Commit bodies are left out on purpose:
                 they carry the author's reasoning.

Written in Python rather than shell so that it survives CRLF line endings.
"""

import os
import subprocess
import sys
import tempfile

HISTORY_LIMIT = 400


def git(root, *args, check=True):
    result = subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def resolve_base(root, requested):
    if requested:
        if git(root, "rev-parse", "-q", "--verify", f"{requested}^{{commit}}", check=False).strip():
            return requested
        sys.exit(
            f"nomad-review-packet: '{requested}' is not a git revision. "
            "Pass a base ref (a branch, tag or commit), or nothing to use the default."
        )
    for candidate in ("origin/HEAD", "origin/main", "main", "origin/master", "master"):
        if git(root, "rev-parse", "-q", "--verify", candidate, check=False).strip():
            return git(root, "merge-base", "HEAD", candidate).strip()
    sys.exit("nomad-review-packet: no base found; pass one.")


def untracked_diff(root, path):
    # `git diff --no-index` exits 1 when files differ; that is the normal case.
    result = subprocess.run(
        ["git", "-C", root, "diff", "--no-index", "--", os.devnull, path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return result.stdout


def main():
    try:
        root = git(os.getcwd(), "rev-parse", "--show-toplevel").strip()
    except RuntimeError:
        sys.exit("nomad-review-packet: not inside a git repository.")
    base = resolve_base(root, sys.argv[1] if len(sys.argv) > 1 else "")
    packet = tempfile.mkdtemp(prefix="nomad-review.")

    def write(name, text):
        with open(os.path.join(packet, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    canon_file = os.path.join(root, ".nomad-method", "canon")
    canon = (
        "canon: .nomad-method/canon"
        if os.path.isfile(canon_file)
        else "canon: built-in defaults (no .nomad-method/canon in this repository)"
    )
    shallow = git(root, "rev-parse", "--is-shallow-repository", check=False).strip() == "true"
    write(
        "README.txt",
        "\n".join(
            [
                f"repository: {root}",
                f"base: {git(root, 'rev-parse', '--short', base).strip()} ({git(root, 'log', '-1', '--format=%s', base).strip()})",
                f"head: {git(root, 'rev-parse', '--short', 'HEAD').strip()}",
                canon,
                "",
                "commits since base (subjects only):",
                git(root, "log", "--format=- %h %s", f"{base}..HEAD").rstrip(),
                "",
            ]
        ),
    )
    write("stat.txt", git(root, "diff", "--stat", base))
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    write("untracked.txt", "".join(f"{p}\n" for p in untracked))
    write("change.diff", git(root, "diff", base) + "".join(untracked_diff(root, p) for p in untracked))

    refs = git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes").split()
    log = git(
        root, "log", f"-n{HISTORY_LIMIT}", "--date=short", "--name-status",
        "--format=%n%h %ad %an | %s", *refs, "HEAD",
    )
    count = int(git(root, "rev-list", "--count", *refs, "HEAD").strip() or 0)
    header = [
        f"refs: {', '.join(refs) or 'HEAD'}",
        f"commits: {count}" + (f", the newest {HISTORY_LIMIT} shown" if count > HISTORY_LIMIT else ", all shown"),
        "clone: shallow; history before its first commit is unknown" if shallow else "clone: full",
        "Each commit: hash date author | subject, then the files it added (A), modified (M), deleted (D) or renamed (R).",
    ]
    write("history.txt", "\n".join(header) + "\n" + log)
    print(packet)


if __name__ == "__main__":
    main()
