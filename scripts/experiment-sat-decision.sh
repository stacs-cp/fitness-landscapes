#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."
source scripts/experiment-common.sh

commands_file=satcommandsDEC

python3 scripts/create-sat-commands-decision.py "$@" --commands-file "$commands_file"

command_count=$(experiment_count_commands "$commands_file")
if [[ $command_count -eq 0 ]]; then
    echo "No SAT decision commands generated; not updating SLURM or submitting."
    exit 0
fi

experiment_render_slurm scripts/sat-decision.slurm.template scripts/sat-decision.slurm "$command_count"
echo "Rendered scripts/sat-decision.slurm with $command_count array task(s)."

experiment_submit scripts/sat-decision.slurm
