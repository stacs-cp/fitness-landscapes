#!/usr/bin/env bash

set -euo pipefail

experiment_count_commands() {
    local commands_file=$1
    if [[ ! -f $commands_file ]]; then
        echo "Missing command file: $commands_file" >&2
        return 1
    fi

    awk 'NF { count++ } END { print count + 0 }' "$commands_file"
}

experiment_first_command() {
    local commands_file=$1
    awk 'NF { print; exit }' "$commands_file"
}

experiment_render_slurm() {
    local template_file=$1
    local slurm_file=$2
    local command_count=$3

    sed "s/__ARRAY_COUNT__/$command_count/g" "$template_file" > "$slurm_file"
}

experiment_submit() {
    local slurm_file=$1

    sbatch "$slurm_file"
}
