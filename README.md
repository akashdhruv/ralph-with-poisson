# Orchestration Patterns for AI Coding Agents

This repo is a controlled experiment in **how you structure the loop around an AI coding agent** — how sessions start, what context survives between them, and whether multiple agents should collaborate or one should run alone. The concrete task is a 2D Poisson solver in Python (`SPEC.md`): a classic workhorse of computational science, appearing in electrostatics, fluid dynamics, and heat transfer, and a standard benchmark in the numerical methods literature. It's non-trivial enough to require several files, iterative debugging, and deliberate design choices — but small enough that any capable model can finish it in a single session if given the right scaffolding. That makes it a useful benchmark for comparing orchestration strategies: the task is held constant, and what varies is the harness.

This experiment is part of the authors' broader work on AI-driven scientific software engineering and automated code translation. Prior publications and associated datasets are linked from the [CodeScribe repo](https://github.com/Lab-Notebooks/CodeScribe).

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

The Poisson equation (∇²u = f) is one of the most studied problems in computational mathematics, with applications across electrostatics, incompressible flow, image processing, and structural mechanics. Its solvers are a standard first test for numerical computing libraries and a natural benchmark for AI coding agents: the problem is well-specified, has known analytic solutions for verification, and requires real engineering decisions — discretization scheme, boundary condition handling, solver choice, convergence criteria.

`SPEC.md` asks the agent to build a solver on a unit square with:

- A `Grid` class (ghost-cell stencil, Dirichlet and Neumann boundary conditions)
- Three solvers: Jacobi (iterative), Conjugate Gradient (numpy only), and direct (sparse via `scipy`)
- A manufactured solution test (`sin(πx)sin(πy)`) verifying L2 error < 1e-4
- A `demo.py` producing a convergence plot and wall-clock benchmark

All generated code lands under `generated-src/` and is never committed to this repo — each run starts from a clean slate.

---

## Orchestration Patterns Explored

Three different orchestration strategies were tested, implemented by two different harnesses.

### 1. CodeScribe fresh-session loop

[CodeScribe](https://github.com/Lab-Notebooks/CodeScribe) is a Python harness that wraps a model API in a structured loop. Each loop session is a fully independent agent context. A `Spec.toml` file defines the task prompt and tool permissions. CodeScribe handles session management, progress logging, and a separate review-phase agent that checks work and records blockers. Because it makes direct API calls with configurable API keys, it works with any provider — Anthropic, OpenAI, or open-weight and open-source models — which makes it useful for comparing model behaviour on the same task across providers.

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
| **Prompt caching** | Not implemented | Yes (Anthropic API, native) | Yes (Anthropic API, native) |
| **Overhead** | Medium (review agent between loops) | Low | Low |
| **Multi-provider** | Yes (any API key / model) | Anthropic only | Anthropic only |
| **Best for** | Long tasks, open-weight models, cost-sensitive runs | Single-shot tasks, large specs | Tasks with natural fan-out |

The `/loop` and Workflow runs both completed faster and with more tests than the CodeScribe runs, largely because `claude-sonnet-4-6` with a 1M context window could load the entire workspace in one shot. The CodeScribe runs with `claude-opus-4-6` + reasoning produced good code but spent several loops on cleanup and threshold-tuning that a single-context run handles in one pass.

Token usage reflects a different trade-off. The Claude Code experiments expose a split between actual input tokens and cache reads — a feature of the Anthropic model API's prompt caching support, which Claude Code uses natively. The `/loop` run billed only 1,100 actual input tokens against 1.1M cache reads; the Workflow run billed 2,600 against 932k. The CodeScribe runs show no cache reads (415k–974k tokens billed at standard rates) because the current API integration does not yet implement caching. That said, CodeScribe's fresh-session model keeps each individual session's active context small — it loads only what's needed for the current task rather than holding the entire workspace in a 1M window — which limits per-session cost and makes it practical with smaller or cheaper models. Work is underway to add prompt caching to CodeScribe's API calls and to reduce loop count by consolidating tasks that the agent currently spreads across multiple sessions.

From a scientific software perspective, the more notable result is that all six runs produced *correct* solvers with verified L2 errors below the spec threshold. The variation across runs was in polish, test coverage, and wall time — not in numerical correctness. That's a meaningful result: the hard part of AI-driven scientific software is no longer getting the math right, it's structuring the agent's workflow so it doesn't waste loops producing hallucinations.

The shell output logs (`archive/run-2026-06-10_3/shell_output.md`) and terminal screenshots (`media/shell-v*.png`) give qualitative insight into why the Opus 4.6 runs needed more loops. Two patterns stand out.

First, the model caught a numerical discrepancy in `SPEC.md`: the spec asks for L2 error < 1e-4 on a 32×32 grid, but a second-order finite difference discretization on that grid inherently produces a truncation error of ~3.9e-4. In iter 8 of Loop 1 of `run-2026-06-10_3`, the model spent 13,540 output tokens working through this — computing discrete Laplacian eigenvalues, re-examining grid conventions (intervals vs. interior points), and ultimately relaxing the test threshold to 5e-4 with a documented justification. This is genuinely useful behaviour: the model found a real problem in the spec. But in a fresh-session loop, that analysis consumed an entire iteration before any code was written, which pushed implementation into the next loop.

Second, the model repeatedly re-validated the spelling of `AssertionError` across multiple loops. This can be a consequence of the fresh-session model: each new context has no memory of checks performed in prior sessions, so it re-verifies things the previous session already confirmed. An important caveat to note here is that `code-scribe loop` does read a `review_output.toml` which may trigger hallucinations. Both behaviours are characteristic of Opus 4.6 with extended thinking — thorough reasoning that surfaces real issues, but whose cost compounds in a loop where the slate is wiped between sessions.

---

## Repository Layout

**Specification and task files**

- `SPEC.md` — the full technical specification for the Poisson solver: problem statement, module layout, solver signatures, boundary condition rules, manufactured solution test, and convergence criteria. This is the ground truth every agent reads.
- `PLAN.md` — the task checklist. Eight items, each marked `[ ]` at the start. Agents tick them off as they go (`[x]`), and the loop terminates when all are checked and all tests pass. Shared state between sessions in the fresh-session strategies.
- `Spec.toml` — a CodeScribe agent specification file. In the authors' HPC code translation work, CodeScribe specs define a three-phase workflow — *index* (survey the codebase), *translate* (convert source to target language), *generate* (produce tests and documentation) — each phase driven by a separate agent context. The motivation for building this in CodeScribe rather than off-the-shelf orchestration tools is a desire to write agent workflows in Python with native API access, giving precise control over the multitude of HPC tools invoked at each phase and the context they produce. For this experiment we use a more fundamental workflow: a plain loop, one task at a time, inspired by the Ralph Loop concept. The spec instructs the agent to read `SPEC.md`, `AGENTS.md`, and `PLAN.md`, pick the highest-priority remaining task, implement it, and list what's left for the next session. Tool allowlist: `bash = ["python3.8"]`.
**Harness**

- `ralph-loop.sh` — a minimal bash loop that calls `pi @Spec.toml` on each iteration, effectively running any Pi-compatible frontend against the same task in a fresh-session pattern. Includes a commented-out opencode variant. Stop with `Ctrl+C`.

**Agent instructions**

- `AGENTS.md` — one line: `IGNORE: archive/*, README.md, media/*`. This tells every agent to treat the archived runs, this file, and the screenshots as read-only. Agents that respect `AGENTS.md` will never overwrite past results or touch documentation.

**Output**

- `generated-src/` — empty at rest. Agents write their solver code here during a live run. Not committed to the repo — every experiment starts from a blank slate.

**Archive**

- `archive/run-2026-06-09/` — CodeScribe, Opus 4.6, 4 loops, 5/5 tests, 11m 52s
- `archive/run-2026-06-10/` — CodeScribe, Opus 4.6, 5 loops, 6/6 tests, 16m 45s
- `archive/run-2026-06-10_2/` — CodeScribe, Opus 4.6, 5 loops, 12/12 tests, 974k tokens in, 16m 47s
- `archive/run-2026-06-10_3/` — CodeScribe, Opus 4.6, 2 loops (fastest), 6/6 tests, 415k tokens in, 10m 29s
- `archive/run-2026-06-10-claude-loop/` — Claude Code `/loop`, Sonnet 4.6 1M, 1 iteration, 9/9 tests, $0.63, 5m 51s
- `archive/run-2026-06-10-claude-workflow/` — Claude Code Workflow, Sonnet 4.6 1M, 3 agents, 20/20 tests, 5m 42s

Each `archive/run-*/` directory contains:
- `report.md` — experiment report (setup, tokens, test output, benchmark, notes)
- `generated-src/` — the solver code the agent produced (preserved, never modified)
- `PLAN.md` — task checklist state at the end of the run
- `.codescribe/loop/` — CodeScribe run logs (CodeScribe runs only)

**Media**

- `media/shell-v1.png` … `shell-v6.png` — terminal screenshots, one per run, showing live agent output.

Note that `AGENTS.md` explicitly instructs agents to ignore `archive/*`, `media/*`, and `README.md` — so archived `generated-src/` trees are preserved as read-only artefacts and won't be touched if you run a new experiment from this repo.

---

## Running the Experiments

### CodeScribe (fresh-session loop)

**1. Install CodeScribe**

See the [CodeScribe README](https://github.com/Lab-Notebooks/CodeScribe/tree/b9272c16c34111c98332a967b9be7ea3e3cdb8b8) for installation and setup.


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

CC BY 4.0 — see `LICENSE`.
