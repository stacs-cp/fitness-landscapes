#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."
source scripts/experiment-common.sh

commands_file=satcommands

python3 scripts/create-sat-commands-counting.py "$@" --commands-file "$commands_file"

command_count=$(experiment_count_commands "$commands_file")
if [[ $command_count -eq 0 ]]; then
    echo "No SAT count commands generated; not updating SLURM or submitting."
    exit 0
fi

experiment_render_slurm scripts/sat-count.slurm.template scripts/sat-count.slurm "$command_count"
echo "Rendered scripts/sat-count.slurm with $command_count array task(s)."

experiment_submit scripts/sat-count.slurm
