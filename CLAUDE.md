# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A ralph loop demo that uses an external harness to iteratively build a numerical Poisson solver. The harness resets the agent's context each iteration (by calling opencode fresh), while continuity is maintained through structured files the agent reads and updates.

## Running the Loop

```bash
./ralph-loop.sh
```

Each iteration: pipes `PROMPT.md` into `opencode --agent build run`, sleeps 60 seconds, repeats. Run until manually stopped.

## File Roles

| File | Role |
|------|------|
| `PROMPT.md` | Entry point — piped to agent each iteration |
| `PLAN.md` | Living task list — agent marks tasks `[x]` when complete |
| `SPEC.md` | Stable technical spec — Poisson solver details + the rule to update PLAN.md |
| `generated-src/` | All agent-generated code lives here |
| `ralph-loop.sh` | Harness — `while true; cat PROMPT.md \| opencode; sleep 60` |

## Agent Workflow (per iteration)

1. Reads `PROMPT.md` (via stdin)
2. Reads `PLAN.md` to see what's done and what's next
3. Reads `SPEC.md` for technical implementation details
4. Picks the top incomplete task and implements it in `generated-src/`
5. Updates `PLAN.md`: marks task `[x]`, adds a note

## What's Being Built

A standalone 2D Poisson solver (∇²φ = f) in Python under `generated-src/poisson/`:

- `grid.py` — `Grid` class: uniform 2D grid with numpy arrays for φ and RHS
- `solvers.py` — Jacobi, Conjugate Gradient (numpy), Direct (scipy)
- `tests/test_poisson.py` — manufactured solution verification
- `demo.py` — convergence and benchmark demo

See `SPEC.md` for full technical details.

## Ralph Loop Pattern

**External harness** (this repo): agent context resets each iteration; state is carried by `PLAN.md`. Context window stays manageable indefinitely.

**Internal harness** (alternative): agent accumulates all history in one session; context window grows until exhausted.
