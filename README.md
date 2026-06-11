## Experiment: Ralph-style loop harness + CodeScribe loop mode

This repo is an experiment in running repeated “fresh session” coding-agent iterations over a single task prompt.

Key files:

- `Spec.toml` — task file for CodeScribe; points the agent at `SPEC.md`, `AGENTS.md`, and `PLAN.md`
- `SPEC.md` — technical specification for the Poisson solver
- `AGENTS.md` — repo restrictions for agents
- `PLAN.md` — task checklist; agents mark tasks done as they implement them
- `ralph-loop.sh` — external harness for testing other coding-agent frontends (opencode, Pi, etc.)

## CodeScribe Quickstart

**1. Install CodeScribe**

See the [CodeScribe README](https://github.com/Lab-Notebooks/CodeScribe) for installation and setup.

**2. Run the fresh-session loop**

Set your API key and run from this repo root:

```bash
export ANTHROPIC_API_KEY=”sk-ant-...”
code-scribe loop Spec.toml -m anthropic-claude-opus-4-6 -v --reason
```

- `-v` — verbose output (agent actions and token usage per iteration)
- `--reason` — enable adaptive thinking (Anthropic models only)
- Stop early with `Ctrl+C`.

To cap the run, add `-niter` (max iterations per session) and `-nloop` (max sessions).

Sample output (truncated):

```
▶  loop 1 [execution]
  iter 1
    │ Let me start by reading the task file, SPEC.md, AGENTS.md, and PLAN.md to understand the full context.
    usage  in 1,779  out 229  total 2,008
    ▸ read   Spec.toml
    ▸ read   SPEC.md
    ▸ read   AGENTS.md
    ▸ read   PLAN.md
  iter 2
    │ Let me understand the current state. All tasks are unchecked. I need to pick the most important
    │ thing to implement first. The most foundational task is the `Grid` class since everything else
    │ depends on it. Let me also check what files exist currently.
    usage  in 4,164  out 154  total 4,318
    ▸ glob   {“pattern”: “generated-src/**/*”, “include_dirs”: 1}          (empty)
  iter 3
    usage  in 4,359  out 276  total 4,635
    ▸ bash   python3.8 -c “import numpy”                                   bash exit_code=0
    ▸ bash   python3.8 -c “import scipy”                                   bash exit_code=0
  iter 4
    usage  in 4,637  out 151  total 4,788
    ▸ bash   mkdir -p generated-src/poisson/tests                          Error: command not allowed: 'mkdir'
  iter 5
    usage  in 5,047  out 347  total 5,394
    ▸ write  generated-src/poisson/__init__.py
  ...
```

**3. How it works**

Each loop session opens a fresh agent context with `Spec.toml` as the prompt. The agent reads `SPEC.md`, `AGENTS.md`, and `PLAN.md`, picks the highest-priority remaining task, implements it, then lists what remains. On the next loop a new session begins from the same prompt — no memory carries over, only the files the agent wrote.

- **Execution phase** — agent writes code under `generated-src/`
- **Review phase** — agent records progress
- Loop artifacts (status + report) land under `.codescribe/loop/`

## Run via the generic loop harness (multi-agent testing)

Use `ralph-loop.sh` when you want to test the same loop idea with other coding-agent frontends (opencode, Pi, etc.):

```bash
./ralph-loop.sh
```

Stop with `Ctrl+C`.

## Running the generated code

A completed solution lives under `archive/run-2026-06-09/generated-src/`.

**Run the demo** (convergence plot + benchmark) from inside `generated-src/`:

```bash
cd archive/run-2026-06-09/generated-src
python3.8 -m poisson.demo
```

Prints residual-vs-iteration for the Jacobi and CG solvers, then a wall-clock benchmark comparing all three solvers on 64×64 and 128×128 grids.

**Run the tests** from the archive run root:

```bash
cd archive/run-2026-06-09
python3.8 -m pytest generated-src/tests/test_poisson.py -v
```

The test suite uses a manufactured solution on a 64×64 grid and asserts L2 error < 1e-4 for each solver.

## Loop logs (`.codescribe/loop/`)

Each run archives its state in `.codescribe/loop/`. The files produced per run are:

| File | Contents |
|------|----------|
| `run.toml` | Run-level metadata — `run_id`, `created_at`, `model`, `agent_loops`, `agent_iterations` |
| `state.toml` | Live loop state — `loop_index`, current `phase` (`execution` or `review`), `updated_at` |
| `execution.toml` | Full event log: one `[[event]]` block per agent action (`run_start`, `iteration_start`, `model_response`, `tool_call`, `tool_result`, `run_end`), with token usage and timing per iteration |
| `review.toml` | Review-phase configuration passed to the reviewer agent |
| `review_output.toml` | Per-loop review summary — `loop` index, `summary` (what was built or cleaned up), `blocker` (empty string when unblocked) |

`execution.toml` is the most detailed: each `model_response` event includes `duration_ms`, `text_chars`, `tool_calls`, and a `usage` JSON blob with input/output/cache token counts. `model_text` records the agent's planning narrative verbatim.

## References

- [Ralph Wiggum as a “software engineer”](https://ghuntley.com/ralph) — The original blog post explaining the Ralph technique

## License

MIT — see `LICENSE`.
