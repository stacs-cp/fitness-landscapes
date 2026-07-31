#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."
find output -type f -name '*.csv' -print0 | parallel -0 --no-notice python3 scripts/csv-heatmap.py
