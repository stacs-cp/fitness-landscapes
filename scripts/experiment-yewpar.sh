#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."
source scripts/experiment-common.sh

commands_file=yewparcommands

python3 scripts/create-yewpar-commands.py "$@" --commands-file "$commands_file"

command_count=$(experiment_count_commands "$commands_file")
if [[ $command_count -eq 0 ]]; then
    echo "No YewPar commands generated; not updating SLURM or submitting."
    exit 0
fi

experiment_render_slurm scripts/yewpar.slurm.template scripts/sat-count.slurm "$command_count"
echo "Rendered scripts/sat-count.slurm with $command_count array task(s)."

experiment_submit scripts/sat-count.slurm
