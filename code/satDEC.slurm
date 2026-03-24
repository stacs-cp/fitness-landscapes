#!/bin/sh

#SBATCH  --partition=debug
#SBATCH --job-name=rh347DEC
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G

#SBATCH --array=1-10

python3 data/satinputDEC.py

srun `sed -n "$SLURM_ARRAY_TASK_ID"p satcommandsDEC`
