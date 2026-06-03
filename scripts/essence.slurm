#!/bin/sh

#SBATCH  --partition=large-short
#SBATCH --job-name=rh347CP
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G

#SBATCH --array=1-3048%20

srun `sed -n "$SLURM_ARRAY_TASK_ID"p cpcommands`
