#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

while true; do
    pi @Spec.toml -p --model claudeopus46
    #cat Spec.toml | opencode --agent build run
    #sleep 60
done
