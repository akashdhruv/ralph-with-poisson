#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

START_EPOCH="$(date +%s)"

for M in 1 2 3 4 5; do
	TARGET=$((START_EPOCH + (M * 60)))

	# Wait until minute mark
	while :; do
		NOW="$(date +%s)"
		if [ "$NOW" -ge "$TARGET" ]; then
			break
		fi
		sleep 1
	done

	ELAPSED=$((NOW - START_EPOCH))

	# Prepend iteration metadata to specs, pipe to opencode
	{
		printf '# Run Context\n'
		printf 'Iteration: %d\n' "$M"
		printf 'Elapsed seconds: %d\n' "$ELAPSED"
		printf '\n---\n\n'
		cat specs.md
	} | opencode --agent build run

done
