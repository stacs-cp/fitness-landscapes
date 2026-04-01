#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."
find tables -type f -name '*.csv' -print0 | parallel -0 --no-notice python3 code/csv_heatmap.py
