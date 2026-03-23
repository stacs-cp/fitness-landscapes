#!/bin/sh

#SBATCH  --partition=large-short
#SBATCH --job-name=rh347DEC
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G

#SBATCH --array=1-3048

python3 data/satinput.py

srun `sed -n "$SLURM_ARRAY_TASK_ID"p satcommandsDEC`
