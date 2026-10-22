---
status: non-canon
kind: trail
origin: ai-assisted
trail_of: ../../README.md
---

# NomadArchitecture's canon, applied to nomad-method

> **Context:** nomad-method was extracted from NomadGameEngineV2 on 2026-10-22.
> The human then asked for "step 4 first, then 3". Step 3 was the assistant's
> proposal: make this repository the second consumer of
> [NomadArchitecture](https://github.com/RikhoDev/NomadArchitecture)'s canon,
> record where the canon does not fit a Claude Code plugin, and change neither
> side to hide a misfit.
> **Author:** Claude Code, for Eric (Shaman).

NomadArchitecture's canon is cited as `NA:` paths at its commit `937eddc`.

## How it was tried

NomadArchitecture's own tools were copied, unchanged, into a scratch copy of
this repository and run there: `Scripts/Test-Repository.ps1` and the
DocReader Host. Then each canon rule was applied by hand.

The trial first found two bugs in NomadArchitecture's tools, not in this
repository:
- the check crashed when a canon list or canon index was missing;
- the reader took the README's `<img>` icon line as its opening sentence.

Both are fixed there, with proofs, in `937eddc`.

## What fits, and was adopted

- **Canon list.** `.nomad-method/canon` names the plugin's binding texts:
  `discipline.md`, `agents/judge.md` and `skills/review/SKILL.md`. Before this,
  the plugin's own commit check covered none of them, because they match none
  of its default globs. Copying a sentence from `discipline.md` into
  `judge.md` is now blocked at commit; this was tried in a scratch copy.
  (NA:`__Docs/README.md#how-canon-grows`)
- **Status headers, merged into the platform's front matter.** `judge.md` and
  `SKILL.md` must begin with Claude Code's own YAML front matter (`name`,
  `description`, `tools`). NomadArchitecture's `status`, `kind` and `origin`
  were added to that same block, and `claude plugin validate` still passes.
  They are `status: proposed`, because their 0.2.0 changes, including a new
  sentence on delegated authority in `discipline.md`, have not been accepted
  by the human. Publishing 0.2.0 would be that acceptance.
  (NA:`__Docs/README.md#status-header`)
- **Trails.** This file lives in `__Docs/_Trails/`, is named for its owner and
  names it in `trail_of:`. (NA:`__Docs/README.md#trails-hold-the-conversation`)
- **Evidence and authority.** The README's Evidence and Known limits sections
  already keep what was run apart from what is claimed, and say what the
  plugin cannot do. (NA:`__Docs/Evidence-And-Authority.md`)

Reading the files to merge the headers also found a stale name from 0.2.0:
the judge's description still said "written by nomad-review-packet". It now
names `nomad_review_packet.py`.

## What does not fit, recorded rather than forced

1. **The platform decides the first folders.** Claude Code requires
   `.claude-plugin/`, `hooks/`, `agents/`, `skills/<name>/SKILL.md`, and in
   practice `scripts/`. These are folders named for technologies, which is
   what the Explorer test warns against
   (NA:`__Docs/Architecture.md#placement`). Moving them would break the
   plugin. NomadArchitecture's own source of the test says to "record the
   contradiction as evidence and correct the doctrine"
   (NGE:`Engine/__Docs/Patterns/Feature-Sovereignty-Doctrine.md`).
   *Proposal for NomadArchitecture, the human's to decide:* a layout that the
   Host platform requires belongs to the Host. Meaning is then placed beneath
   or beside it, and the placement test applies from there.
2. **A file the platform injects verbatim cannot carry a header.** The
   SessionStart hook prints `discipline.md` into every session as it is. A
   status header would print YAML into every agent's context. It is listed in
   `.nomad-method/canon` but has no header.
   *Options:* the hook strips front matter before printing, or the canon lets
   a canon list stand in for a header on such files.
3. **The canon index is NomadArchitecture's own.** Its check requires a
   `__Docs/README.md` with a `## Canon` list that agrees with the headers and
   with `.nomad-method/canon`. This repository has no such index;
   `.nomad-method/canon` is enough here. The three-list agreement does not
   travel; the canon list does.
4. **Folder grammar against language habits.** `tests/`, `dist/` and
   `examples/` are structural folders without the `_` prefix
   (NA:`__Docs/README.md#folder-grammar`). `tests/` is also what
   `python3 -m unittest discover -s tests` expects by habit. Not renamed:
   nothing is gained but conformity, and the README's commands would change.
5. **Feature READMEs.** The three parts (discipline, canon check, review) have
   no README each; the root README's table describes all three. That fits
   "parents summarise and link", but not the per-Feature README rule
   (NA:`__Docs/Architecture.md#feature-readme`, itself still awaiting the
   human's reading).
6. **The tools need PowerShell.** NomadArchitecture's check and reader run on
   `pwsh`; this repository's tooling is Python. They ran here only because
   `pwsh` was installed by hand. A canon that wants second consumers may need
   its checks in the consumer's language, or a portable one.

## Promotion evidence, not acted on

`scripts/canon_check.py` and `scripts/nomad_review_packet.py` each define a
`git()` helper. That makes two consumers, but they differ:
- one raises on any failure;
- the other makes failure optional, uses explicit encoding, and reports
  git's error text.

By the promotion rule (NA:`__Docs/Architecture.md#promotion`), these are
realization and policy differences to classify, not a conflict, and the
saving would be a few lines. Not promoted.

## What this says about the canon

Of the canon's rules, the canon list, status headers, Trails, the placement
test's spirit, and evidence and authority carried over. The rest met a
platform or language convention first: the first folders, files consumed
verbatim, the canon index, the `_` prefix and the tooling language. Each
misfit above is a candidate amendment for NomadArchitecture, for the human to
accept or reject. None was made there.
