# benchmark.py — archive run comparator

A dependency-free CLI for comparing the archived CodeScribe / Claude Code runs under
`../archive/`. It parses each run's CodeScribe loop logs (`.codescribe/loop/*.toml`),
its `report.md`, and any `shell_output.md`, then renders a comparison table, a per-run
detail view, a two-run diff, or raw JSON.

> This lives under `benchmark/`, which `AGENTS.md` lists as ignored — it is scratch
> tooling for inspecting the archive, not part of a solver run.

## Requirements

- Python 3.8+ (standard library only — no `pip install` needed; it does not even require a
  TOML parser, fields are extracted with regex).

## Usage

Run it from anywhere — the archive path is resolved relative to the script, not your
current directory:

```bash
# Comparison table of all runs (default)
python3.8 benchmark.py

# Detailed metrics for one run
python3.8 benchmark.py --run run-2026-06-16

# Diff metrics + generated-src/ source between two runs
python3.8 benchmark.py --diff run-2026-06-10_3 run-2026-06-16

# All metrics for all runs as JSON (for scripting)
python3.8 benchmark.py --json
```

Run names are the directory names under `../archive/`. An unknown name prints the list of
available runs.

## Comparison table columns

```
+--------------------------------+-------------+-------+--------+---------+---------+--------+-------+------+---------+---------+
| Run                            | Harness     | Loops | In Tok | Out Tok | Cache-R | Reason | Tests | Errs | Pending | Blocker |
```

| Column    | Meaning |
|-----------|---------|
| `Run`     | Archive directory name |
| `Harness` | `codescribe`, `claude-loop`, `workflow`, or `external` (auto-detected) |
| `Loops`   | Loops completed / max loops (CodeScribe runs) |
| `In Tok`  | Billed input tokens (`*` = last-loop only, when cumulative tracking is unavailable) |
| `Out Tok` | Output tokens |
| `Cache-R` | Prompt-cache read tokens (`—` for runs that predate caching) |
| `Reason`  | Extended-reasoning tokens |
| `Tests`   | Tests passed / total |
| `Errs`    | Tool errors (e.g. blocked commands like `mkdir`/`rm`) |
| `Pending` | `[[pending]]` items left in `review_output.toml` |
| `Blocker` | Whether the review phase recorded a blocker |

A `—` means the value was not recorded for that run.

## Where the numbers come from

`benchmark.py` merges several sources per run, preferring the most authoritative and
filling gaps from the rest:

- **`.codescribe/loop/run.toml`** — model, max loops, max iterations.
- **`.codescribe/loop/state.toml`** — loops completed, current phase.
- **`.codescribe/loop/execution.toml`** (and `review.toml`) — input/output/reasoning and
  **cache** tokens are summed from each `run_end` event (`total_*_tokens`); tool errors and
  pytest exit codes come from `tool_end` events. Caching-era runs (2026-06-16 onward) carry
  `total_cache_read_tokens` / `total_cache_creation_tokens` here, which populate `Cache-R`.
- **`.codescribe/loop/review_output.toml`** — review summary, blocker, pending count.
- **`report.md`** — primary source for non-CodeScribe runs and a supplement for CodeScribe
  ones; supplies wall duration, cache totals, and the `PASSED`/`FAILED` test counts.
- **`shell_output.md`** — supplements token counts and test results when present.

Because parsing is regex-based, no third-party TOML/Markdown libraries are required, but the
field names above must match what CodeScribe writes.

## Adding a new run

Drop the run directory under `../archive/<name>/` with its `.codescribe/loop/` logs and a
`report.md`. It is picked up automatically — `discover_runs()` scans every non-hidden
directory in `../archive/`. Include `report.md` so the `Tests` column populates (the loop
logs alone do not record a pass/fail tally).
