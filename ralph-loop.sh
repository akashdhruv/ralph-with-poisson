#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

while true; do
    cat prompt.md | opencode --agent build run
    #sleep 60
done
