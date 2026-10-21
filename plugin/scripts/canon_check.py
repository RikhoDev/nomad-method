#!/usr/bin/env python3
"""PreToolUse hook: before `git commit`, flag new canon text that restates
canon already present.

Compares sentences added to canon files (working tree against HEAD) with the
rest of the canon as it will stand after the change. A restatement blocks the
commit once, with the matches listed. The agent either points to the existing
rule instead, or records that it looked by adding the trailer
`Canon-Check: reviewed` to the commit message.

Fails open: anything unexpected (no repository, no HEAD, bad input) allows
the commit. The check makes the agent look; it does not judge.

Canon is configured per project in `.nomad-method/canon` (one glob per line,
`#` for comments). Without that file, DEFAULT_CANON applies.
"""

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

DEFAULT_CANON = [
    "AGENTS.md",
    "**/AGENTS.md",
    "CLAUDE.md",
    "**/CLAUDE.md",
    ".github/copilot-instructions.md",
    ".github/instructions/*.md",
    "**/ARCHITECTURE.md",
    "**/ADR*/*.md",
    "**/adr/*.md",
    "**/adrs/*.md",
]
REVIEWED_TRAILER = "Canon-Check: reviewed"
MIN_WORDS = 8
THRESHOLD = 0.7
MAX_REPORTED = 8


def git(root, *args):
    return subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, check=True
    ).stdout


def canon_globs(root):
    try:
        with open(f"{root}/.nomad-method/canon", encoding="utf-8") as f:
            globs = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            return globs or DEFAULT_CANON
    except OSError:
        return DEFAULT_CANON


def is_canon(path, globs):
    # fnmatch's "*" crosses "/", so "**/X" also needs the root-level form.
    return any(
        fnmatch.fnmatch(path, g) or (g.startswith("**/") and fnmatch.fnmatch(path, g[3:]))
        for g in globs
    )


def normalize(text):
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown links
    text = re.sub(r"[`*_>#|]", " ", text.lower())
    return re.findall(r"[a-z0-9']+", text)


def sentences(lines):
    """Yield (start_line, words) for each sentence in numbered lines.

    Wrapped Markdown lines are joined; blank lines, headings, list markers and
    table rows end a sentence.
    """
    buf, start = [], None

    def flush():
        joined = " ".join(buf)
        for part in re.split(r"(?<=[.;:!?])\s+", joined):
            words = normalize(part)
            # A line that is mostly a link (an index entry) is not a rule.
            prose = normalize(re.sub(r"\[[^\]]*\]\([^)]*\)", " ", part))
            if len(prose) >= MIN_WORDS:
                yield start, words

    for number, line in lines:
        stripped = line.strip()
        boundary = (
            not stripped
            or stripped.startswith(("#", "|", "```"))
            or re.match(r"^([-*+]|\d+\.)\s", stripped)
        )
        if boundary and buf:
            yield from flush()
            buf, start = [], None
        if stripped and not stripped.startswith(("#", "|", "```")):
            if start is None:
                start = number
            buf.append(re.sub(r"^([-*+]|\d+\.)\s+", "", stripped))
    if buf:
        yield from flush()


def trigrams(words):
    return {tuple(words[i : i + 3]) for i in range(len(words) - 2)}


def added_lines(root, paths):
    """Map path -> {new_line_number: text} for lines added since HEAD."""
    diff = git(root, "diff", "HEAD", "-U0", "--no-color", "--", *paths)
    added, path, number = {}, None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            number = int(re.search(r"\+(\d+)", line).group(1))
        elif path and line.startswith("+"):
            added.setdefault(path, {})[number] = line[1:]
            number += 1
    return added


def find_restatements(root):
    globs = canon_globs(root)
    tracked = git(root, "ls-files").splitlines()
    changed = git(root, "diff", "HEAD", "--name-only").splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    canon = sorted({p for p in tracked + untracked if is_canon(p, globs)})
    changed_canon = [p for p in changed if p in canon]
    new_files = [p for p in untracked if p in canon]
    if not changed_canon and not new_files:
        return []

    # Untracked files may be added in the same command as the commit; every
    # line in them is new.
    added = added_lines(root, changed_canon) if changed_canon else {}
    for path in new_files:
        try:
            with open(f"{root}/{path}", encoding="utf-8") as f:
                added[path] = dict(enumerate(f.read().splitlines(), 1))
        except (OSError, UnicodeDecodeError):
            pass
    corpus = []  # (path, line, trigram set) of canon text that is not new
    new = []  # (path, line, words) of added canon text
    for path in canon:
        try:
            with open(f"{root}/{path}", encoding="utf-8") as f:
                content = f.read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        mine = added.get(path, {})
        old = [(n, l) for n, l in enumerate(content, 1) if n not in mine]
        corpus += [(path, n, trigrams(w)) for n, w in sentences(old)]
        new += [(path, n, w) for n, w in sentences(sorted(mine.items()))]

    found = []
    for path, line, words in new:
        grams = trigrams(words)
        best = max(
            ((len(grams & g) / len(grams), p, n) for p, n, g in corpus if g),
            default=(0, None, None),
        )
        if best[0] >= THRESHOLD:
            found.append((path, line, " ".join(words), best[1], best[2], best[0]))
    return found


SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")", "\n"}


def commit_dirs(command, cwd):
    """Directories in which `command` runs `git commit`.

    Follows `cd <dir>` and `git -C <dir>` through compound commands such as
    `cd repo && git add -A && git commit -m ...`, so the check looks at the
    repository being committed to, not the session's working directory.
    """
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    tokens = list(lexer)
    dirs, here, i = [], cwd, 0
    while i < len(tokens):
        start = i == 0 or tokens[i - 1] in SEPARATORS
        word = tokens[i]
        if start and word == "cd" and i + 1 < len(tokens) and tokens[i + 1] not in SEPARATORS:
            here = os.path.normpath(os.path.join(here, os.path.expanduser(tokens[i + 1])))
            i += 2
            continue
        if start and word == "git":
            j, where = i + 1, here
            while j < len(tokens) and tokens[j] not in SEPARATORS:
                if tokens[j] == "-C" and j + 1 < len(tokens):
                    where = os.path.normpath(os.path.join(where, os.path.expanduser(tokens[j + 1])))
                    j += 2
                elif tokens[j] in ("-c", "--git-dir", "--work-tree") and j + 1 < len(tokens):
                    j += 2
                elif tokens[j].startswith("-"):
                    j += 1
                else:
                    if tokens[j] == "commit":
                        dirs.append(where)
                    break
            i = j
            continue
        i += 1
    return dirs


def main():
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
        if "commit" not in command or REVIEWED_TRAILER in command:
            return 0
        cwd = payload.get("cwd") or "."
        try:
            dirs = commit_dirs(command, cwd)
        except ValueError:  # unbalanced quotes: fall back to the session's directory
            dirs = [cwd] if re.search(r"\bgit\b.*\bcommit\b", command) else []
        found = []
        for root in dict.fromkeys(git(d, "rev-parse", "--show-toplevel").strip() for d in dirs):
            git(root, "rev-parse", "--verify", "HEAD")
            found += find_restatements(root)
    except Exception:  # fail open: the check prompts a look, it never wedges work
        return 0
    if not found:
        return 0

    report = [
        "nomad-method canon check: new canon text closely restates existing canon.",
        "",
    ]
    for path, line, text, other, other_line, score in found[:MAX_REPORTED]:
        report.append(f"- {path}:{line} \"{text[:120]}\"")
        report.append(f"  restates {other}:{other_line} ({score:.0%} overlap)")
    if len(found) > MAX_REPORTED:
        report.append(f"- ... and {len(found) - MAX_REPORTED} more")
    report += [
        "",
        "Point to the existing rule instead of restating it, or remove the older",
        "copy. If the repetition is intended, say why in the commit message and add",
        f"the trailer '{REVIEWED_TRAILER}'.",
    ]
    print("\n".join(report), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
