#!/bin/sh

#SBATCH  --partition=small-short
#SBATCH --job-name=rh347SAT
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

#SBATCH --array=1-3048

python3 data/satinput.py

srun `sed -n "$SLURM_ARRAY_TASK_ID"p satcommands`
