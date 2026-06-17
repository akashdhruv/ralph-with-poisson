#!/usr/bin/env python3
"""
CodeScribe benchmark for ralph-poisson archive/.

Parses .codescribe/loop/ TOML files, report.md, and shell_output.md
from each run directory and produces a comparison table or source diffs.

Usage:
  python3 benchmark.py                         # comparison table of all runs
  python3 benchmark.py --diff run-A run-B      # diff generated-src/ between two runs
  python3 benchmark.py --run run-A             # detailed view of one run
  python3 benchmark.py --json                  # all metrics as JSON
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ARCHIVE = Path(__file__).resolve().parent.parent / "archive"


# ── TOML field extractors (no external deps needed) ───────────────────────────

def _toml_str(text: str, key: str) -> Optional[str]:
    m = re.search(rf'(?m)^{re.escape(key)}\s*=\s*"((?:[^"\\]|\\.)*)"', text)
    if m:
        return m.group(1)
    m = re.search(rf"(?ms)^{re.escape(key)}\s*=\s*'''(.*?)'''", text)
    if m:
        return m.group(1).strip()
    return None


def _toml_int(text: str, key: str) -> Optional[int]:
    m = re.search(rf'(?m)^{re.escape(key)}\s*=\s*(\d+)', text)
    return int(m.group(1)) if m else None


def _numstr(s: str) -> int:
    return int(re.sub(r"[,\s]", "", s))


# ── Parsers for individual data sources ───────────────────────────────────────

def parse_exec_log(path: Path) -> Dict[str, Any]:
    """Parse execution.toml or review.toml: aggregate token counts, tool stats."""
    out: Dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "tool_errors": 0,
        "iterations": 0,
        "pytest_exit_codes": [],
    }
    if not path.exists():
        return out

    text = path.read_text()
    for block in re.split(r"\[\[event\]\]", text):
        ev_m = re.search(r'^event\s*=\s*"(\w+)"', block, re.MULTILINE)
        if not ev_m:
            continue
        ev = ev_m.group(1)

        if ev == "run_end":
            for field, key in [
                ("input_tokens", "total_input_tokens"),
                ("output_tokens", "total_output_tokens"),
                ("reasoning_tokens", "total_reasoning_tokens"),
                ("cache_read_tokens", "total_cache_read_tokens"),
                ("cache_write_tokens", "total_cache_creation_tokens"),
            ]:
                m = re.search(rf"^{key}\s*=\s*(\d+)", block, re.MULTILINE)
                if m:
                    out[field] += int(m.group(1))

        elif ev == "tool_end":
            ok_m = re.search(r"^ok\s*=\s*(true|false)", block, re.MULTILINE)
            if ok_m and ok_m.group(1) == "false":
                out["tool_errors"] += 1
            if "pytest" in block or "test_poisson" in block:
                m = re.search(r"exit_code:\s*(\d+)", block)
                if m:
                    out["pytest_exit_codes"].append(int(m.group(1)))

        elif ev == "iteration_end":
            out["iterations"] += 1

    return out


def parse_review_output(path: Path) -> Dict[str, Any]:
    out = {"review_loop": None, "summary": "", "blocker": None, "pending_count": 0}
    if not path.exists():
        return out
    text = path.read_text()
    out["review_loop"] = _toml_int(text, "loop")
    out["summary"] = _toml_str(text, "summary") or ""
    out["blocker"] = _toml_str(text, "blocker")
    out["pending_count"] = len(re.findall(r"^\[\[pending\]\]", text, re.MULTILINE))
    return out


def parse_run_toml(path: Path) -> Dict[str, Any]:
    out = {"model": None, "max_loops": None, "max_iterations": None}
    if not path.exists():
        return out
    t = path.read_text()
    out["model"] = _toml_str(t, "model")
    out["max_loops"] = _toml_int(t, "agent_loops")
    out["max_iterations"] = _toml_int(t, "agent_iterations")
    return out


def parse_state_toml(path: Path) -> Dict[str, Any]:
    out = {"loops_done": None, "phase": None}
    if not path.exists():
        return out
    t = path.read_text()
    out["loops_done"] = _toml_int(t, "loop_index")
    out["phase"] = _toml_str(t, "phase")
    return out


def parse_report_md(path: Path) -> Dict[str, Any]:
    """Parse report.md markdown tables for token usage, test results, setup info."""
    out: Dict[str, Any] = {
        "model": None,
        "wall_duration": None,
        "loops_done": None,
        "max_loops": None,
        "input_tokens": None,
        "output_tokens": None,
        "cache_read_tokens": None,
        "cache_write_tokens": None,
        "last_loop_input_tokens": None,
        "last_loop_output_tokens": None,
        "tests_passed": None,
        "tests_total": None,
    }
    if not path.exists():
        return out
    text = path.read_text()

    for line in text.splitlines():
        m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$", line)
        if not m:
            continue
        raw_key = m.group(1).strip()
        raw_val = m.group(2).strip()
        key = raw_key.lower()
        val = raw_val

        # Skip header/separator rows
        if val in ("-", "---", "value", "field", "Value", "Field"):
            continue
        # Skip explicitly unrecorded values
        if "not recorded" in val:
            continue
        # Skip per-loop breakdowns (Loop N input/output)
        if re.match(r"loop\s+\d+\s+(input|output)", key):
            continue

        try:
            if "model" in key and "model" in raw_key.lower()[:6]:
                out["model"] = val
            elif key in ("input tokens", "input token"):
                out["input_tokens"] = _numstr(val)
            elif key in ("output tokens", "output token"):
                out["output_tokens"] = _numstr(val)
            elif "cache read" in key:
                out["cache_read_tokens"] = _numstr(val)
            elif "cache write" in key:
                out["cache_write_tokens"] = _numstr(val)
            elif "last-loop input" in key or "last loop input" in key:
                out["last_loop_input_tokens"] = _numstr(val)
            elif "last-loop output" in key or "last loop output" in key:
                out["last_loop_output_tokens"] = _numstr(val)
            elif "wall" in key and "duration" in key:
                out["wall_duration"] = val
            elif "loop" in key and "complet" in key:
                m2 = re.match(r"(\d+)\s+of\s+(\d+)", val)
                if m2:
                    out["loops_done"] = int(m2.group(1))
                    out["max_loops"] = int(m2.group(2))
        except (ValueError, TypeError):
            pass

    # Count PASSED/FAILED lines (in code blocks or anywhere in the file)
    passed = len(re.findall(r"\bPASSED\b", text))
    failed = len(re.findall(r"\bFAILED\b", text))
    if passed or failed:
        out["tests_passed"] = passed
        out["tests_total"] = passed + failed
    else:
        m2 = re.search(r"(\d+)/(\d+)\s*tests?\s*pass", text, re.IGNORECASE)
        if m2:
            out["tests_passed"] = int(m2.group(1))
            out["tests_total"] = int(m2.group(2))

    return out


def parse_shell_output(path: Path) -> Dict[str, Any]:
    """Parse shell_output.md: sum token lines, extract pytest results."""
    out: Dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "tests_passed": None,
        "tests_total": None,
        "pytest_exit_codes": [],
    }
    if not path.exists():
        return out
    text = path.read_text()

    # Sum all "`tokens  in X  out Y  total Z`" lines (one per loop)
    for m in re.finditer(r"`tokens\s+in\s+([\d,]+)\s+out\s+([\d,]+)", text):
        out["input_tokens"] += _numstr(m.group(1))
        out["output_tokens"] += _numstr(m.group(2))

    for m in re.finditer(r"pytest.*?exit_code=(\d+)", text):
        out["pytest_exit_codes"].append(int(m.group(1)))

    passed = len(re.findall(r"\bPASSED\b", text))
    failed = len(re.findall(r"\bFAILED\b", text))
    if passed or failed:
        out["tests_passed"] = passed
        out["tests_total"] = passed + failed

    return out


# ── File tree ─────────────────────────────────────────────────────────────────

def list_py_files(src_dir: Path) -> Dict[str, Path]:
    """Return {rel_path: abs_path} for all .py files under src_dir."""
    if not src_dir.exists():
        return {}
    return {
        str(f.relative_to(src_dir)): f
        for f in sorted(src_dir.rglob("*.py"))
        if "__pycache__" not in str(f)
    }


# ── Run loader ────────────────────────────────────────────────────────────────

def detect_harness(run_dir: Path) -> str:
    name = run_dir.name
    if (run_dir / ".codescribe" / "loop").exists():
        return "codescribe"
    if "workflow" in name:
        return "workflow"
    if "loop" in name:
        return "claude-loop"
    return "external"


def _merge(data: dict, source: dict) -> None:
    """Fill None/0/empty fields in data from source."""
    for k, v in source.items():
        if v not in (None, 0, "", []) and data.get(k) in (None, 0, "", []):
            data[k] = v


def load_run(run_dir: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "name": run_dir.name,
        "harness": detect_harness(run_dir),
        "model": None,
        "max_loops": None,
        "max_iterations": None,
        "loops_done": None,
        "phase": None,
        "review_loop": None,
        "summary": "",
        "blocker": None,
        "pending_count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "last_loop_input_tokens": None,
        "last_loop_output_tokens": None,
        "wall_duration": None,
        "tool_errors": 0,
        "tests_passed": None,
        "tests_total": None,
        "pytest_exit_codes": [],
        "generated_files": [],
    }

    loop_dir = run_dir / ".codescribe" / "loop"
    if loop_dir.exists():
        data.update({k: v for k, v in parse_run_toml(loop_dir / "run.toml").items()
                     if v not in (None, "")})
        data.update({k: v for k, v in parse_state_toml(loop_dir / "state.toml").items()
                     if v not in (None, "")})
        data.update({k: v for k, v in parse_review_output(loop_dir / "review_output.toml").items()
                     if v not in (None, "")})

        ex = parse_exec_log(loop_dir / "execution.toml")
        rv = parse_exec_log(loop_dir / "review.toml")
        data["input_tokens"] += ex["input_tokens"] + rv["input_tokens"]
        data["output_tokens"] += ex["output_tokens"] + rv["output_tokens"]
        data["reasoning_tokens"] += ex["reasoning_tokens"] + rv["reasoning_tokens"]
        data["cache_read_tokens"] += ex["cache_read_tokens"] + rv["cache_read_tokens"]
        data["cache_write_tokens"] += ex["cache_write_tokens"] + rv["cache_write_tokens"]
        data["tool_errors"] = ex["tool_errors"]
        data["pytest_exit_codes"] = ex["pytest_exit_codes"] + rv["pytest_exit_codes"]

    # report.md: primary for external runs, supplement for native
    _merge(data, parse_report_md(run_dir / "report.md"))

    # shell_output.md: supplement token counts and test results
    so = parse_shell_output(run_dir / "shell_output.md")
    if so["input_tokens"] > 0:
        _merge(data, {"input_tokens": so["input_tokens"],
                      "output_tokens": so["output_tokens"]})
    if so["tests_passed"] is not None:
        _merge(data, {"tests_passed": so["tests_passed"],
                      "tests_total": so["tests_total"]})
    for code in so["pytest_exit_codes"]:
        if code not in data["pytest_exit_codes"]:
            data["pytest_exit_codes"].append(code)

    data["generated_files"] = sorted(list_py_files(run_dir / "generated-src").keys())
    return data


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_tok(n: Any, suffix: str = "") -> str:
    if not n:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M{suffix}"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k{suffix}"
    return f"{n}{suffix}"


def _fmt_loops(done: Any, max_l: Any) -> str:
    if done is None:
        return "—"
    return f"{done}/{max_l}" if max_l else str(done)


def _fmt_tests(passed: Any, total: Any) -> str:
    if passed is None:
        return "—"
    return f"{passed}/{total}" if total else str(passed)


def _fmt_blocker(b: Any) -> str:
    if b is None:
        return "?"
    return "YES" if b else ""


# ── Output modes ──────────────────────────────────────────────────────────────

def render_table(runs: List[Dict[str, Any]]) -> None:
    headers = [
        "Run", "Harness", "Loops",
        "In Tok", "Out Tok", "Cache-R", "Reason",
        "Tests", "Errs", "Pending", "Blocker",
    ]

    def row_of(r: Dict) -> List[str]:
        in_tok = r.get("input_tokens") or r.get("last_loop_input_tokens")
        out_tok = r.get("output_tokens") or r.get("last_loop_output_tokens")
        in_note = "" if r.get("input_tokens") else "*"
        return [
            r["name"],
            r.get("harness", "?"),
            _fmt_loops(r.get("loops_done"), r.get("max_loops")),
            _fmt_tok(in_tok, in_note),
            _fmt_tok(out_tok, in_note),
            _fmt_tok(r.get("cache_read_tokens")),
            _fmt_tok(r.get("reasoning_tokens")),
            _fmt_tests(r.get("tests_passed"), r.get("tests_total")),
            str(r.get("tool_errors") or ""),
            str(r.get("pending_count") or ""),
            _fmt_blocker(r.get("blocker")),
        ]

    rows = [row_of(r) for r in runs]
    widths = [
        max(len(h), max((len(row[i]) for row in rows), default=0))
        for i, h in enumerate(headers)
    ]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"

    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for r_data, row in zip(runs, rows):
        print(fmt.format(*row))
    print(sep)
    print("  * = last-loop only (cumulative tracking unavailable for that run)")
    print(f"\n  Columns: In/Out Tok = input/output tokens, Cache-R = cache read tokens,")
    print(f"           Reason = extended reasoning tokens, Errs = tool_errors (blocked cmds)")


def render_run_detail(r: Dict[str, Any]) -> None:
    print(f"\n{'='*60}")
    print(f"  {r['name']}")
    print(f"{'='*60}")
    print(f"  Harness:         {r.get('harness', '?')}")
    print(f"  Model:           {r.get('model') or '(from report.md)'}")
    print(f"  Loops:           {_fmt_loops(r.get('loops_done'), r.get('max_loops'))}")
    print(f"  Phase:           {r.get('phase') or '?'}")
    print(f"  Wall duration:   {r.get('wall_duration') or '?'}")
    print()
    in_tok = r.get("input_tokens") or r.get("last_loop_input_tokens")
    out_tok = r.get("output_tokens") or r.get("last_loop_output_tokens")
    note = " (last-loop only)" if not r.get("input_tokens") and in_tok else ""
    print(f"  Input tokens:    {_fmt_tok(in_tok)}{note}")
    print(f"  Output tokens:   {_fmt_tok(out_tok)}{note}")
    print(f"  Reasoning tok:   {_fmt_tok(r.get('reasoning_tokens'))}")
    print(f"  Cache read:      {_fmt_tok(r.get('cache_read_tokens'))}")
    print(f"  Cache write:     {_fmt_tok(r.get('cache_write_tokens'))}")
    print()
    print(f"  Tool errors:     {r.get('tool_errors', '?')}")
    codes = r.get("pytest_exit_codes", [])
    print(f"  Pytest runs:     {len(codes)} — exit codes: {codes if codes else '(none parsed)'}")
    print(f"  Tests:           {_fmt_tests(r.get('tests_passed'), r.get('tests_total'))}")
    print()
    print(f"  Blocker:         {r.get('blocker') or '(none)'}")
    print(f"  Pending items:   {r.get('pending_count', 0)}")
    if r.get("summary"):
        print(f"  Summary:         {r['summary'][:160]}...")
    files = r.get("generated_files", [])
    print(f"\n  Generated .py files ({len(files)}):")
    for f in files:
        print(f"    {f}")


def diff_runs(name_a: str, name_b: str, runs: List[Dict[str, Any]]) -> None:
    dir_a = ARCHIVE / name_a
    dir_b = ARCHIVE / name_b

    for name, path in [(name_a, dir_a), (name_b, dir_b)]:
        if not path.exists():
            print(f"Run not found: {name}", file=sys.stderr)
            sys.exit(1)

    # Metric comparison
    ra = next((r for r in runs if r["name"] == name_a), None)
    rb = next((r for r in runs if r["name"] == name_b), None)
    if ra and rb:
        print(f"=== {name_a}  vs  {name_b} ===\n")
        print(f"{'Metric':<22} {'A':>14} {'B':>14}")
        print("-" * 52)
        metrics = [
            ("Harness", "harness"),
            ("Loops", None),
            ("In tokens", "input_tokens"),
            ("Out tokens", "output_tokens"),
            ("Cache read", "cache_read_tokens"),
            ("Reasoning", "reasoning_tokens"),
            ("Tests", None),
            ("Tool errors", "tool_errors"),
            ("Pending", "pending_count"),
            ("Wall duration", "wall_duration"),
        ]
        for label, key in metrics:
            if key is None:
                if label == "Loops":
                    va = _fmt_loops(ra.get("loops_done"), ra.get("max_loops"))
                    vb = _fmt_loops(rb.get("loops_done"), rb.get("max_loops"))
                elif label == "Tests":
                    va = _fmt_tests(ra.get("tests_passed"), ra.get("tests_total"))
                    vb = _fmt_tests(rb.get("tests_passed"), rb.get("tests_total"))
                else:
                    continue
            elif key in ("input_tokens", "output_tokens", "cache_read_tokens", "reasoning_tokens"):
                va = _fmt_tok(ra.get(key) or ra.get("last_loop_input_tokens" if "input" in key else key))
                vb = _fmt_tok(rb.get(key) or rb.get("last_loop_input_tokens" if "input" in key else key))
            else:
                va = str(ra.get(key) or "—")
                vb = str(rb.get(key) or "—")
            marker = "  ←" if va != vb else ""
            print(f"  {label:<20} {va:>14} {vb:>14}{marker}")
        print()

    # Source file diff
    src_a = dir_a / "generated-src"
    src_b = dir_b / "generated-src"
    files_a = list_py_files(src_a)
    files_b = list_py_files(src_b)
    all_rel = sorted(set(files_a) | set(files_b))

    only_a = [f for f in all_rel if f in files_a and f not in files_b]
    only_b = [f for f in all_rel if f in files_b and f not in files_a]
    common = [f for f in all_rel if f in files_a and f in files_b]

    if only_a:
        print(f"Only in {name_a}:")
        for f in only_a:
            print(f"  - {f}")
        print()
    if only_b:
        print(f"Only in {name_b}:")
        for f in only_b:
            print(f"  + {f}")
        print()

    changed = 0
    unchanged = 0
    for rel in common:
        lines_a = files_a[rel].read_text().splitlines(keepends=True)
        lines_b = files_b[rel].read_text().splitlines(keepends=True)
        if lines_a == lines_b:
            unchanged += 1
            continue
        changed += 1
        diff = list(difflib.unified_diff(
            lines_a, lines_b,
            fromfile=f"{name_a}/{rel}",
            tofile=f"{name_b}/{rel}",
            lineterm="",
        ))
        print("\n".join(diff))
        print()

    print(f"({changed} file(s) changed, {unchanged} identical, "
          f"{len(only_a)} only-in-A, {len(only_b)} only-in-B)")


# ── Entry point ───────────────────────────────────────────────────────────────

def discover_runs() -> List[Path]:
    return sorted(
        p for p in ARCHIVE.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CodeScribe benchmark: compare ralph-poisson archive runs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--diff", nargs=2, metavar=("RUN_A", "RUN_B"),
        help="Diff generated-src/ between two runs and compare metrics",
    )
    parser.add_argument(
        "--run", metavar="NAME",
        help="Show detailed metrics for a single run",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output all metrics as JSON",
    )
    args = parser.parse_args()

    runs = [load_run(p) for p in discover_runs()]

    if args.diff:
        diff_runs(args.diff[0], args.diff[1], runs)
        return

    if args.run:
        match = [r for r in runs if r["name"] == args.run]
        if not match:
            names = ", ".join(r["name"] for r in runs)
            print(f"Run not found: {args.run}\nAvailable: {names}", file=sys.stderr)
            sys.exit(1)
        render_run_detail(match[0])
        return

    if args.json:
        print(json.dumps(runs, indent=2, default=str))
        return

    render_table(runs)


if __name__ == "__main__":
    main()
