## Run

One-shot:

```
cat prompt.md | opencode --agent build run
```

Loop (external harness):

```
./ralph-loop.sh
```

Stop with Ctrl+C.

## Notes

### Exploding context window (inside harness)

```
cat prompt.md | opencode --agent build run "/ralph-loop"
```

### Manageable context window (outside harness)

```
while true; do
    cat prompt.md | opencode --agent build run
done
```

## References

- [Ralph Wiggum as a "software engineer"](https://ghuntley.com/ralph) — The original blog post explaining the Ralph technique

## License

MIT — see `LICENSE`.
