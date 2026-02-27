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

### Manageable context window (external harness)

```
while true; do
    cat prompt.md | opencode --agent build run
done
```

## License

MIT — see `LICENSE`.
