# nomad-method

<img src="plugin/.claude-plugin/icon.png" alt="nomad-method icon: a camel silhouette against a low sun, head turned back over its hump toward its own footprints" width="128">

A Claude Code plugin that makes a contributor's checks happen at the moments
they matter, instead of relying on anyone remembering to ask for them.

> **Extracted on 2026-10-22** from `tools/nomad-method` in
> RikhoKorp/NomadGameEngineV2, with its history (`git subtree split`). The
> method it carries is written down in
> [RikhoDev/NomadArchitecture](https://github.com/RikhoDev/NomadArchitecture),
> which uses this plugin on itself.

## What it promises, and what it does not

It promises that the checks run: the agent starts each session with the
working discipline, a commit that restates existing guidance is stopped once
and has to be resolved or acknowledged, and a review goes to a judge that
sees the change but not the author's reasoning.

It does **not** promise that the agent gets things right first time. In the
probes this comes from, the method worked by being wrong and corrected: most
corrections came from verification turns, and the best ones came from a human
who knew things the agent could not. The plugin can prompt that; it cannot
supply it. Someone who knows the work still has to contradict the agent when
it is wrong.

## What is in it

| Part | When it acts | What it does |
| --- | --- | --- |
| [Working discipline](plugin/discipline.md) | every session start (hook) | modes, verify hints, label status, hold and yield on evidence, keep canon small, compare with the base, authority |
| [Canon check](plugin/scripts/canon_check.py) | before any Bash command that commits (hook) | blocks once when added canon text restates existing canon; lists the matches. Finds the commit inside compound commands and follows `cd` and `git -C` to the repository being committed to |
| [`/nomad-method:review`](plugin/skills/review/SKILL.md) | on request, or when the agent is about to call a canon change done | author rereads the diff against the base, then hands a packet to the judge with a fixed prompt |
| [`judge` agent](plugin/agents/judge.md) | launched by review | read-only (Read, Grep, Glob); restatement, growth, unverified claims, status, contradiction, placement; then three questions |
| [`nomad_review_packet.py`](plugin/scripts/nomad_review_packet.py) | used by review | writes to a temporary directory: the diff including new files' contents, the stat, commit subjects, which canon list is in use, and every local ref's history (no commit bodies) |

The project's own instructions win where they conflict with the discipline.

## Install

```text
/plugin marketplace add RikhoDev/nomad-method
/plugin install nomad-method@nomad-method
```

From a local clone, use `/plugin marketplace add ./` instead. To try it for
one session without installing: `claude --plugin-dir ./plugin`.

Requirements: `git` and `python3` (standard library only) on `PATH`.

The plugin ships no `bin/` folder: claude.ai-hosted plugins may not, because
`bin/` executables join `PATH` without appearing on the admin approval
surface. Its scripts run only through the hooks and the review skill, which
call them by path.

### Upload to claude.ai

[dist/nomad-method-plugin.zip](dist/nomad-method-plugin.zip) is the plugin
folder zipped with its manifest at the archive root, ready to upload. It is a
build of `plugin/`; rebuild it after changing the plugin:

```bash
git archive --format=zip -o dist/nomad-method-plugin.zip HEAD:plugin
```

`claude plugin validate` does not read zips; unzip into an empty folder to
validate.

### Tell it what canon is

By default the canon check covers `AGENTS.md`, `CLAUDE.md`, Copilot
instruction files, `ARCHITECTURE.md` and ADR folders. To set your own, commit
a `.nomad-method/canon` file at the project root with one glob per line; it
replaces the defaults. [examples/nomadgameenginev2.canon](examples/nomadgameenginev2.canon)
is the list used for this repository.

### When the canon check blocks

The agent sees the matches and either replaces the restatement with a pointer
(or removes the older copy), or, when the repetition is intended, says why in
the commit message and adds the trailer `Canon-Check: reviewed`. The trailer
is visible in history, so a human can audit every override. The trailer is
only seen when it is in the command itself (`-m` or a heredoc), not in a
message file passed with `-F path`.

## Evidence

Everything below was run on 2026-10-21 with Claude Code 2.1.306. It is
evidence that the parts work as designed, not that they make contributors
better; see the limits.

- **Focused proof:** `python3 -m unittest discover -s tests`. Ten cases:
  restatement blocks (in place and in a new untracked file), a moved rule
  passes, new wording passes, link-only index lines are ignored, non-canon
  files are ignored, the trailer passes, project config replaces defaults,
  other commands and non-repositories pass, bad input fails open.
- **Replay against real history:** `tests/replay_history.sh <repo> --canon
  <file> <revs>` recreates the moment before each commit and runs the hook.
  - On the NomadGameEngineV2 method branch (22 commits): one block, on
    `890ec34c`, the commit where the author restated an existing authority
    rule in a new section. No reviewer, including a cross-family one, caught
    it; the author found it a day later by comparing the diff with `main`.
    The hook would have caught it at commit time.
  - On the last 78 canon-touching commits of that repository's `main`: one
    block, an ADR repeating a short sentence from the previous ADR. An
    earlier version with a 60% threshold and no link filter blocked 6 of 78;
    those cases set the current settings.
  - Run time: about 0.2 s per commit there.
- **Live sessions** (headless `claude -p --plugin-dir`, a throwaway repository):
  - The session received the discipline at start and could quote it.
  - Asked to add a section restating an existing rule and commit, the agent
    announced Change mode, noticed the duplication itself, was blocked once by
    the hook, recorded in the commit message that the human had asked for the
    repetition, added the trailer and told the human which copy to delete.
  - `/nomad-method:review` built the packet, passed the judge the fixed
    one-line prompt unchanged, and reported the judge verbatim beside its own
    reread. Both found the duplication independently and left the decision to
    the human. The agent's closing offer named the base commit as the one to
    revert: a slip of the kind the plugin does not catch.

### 0.2.0, from a field test on NomadArchitecture (2026-10-21)

A session used 0.1.0 to rework the NomadArchitecture repository through three
review loops. It found these problems in the plugin; each fix has a test.

- **The canon check never ran.** `"if": "Bash(git commit*)"` matches only
  commands that start with `git commit`. Agents usually commit with
  `cd <repo> && git add -A && git commit ...`. Observed live with Claude Code
  2.1.306 and `claude -p --plugin-dir`: a compound commit restating a rule at
  93% overlap went through, while a plain `git commit` was blocked. The
  script also read the session's directory, not the one the command entered.
  Fixed: no `if`; the script finds commits in compound commands and follows
  `cd` and `git -C`.
- **The review script did not run from the synced copy.** The copy installed
  from claude.ai had CRLF line endings, and bash rejected `set -o pipefail`.
  The committed zip is LF, so where the CRLF came from is unknown. Fixed: the
  script is now Python, which accepts either ending, and `.gitattributes` keeps
  LF in checkouts.
- **The judge could not see new files.** The packet listed untracked files by
  name only; on that session's first review, all five new canon files would
  have been invisible. Fixed: their contents are in `change.diff`.
- **The judge reported checkable history as unknown**, for example "this file
  never existed" or "this commit added that file". Fixed: `history.txt`.
- **A wrong argument failed obscurely.** Passing a description instead of a
  base ref ended in a git error. Fixed: a clear refusal.
- **The canon was not configured, silently.** Without `.nomad-method/canon`,
  the defaults covered none of NomadArchitecture's canon. Now `README.txt`
  names the canon list in use, and the judge flags guidance the defaults miss.
- **Delegated authority had no rule.** The human said "infer what I would deem
  canon … for the rest, you debate with yourself"; the author and the judge
  disagreed over whether the result was the human's decision. The discipline
  now says how to record a delegation.

Tests: `python3 -m unittest discover -s tests` now runs 19 cases. Nine were
added for the faults above, and each failed before its fix.

## Known limits

- The canon check matches wording, not meaning. A paraphrase of an existing
  rule passes; so does guidance that contradicts canon. (The NomadGameEngineV2
  doctrine amendment `38fd5892`, which contradicted existing doctrine and was
  later reverted, passes the hook.) That is the judge's job, and the human's.
- The judge sees commit subjects but not commit bodies, by design: bodies
  carry the author's reasoning. So it cannot see an authorization recorded
  there, and reports it as unknown.
- The judge cannot run git. It checks history claims against the packet's
  `history.txt`; what lies beyond it (a shallow clone's past, refs not
  fetched, commit bodies) stays unknown.
- The hook now runs for every Bash command and exits in about 40 ms when the
  command does not commit. A commit hidden from the parser, for example inside
  a script file or an `eval`, is not checked.
- The discipline is instruction text. In the probes, instruction text alone
  changed behaviour for asking what kind of answer is wanted (2 of 2) and for
  not rewriting an existing rule (2 of 2); small samples, one model family.
- Nothing here verifies hints the human offers. The discipline asks for it;
  only the agent's tool use can do it, and only the human knows which hints
  were wrong.

## Origin

Drawn from the method probes recorded in NomadGameEngineV2
dossier 2610-85 (NomadGameEngineV2: `Engine/__Docs/Dossiers/2610-85-Method-Hypothesis-And-Behaviour-Probe.md`, on its method branch).
Each part answers a learning there:

- the discipline: "understanding is not action";
- the canon check: the author's own H4 miss;
- the judge's isolation: the clean-channel note;
- the three questions: the recursion step.

That repository is private; the reference is kept as provenance.

## Icon

![nomad-method icon at full size](plugin/.claude-plugin/icon.png)

**Purpose.** The plugin's listing icon; the validator looks for it at
`plugin/.claude-plugin/icon.png`. **Original:**
[icon.svg](plugin/.claude-plugin/icon.svg), hand-written vector; the PNG is a
1024 px render of it.

A camel looking back over its shoulder at its own tracks: thinking shown as
checking, after the plugin's best-evidenced check, comparing your change with
the base. The design went through the method: the first idea, a camel with a
thought bubble, did not survive the 32 px size at which plugin lists show it;
the first drafts read as a llama, then a bear, and were redrawn.

To re-render after editing the SVG, open it at 1024 × 1024 in a browser (for
example headless Chromium with `--screenshot`) and save as PNG. Limits: drawn
by an AI contributor, not a designer; checked by eye at 1024, 48 and 32 px
only.

## Testing a colleague's setup

Run the dossier's probe protocol in a fresh session, with and without the
plugin, and compare per-claim behaviour. Do not tell the session it is a
test. One run is an observation, not a rate.
