#!/usr/bin/env python3
"""Print a Markdown document without its status header.

The SessionStart hook uses this to give each session the working discipline:
the file carries a status header like every other document in the
repository, but the header is bookkeeping, not discipline, so the session
never sees it.

usage: print_document.py <path>
"""

import sys


def body(text):
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[0] == "---" and "---" in lines[1:]:
        end = lines.index("---", 1)
        lines = lines[end + 1 :]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines)


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        sys.stdout.write(body(f.read()))


if __name__ == "__main__":
    main()
