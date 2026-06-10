## Experiment: Ralph-style loop harness + CodeScribe loop mode

This repo is an experiment in running repeated “fresh session” coding-agent iterations over a single task prompt.

Key files:

- `specification.toml` — the task file used by CodeScribe loop mode
- `ralph-loop.sh` — a small external harness for testing different coding agents (e.g. opencode, Pi, etc.) and for CodeScribe-specific special tests

## CodeScribe Quickstart

**1. Install CodeScribe**

See the [CodeScribe README](https://github.com/Lab-Notebooks/CodeScribe) for installation and setup.

**2. Run the bounded fresh-session loop**

Set your API key and run from this repo root:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
code-scribe loop specification.toml -m anthropic-claude-opus-4-6 -v -niter 30 -nloop 20 --reason
```

- `-niter` — max iterations per loop session
- `-nloop` — max number of loop sessions
- `--reason` — enable adaptive thinking (Anthropic models only)
- Stop early with `Ctrl+C`.

Sample output (truncated):

```
▶  loop 1 [execution]
  iter 1
    │ Let me start by reading the task file and understanding the current state of the project.
    usage  in 2,517  out 158  total 2,675
    ▸ read   specification.toml
    ▸ bash   find . -type f -not -path './.git/*' 2>/dev/null              Error: blocked shell syntax detected
  iter 2
    usage  in 4,093  out 64  total 4,157
    ▸ bash   find . -type f -not -path "./.git/*"                          bash exit_code=0
  iter 3
    usage  in 4,598  out 54  total 4,652
    ▸ read   PLAN.md
  iter 4
    │ Now I have a clear picture. This is the first loop and nothing has been implemented yet.
    │ I'll start by building out the core components: the Grid class to handle the discretization,
    │ all three solver implementations, and the test suite to validate them.
    usage  in 5,147  out 4,009  total 9,156
    ▸ write  generated-src/poisson/__init__.py
    ▸ write  generated-src/poisson/grid.py
    ▸ write  generated-src/poisson/solvers.py
  iter 5
    usage  in 9,292  out 1,767  total 11,059
    ▸ write  generated-src/tests/__init__.py
    ▸ write  generated-src/tests/test_poisson.py
    ▸ write  generated-src/poisson/demo.py
  ...
```

**3. How it works**

Each loop session opens a fresh agent context with `specification.toml` as the prompt. The agent reads `PLAN.md`, picks the highest-priority remaining task, implements it, then lists what remains. On the next loop a new session begins from the same prompt — no memory carries over, only the files the agent wrote.

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
