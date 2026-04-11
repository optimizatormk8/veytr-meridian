#!/usr/bin/env bash
set -euo pipefail

hosts=(exit-node relay-node)
: > tests/systemlab/fixtures/known_hosts
for host in "${hosts[@]}"; do
  for _ in $(seq 1 30); do
    if ssh-keyscan -T 2 "$host" >> tests/systemlab/fixtures/known_hosts 2>/dev/null; then
      break
    fi
    sleep 1
  done
done
sort -u tests/systemlab/fixtures/known_hosts -o tests/systemlab/fixtures/known_hosts
