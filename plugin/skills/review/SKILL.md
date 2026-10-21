---
name: review
description: Review your own change before calling it done - reread it against the base, then hand it to an isolated judge that sees the change but not your reasoning. Use before committing or reporting a change to guidance, architecture docs or other canon as finished, and whenever the human asks for a review.
argument-hint: "[base-ref]"
---

# Review a change: self-check, then isolated judge

The order matters. Your own reread of the diff against the base is the check
that has caught problems no reviewer did; the judge catches what you cannot
see because you know why you did it.

## 1. Build the packet

Commit or stage nothing new for this; review what exists. Run:

```bash
nomad-review-packet $ARGUMENTS
```

It prints a directory. Note the path.

## 2. Reread it yourself

Read `change.diff` in that directory as if someone else wrote it. For every
added piece of guidance, search the repository for an existing statement of
the same rule. For every factual claim, find the file or commit that confirms
it. Write down, briefly, what you would now change. Do not fix anything yet.

## 3. Hand it to the judge

Launch the `judge` subagent from this plugin with exactly this prompt,
replacing only `<PACKET>` with the directory path. Add nothing: no summary,
no intent, no reasons. The judge must not be steered by the author.

```text
Review the change in the packet at <PACKET>.
```

## 4. Report to the human

Give the human, in this order:

1. The judge's report, verbatim.
2. Your own reread from step 2.
3. Where you and the judge disagree, your evidence for each side.
4. What you propose to change, and what you would delete.

Then stop. The human decides what is accepted. Do not apply your proposals in
the same turn unless the human has already said to.
