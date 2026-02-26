# Ralph Loop Context Window Test Spec

## Objective
Run a time-boxed Ralph Loop test for 5 minutes. At each elapsed minute mark (1..5), append a new, well-structured "context window" section to `context-window.md` and update `implementation.md`.

## Definitions
- **Minute mark m**: elapsed time since start is >= m * 60 seconds.
- **Iteration m**: the work performed at minute mark m.

## Files
- `specs.md`: this specification (stable during the run).
- `implementation.md`: updated each iteration to reflect progress (checklist + notes).
- `context-window.md`: append-only log, one section per iteration.

## Run Requirements
- Total duration: 5 minutes.
- Iterations: exactly 5, at minute marks 1, 2, 3, 4, 5.
- At each iteration:
  1. Read `specs.md` and current `implementation.md`.
  2. Update `implementation.md` by marking that minute's bullet complete and adding a brief note for that minute.
  3. Append a new section to `context-window.md` with the required structure.

## Required `context-window.md` Structure (per iteration)
Append a section with these headings (in order):

- `## Minute M (Iteration M)`
- `### Metadata`
  - Timestamp (UTC or local, but consistent)
  - Elapsed seconds
  - Runner command (e.g., `opencode ralph-loop ...`)
- `### Prompt`
  - The exact prompt sent to Ralph Loop
- `### Specs`
  - Include full `specs.md` contents OR include a hash plus a short excerpt (choose one and keep consistent)
- `### Implementation Before`
  - The full previous `implementation.md` (before this iteration)
- `### Output Summary`
  - Short structured summary of changes and rationale
- `### Implementation Diff (optional but recommended)`
  - Unified diff of `implementation.md` before vs after
- `### Implementation After`
  - The full new `implementation.md` (after this iteration)

## Output Contract for Ralph Loop (for automation)
Each iteration's Ralph Loop response must contain exactly two fenced blocks:

1) New `implementation.md` content:
```IMPLEMENTATION_MD
(full file contents)
```

2) A short summary:
```SUMMARY
- Changes:
- Rationale:
- Next step:
```

No additional text outside these blocks.

## Acceptance Criteria
- `context-window.md` contains 5 sections, one for each minute mark 1..5, each following the required structure.
- `implementation.md` shows minute bullets 1..5 marked complete by the end of iteration 5.
- The run is time-boxed (iterations occur at elapsed minute marks, not just "sleep 60").
