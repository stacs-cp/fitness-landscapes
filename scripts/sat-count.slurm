#!/bin/sh

#SBATCH  --partition=small-short
#SBATCH --job-name=rh347SAT
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G

#SBATCH --array=1-3048%15

srun `sed -n "$SLURM_ARRAY_TASK_ID"p satcommands`
