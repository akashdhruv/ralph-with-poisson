## Experiment: Ralph-style loop harness + CodeScribe loop mode

This repo is an experiment in running repeated “fresh session” coding-agent iterations over a single task prompt.

Key files:

- `prompt.toml` — the task file used by CodeScribe loop mode
- `ralph-loop.sh` — a small external harness for testing different coding agents (e.g. opencode, Pi, etc.) and for CodeScribe-specific special tests

## Run with CodeScribe (recommended)

Install and configure **CodeScribe** first. See:

- https://github.com/Lab-Notebooks/CodeScribe

Then, from this repo root, run the bounded fresh-session loop:

```bash
code-scribe loop prompt.toml -m oaic-gpt54 -v -niter 30 -nloop 20
```

- `-niter` — max iterations per loop session
- `-nloop` — max number of loop sessions
- Stop early with `Ctrl+C`.
- Each loop is split into an **execution** phase (agent writes code) and a **review** phase (agent records progress).
- Loop artifacts (status + report) are written under `.codescribe/loop/`.

## Run via the generic loop harness (multi-agent testing)

Use `ralph-loop.sh` when you want to test the same loop idea with other coding-agent frontends (opencode, Pi, etc.), or when you’re doing special-case CodeScribe testing:

```bash
./ralph-loop.sh
```

Stop with `Ctrl+C`.

## References

- [Ralph Wiggum as a “software engineer”](https://ghuntley.com/ralph) — The original blog post explaining the Ralph technique

## License

MIT — see `LICENSE`.
