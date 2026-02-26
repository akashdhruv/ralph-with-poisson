## Exploding context window, running ralph loop from withing a coding agent (inside harness)

```
cat spec.md | opencode --agent build run "/ralph-loop"
```

## Manageable context window, running ralph loop outside the coding agent (external harness)

```
while true; do
    cat spec.md | opencode --agent build run
end do
```
