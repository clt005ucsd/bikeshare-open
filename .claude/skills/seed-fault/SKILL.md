---
name: seed-fault
description: Seed one known fault into the pipeline, confirm the suite goes red, then restore it
---

1. Take the fault description from `$ARGUMENTS`.
2. Run `git stash list` and `git status --porcelain --untracked-files=no`; refuse if that prints anything (modified tracked files). Untracked files are fine.
3. Make the single smallest edit that introduces the fault.
4. Run `make test` and show the last 5 lines.
5. Restore with `git checkout -- <edited_file>` and run `make test` again to show green.
6. Print one line: `fault, file:line, red/green result`.

*Never edit `data/raw/` or `tests/`. Do not commit the changes.*