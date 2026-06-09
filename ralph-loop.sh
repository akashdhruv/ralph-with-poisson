#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

while true; do
    pi @prompt.toml \
        --append-system-prompt "Plan your approach before making any changes. You have permission to write and edit files in the current directory without asking for confirmation." \
        -p --model claudeopus46
    #cat prompt.md | opencode --agent build run
    #sleep 60
done
