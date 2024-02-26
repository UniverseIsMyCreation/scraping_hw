#!/usr/bin/env bash

set -eu

mkdir -p real_results
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
