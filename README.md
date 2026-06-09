## Experiment: Ralph-style loop harness + CodeScribe loop mode

This repo is an experiment in running repeated “fresh session” coding-agent iterations over a single task prompt.

Key files:

- `specification.toml` — the task file used by CodeScribe loop mode
- `ralph-loop.sh` — a small external harness for testing different coding agents (e.g. opencode, Pi, etc.) and for CodeScribe-specific special tests

## CodeScribe Quickstart

**1. Install CodeScribe**

See the [CodeScribe README](https://github.com/Lab-Notebooks/CodeScribe) for installation and setup.

**2. Run the bounded fresh-session loop**

From this repo root:

```bash
code-scribe loop specification.toml -m oaic-gpt54 -v -niter 30 -nloop 20
```

- `-niter` — max iterations per loop session
- `-nloop` — max number of loop sessions
- Stop early with `Ctrl+C`.

Sample output:

```
▶  loop 1 [execution]
  iter 1
    │ Let me start by reading the task file and understanding the current state of the project.
    usage  in 2,517  out 162  total 2,679
    ▸ read   specification.toml
    ▸ bash   find . -type f -not -path './.git/*' ...   exit_code=0
  iter 2
    usage  in 4,481  out 69  total 4,550
    ▸ read   PLAN.md
  iter 3
    │ Now I understand the current state. The most important first step is to create the
    │ project structure and implement the Grid class, as everything else depends on it.
    usage  in 5,030  out 709  total 5,739
    ▸ write  generated-src/poisson/__init__.py
    ▸ write  generated-src/poisson/grid.py
    ▸ write  generated-src/poisson/solvers.py
  iter 4
    usage  in 9,675  out 1,222  total 10,897
    ▸ write  generated-src/tests/__init__.py
    ▸ write  generated-src/tests/test_poisson.py
```

**3. How it works**

Each loop session opens a fresh agent context with `specification.toml` as the prompt. The agent reads `PLAN.md`, picks the highest-priority remaining task, implements it, then lists what remains. On the next loop a new session begins from the same prompt — no memory carries over, only the files the agent wrote.

- **Execution phase** — agent writes code under `generated-src/`
- **Review phase** — agent records progress
- Loop artifacts (status + report) land under `.codescribe/loop/`

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
