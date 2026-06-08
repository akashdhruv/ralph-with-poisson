#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

while true; do
    pi @prompt.toml -p --model claudeopus46
    #cat prompt.md | opencode --agent build run
    #sleep 60
done
