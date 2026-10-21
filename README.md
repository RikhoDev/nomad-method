# nomad-method

A Claude Code plugin that makes a contributor's checks happen at the moments
they matter, instead of relying on anyone remembering to ask for them.

> **Staged here for extraction.** This folder is a self-contained side project
> (plugin, marketplace, tests). It is not engine source and nothing in the
> repository depends on it. Lift the folder out as the root of its own
> repository; no paths need to change.

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
| [Canon check](plugin/scripts/canon_check.py) | before any `git commit` (hook) | blocks once when added canon text restates existing canon; lists the matches |
| [`/nomad-method:review`](plugin/skills/review/SKILL.md) | on request, or when the agent is about to call a canon change done | author rereads the diff against the base, then hands a packet to the judge with a fixed prompt |
| [`judge` agent](plugin/agents/judge.md) | launched by review | read-only (Read, Grep, Glob); restatement, growth, unverified claims, status, contradiction, placement; then three questions |
| [`nomad-review-packet`](plugin/bin/nomad-review-packet) | used by review | writes the diff, stat and commit subjects to a temporary directory |

The project's own instructions win where they conflict with the discipline.

## Install

From a clone of this repository (or of the extracted side project):

```text
/plugin marketplace add ./tools/nomad-method
/plugin install nomad-method@nomad-method
```

Once extracted to its own GitHub repository, use
`/plugin marketplace add <owner>/<repo>` instead. To try it for one session
without installing: `claude --plugin-dir ./tools/nomad-method/plugin`.

Requirements: `git`, `python3` (standard library only) and `bash` on `PATH`.

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

## Known limits

- The canon check matches wording, not meaning. A paraphrase of an existing
  rule passes; so does guidance that contradicts canon. (The NomadGameEngineV2
  doctrine amendment `38fd5892`, which contradicted existing doctrine and was
  later reverted, passes the hook.) That is the judge's job, and the human's.
- The judge sees commit subjects but not commit bodies, by design: bodies
  carry the author's reasoning. So it cannot see an authorization recorded
  there, and reports it as unknown.
- The judge cannot run git; claims about history it could not check are
  unknowns.
- The discipline is instruction text. In the probes, instruction text alone
  changed behaviour for asking what kind of answer is wanted (2 of 2) and for
  not rewriting an existing rule (2 of 2); small samples, one model family.
- Nothing here verifies hints the human offers. The discipline asks for it;
  only the agent's tool use can do it, and only the human knows which hints
  were wrong.

## Origin

Drawn from the method probes recorded in NomadGameEngineV2
[dossier 2610-85](../../Engine/__Docs/Dossiers/2610-85-Method-Hypothesis-And-Behaviour-Probe.md).
Each part answers a learning there:

- the discipline: "understanding is not action";
- the canon check: the author's own H4 miss;
- the judge's isolation: the clean-channel note;
- the three questions: the recursion step.

After extraction, that link will break; keep it as provenance.

## Testing a colleague's setup

Run the dossier's probe protocol in a fresh session, with and without the
plugin, and compare per-claim behaviour. Do not tell the session it is a
test. One run is an observation, not a rate.
