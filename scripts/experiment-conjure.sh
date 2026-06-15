#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."
source scripts/experiment-common.sh

commands_file=cpcommands

python3 scripts/create-essence-commands.py "$@" --commands-file "$commands_file"

command_count=$(experiment_count_commands "$commands_file")
if [[ $command_count -eq 0 ]]; then
    echo "No Conjure commands generated; not updating SLURM, warming cache, or submitting."
    exit 0
fi

experiment_render_slurm scripts/essence.slurm.template scripts/essence.slurm "$command_count"
echo "Rendered scripts/essence.slurm with $command_count array task(s)."

mkdir -p output/raw/count-essence-edge-branching-full-symmetry-minion
first_command=$(experiment_first_command "$commands_file")

echo "Warming Conjure eprime cache with the first command from $commands_file."
bash -lc "$first_command"

experiment_submit scripts/essence.slurm
