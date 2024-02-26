#!/usr/bin/env bash

set -eu

if [[ $# != 2 ]]; then
    echo "Usage: $0 <seed url> <path to result>"
    exit 1
fi

seed_url=$1
path_to_result=$2

python3 ./scripts/main.py --url $seed_url --file $path_to_result
timeout 10 wget --recursive -w 0.1 -D localhost $seed_url || true

cp test_data/result.jsonl $path_to_result
echo "Finished running"
