# Orchestration Patterns for AI Coding Agents

This repo is an experiment in **how you direct an AI agent to build software** — not just what prompt you write, but how you structure the loop around the agent: how sessions start, what context survives between them, and whether multiple agents collaborate or one runs alone.

The concrete task is a 2D Poisson solver in Python (`SPEC.md`). The solver is non-trivial enough to require several files, iterative debugging, and deliberate design choices, but small enough that any capable model can finish it in a single session if given the right scaffolding. That makes it a useful benchmark for comparing orchestration strategies: the task itself is held constant, and what varies is the harness.

Six runs are archived under `archive/`. Each has a `report.md` summarising the setup, token usage, test results, and benchmark output.

---

## Background: The Ralph Pattern

The term comes from a [blog post by Geoffrey Huntley](https://ghuntley.com/ralph) describing how to use LLMs as "software engineers" — not by giving them one enormous prompt and hoping for the best, but by running them in a tight loop where each session has a fixed context window, picks up where the last one left off via the files it wrote, and hands off gracefully to the next.

The key insight is that **state lives in the filesystem, not in the model's context**. Each session:

1. Reads the spec, the task checklist (`PLAN.md`), and the files already written.
2. Picks the single highest-priority remaining task.
3. Implements it, marks it done in `PLAN.md`, and exits.

The next session opens with no memory of the previous one — only the artifacts it left behind. This keeps each session focused, prevents context bloat, and makes the loop resumable after interruption.

---

## The Task

`SPEC.md` specifies a 2D Poisson equation solver on a unit square with:

- A `Grid` class (ghost-cell stencil, Dirichlet and Neumann boundary conditions)
- Three solvers: Jacobi (iterative), Conjugate Gradient (numpy only), and direct (sparse via `scipy`)
- A manufactured solution test (`sin(πx)sin(πy)`) verifying L2 error < 1e-4
- A `demo.py` producing a convergence plot and wall-clock benchmark

All generated code lands under `generated-src/` and is never committed to this repo — each run starts from a clean slate.

---

## Orchestration Patterns Explored

Three different orchestration strategies were tested, implemented by two different harnesses.

### 1. CodeScribe fresh-session loop

[CodeScribe](https://github.com/Lab-Notebooks/CodeScribe) is a Python harness that wraps a model API in a structured loop. Each loop session is a fully independent agent context. A `Spec.toml` file defines the task prompt, the model, and tool permissions. CodeScribe handles session management, progress logging, and a separate review-phase agent that checks work and records blockers.

**How it works:**

```
loop 1 [execution]  ← fresh context, reads SPEC.md + PLAN.md, writes code
loop 1 [review]     ← separate agent reads the output, records summary + blockers
loop 2 [execution]  ← fresh context again, picks up from where loop 1 left off
loop 2 [review]     ← ...
...
```

Within each execution session the agent runs for up to N iterations (tool calls interleaved with model reasoning). When it hits the limit or declares itself done, CodeScribe runs the review agent, then starts a new execution session.

Four runs with this pattern are archived, all using `claude-opus-4-6` with extended thinking (`--reason`):

| Run | Loops | Tests | Total tokens in | Wall time |
|-----|-------|-------|-----------------|-----------|
| `run-2026-06-09` | 4 | 5/5 | not recorded | 11m 52s |
| `run-2026-06-10` | 5 | 6/6 | not recorded | 16m 45s |
| `run-2026-06-10_2` | 5 | 12/12 | 974,751 | 16m 47s |
| `run-2026-06-10_3` | 2 | 6/6 | 415,652 | 10m 29s |

All four runs completed all 8 tasks and passed their full test suites. Test coverage improved across runs (5 → 6 → 12 tests) as the agents wrote more thorough test suites. The fastest run (`run-2026-06-10_3`) finished in 2 loops — the model completed the entire implementation in one session and the second loop was the review pass.

---

### 2. Claude Code `/loop` skill

Claude Code (the Anthropic CLI) ships a `/loop` skill that runs a prompt on a self-paced recurring schedule. Unlike CodeScribe's fresh-session model, the `/loop` skill keeps a **single running context** and schedules the next wake-up itself. The agent decides when to sleep and when to re-run; it is not restarted between iterations.

Run: `run-2026-06-10-claude-loop`

| Field | Value |
|-------|-------|
| Model | claude-sonnet-4-6 (1M context) |
| Iterations | 1 (all 8 tasks in a single turn) |
| Tests | 9/9 PASSED |
| Input tokens | ~1,100 + 1,100,000 cache reads |
| Wall time | 5m 51s |
| Cost | $0.63 |

The model completed all 8 tasks in a single iteration and scheduled a fallback wakeup; the user stopped the loop manually. The 1M context window meant the agent could hold the entire spec, all written files, and test output in memory simultaneously — no need for a fresh-session handoff.

---

### 3. Claude Code Workflow (multi-agent orchestration)

Claude Code's Workflow tool runs a JavaScript script that fans out multiple sub-agents concurrently. The script defines which agents spawn, in what order, and what each one sees. This is the most structured form of orchestration: the control flow is deterministic code, not model judgment.

Run: `run-2026-06-10-claude-workflow`

| Field | Value |
|-------|-------|
| Model | claude-sonnet-4-6 (1M context) |
| Agents | 3 — check-plan (×2), implement (×1) |
| Iterations | 1 |
| Tests | 20/20 PASSED |
| Input tokens | 2,600 + 932,600 cache reads |
| Wall time | 5m 42s |

The workflow used a loop-until-dry pattern: a check-plan agent scanned `PLAN.md` for pending tasks, handed them to an implement agent, then re-checked. It exited cleanly after detecting 0 remaining tasks. The implement agent produced the highest test count of any run (20 tests) in a single shot.

---

## What These Patterns Trade Off

| | CodeScribe loop | Claude Code `/loop` | Claude Code Workflow |
|---|---|---|---|
| **Session model** | Fresh per loop | Persistent single context | Deterministic multi-agent |
| **Control flow** | Harness-managed | Model-scheduled | Script-defined |
| **Context budget** | Low per session (grows across loops) | Large (1M window) | Moderate per agent |
| **Parallelism** | None (sequential loops) | None (one agent) | Yes (concurrent agents) |
| **Resumability** | Built-in (state in `.codescribe/`) | Manual | Via workflow run ID |
| **Overhead** | Medium (review agent between loops) | Low | Low |
| **Best for** | Long tasks, many models, no large context | Single-shot tasks, large specs | Tasks with natural fan-out |

The `/loop` and Workflow runs both completed faster and with more tests than the CodeScribe runs, largely because `claude-sonnet-4-6` with a 1M context window could load the entire workspace in one shot. The CodeScribe runs with `claude-opus-4-6` + reasoning produced good code but spent several loops on cleanup and threshold-tuning that a single-context run handles in one pass.

---

## Repository Layout

```
Spec.toml           # Task prompt for CodeScribe
SPEC.md             # Technical specification (Poisson solver)
AGENTS.md           # Repo restrictions for agents (what to ignore)
PLAN.md             # Task checklist — agents mark tasks done as they go
ralph-loop.sh       # Generic loop harness for other frontends (opencode, etc.)
archive/
  run-2026-06-09/           # CodeScribe, Opus 4.6, 4 loops
  run-2026-06-10/           # CodeScribe, Opus 4.6, 5 loops
  run-2026-06-10_2/         # CodeScribe, Opus 4.6, 5 loops
  run-2026-06-10_3/         # CodeScribe, Opus 4.6, 2 loops (fastest)
  run-2026-06-10-claude-loop/       # Claude Code /loop, Sonnet 4.6 1M
  run-2026-06-10-claude-workflow/   # Claude Code Workflow, Sonnet 4.6 1M
generated-src/      # Output directory (empty; agents write here during a run)
```

Each `archive/run-*/` directory contains:
- `report.md` — experiment report (setup, tokens, test output, benchmark, notes)
- `generated-src/` — the code the agent produced
- `PLAN.md` — task checklist at the end of the run
- `.codescribe/loop/` — CodeScribe run logs (CodeScribe runs only)

---

## Running the Experiments

### CodeScribe (fresh-session loop)

**1. Install CodeScribe**

See the [CodeScribe README](https://github.com/Lab-Notebooks/CodeScribe) for installation and setup.

**2. Run the fresh-session loop**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
code-scribe loop Spec.toml -m anthropic-claude-opus-4-6 -v --reason
```

- `-v` — verbose output (agent actions and token usage per iteration)
- `--reason` — enable extended thinking (Anthropic models only)
- `-niter N` — cap iterations per session (default 12)
- `-nloop N` — cap total loop sessions (default 5)
- Stop early with `Ctrl+C`

Sample output:

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
    ▸ glob   {"pattern": "generated-src/**/*", "include_dirs": 1}          (empty)
  iter 3
    usage  in 4,359  out 276  total 4,635
    ▸ bash   python3.8 -c "import numpy"                                   bash exit_code=0
    ▸ bash   python3.8 -c "import scipy"                                   bash exit_code=0
  iter 4
    usage  in 4,637  out 151  total 4,788
    ▸ bash   mkdir -p generated-src/poisson/tests                          Error: command not allowed: 'mkdir'
  iter 5
    usage  in 5,047  out 347  total 5,394
    ▸ write  generated-src/poisson/__init__.py
  ...
```

**How it works:**

Each loop session opens a fresh agent context with `Spec.toml` as the prompt. The agent reads `SPEC.md`, `AGENTS.md`, and `PLAN.md`, picks the highest-priority remaining task, implements it, then lists what remains. On the next loop a new session begins from the same prompt — no memory carries over, only the files the agent wrote.

- **Execution phase** — agent writes code under `generated-src/`
- **Review phase** — separate agent reads the output and records a summary and any blockers
- Loop artifacts land under `.codescribe/loop/`

### Claude Code `/loop`

From this repo root with Claude Code open:

```
/loop Spec.toml
```

The agent reads `Spec.toml`, then works through all tasks in a single self-paced context. It schedules its own wakeup interval and stops when `PLAN.md` has no remaining `[ ]` tasks. Stop manually with `Ctrl+C` once it declares completion.

### Claude Code Workflow

From this repo root with Claude Code open:

```
run a loop on Spec.toml using workflows
```

Claude Code generates and executes a multi-agent workflow script: a check-plan agent scans `PLAN.md`, an implement agent writes the code, and the loop exits when no pending tasks remain. Progress is visible live under `/workflows`.

### Generic loop harness (`ralph-loop.sh`)

Use this to test other coding-agent frontends (opencode, Pi, etc.) against the same task:

```bash
./ralph-loop.sh
```

Stop with `Ctrl+C`.

---

## Running the Generated Code

Any archived run can be exercised independently.

**Run the demo** (convergence plot + benchmark):

```bash
cd archive/run-2026-06-09/generated-src
python3.8 -m poisson.demo
```

Prints residual-vs-iteration for the Jacobi and CG solvers, then a wall-clock benchmark comparing all three solvers on 64×64 and 128×128 grids.

**Run the tests:**

```bash
cd archive/run-2026-06-09
python3.8 -m pytest generated-src/tests/test_poisson.py -v
```

Each run's `report.md` documents the expected test names and output.

---

## CodeScribe Loop Logs (`.codescribe/loop/`)

Each CodeScribe run archives its state in `.codescribe/loop/`. The files produced per run are:

| File | Contents |
|------|----------|
| `run.toml` | Run-level metadata — `run_id`, `created_at`, `model`, `agent_loops`, `agent_iterations`, cumulative token totals |
| `state.toml` | Live loop state — `loop_index`, current `phase` (`execution` or `review`), `updated_at` |
| `execution.toml` | Full event log for the last execution session: one `[[event]]` block per agent action (`run_start`, `iteration_start`, `model_response`, `tool_call`, `tool_result`, `run_end`), with token usage and timing per iteration |
| `review.toml` | Review-phase configuration passed to the reviewer agent |
| `review_output.toml` | Per-loop review summary — `loop` index, `summary` (what was built or cleaned up), `blocker` (empty string when unblocked) |

`execution.toml` is the most detailed: each `model_response` event includes `duration_ms`, `text_chars`, `tool_calls`, and a `usage` JSON blob with input/output/cache token counts. `model_text` records the agent's planning narrative verbatim.

---

## References

- [Ralph Wiggum as a "software engineer"](https://ghuntley.com/ralph) — The original blog post explaining the Ralph technique
- [CodeScribe](https://github.com/Lab-Notebooks/CodeScribe) — The loop harness used for the CodeScribe runs
- [Claude Code](https://claude.ai/code) — Anthropic's coding agent CLI, used for the `/loop` and Workflow runs

## License

MIT — see `LICENSE`.
