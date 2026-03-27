#!/bin/sh

#SBATCH  --partition=small-short
#SBATCH --job-name=rh347DEC
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G

#SBATCH --array=1-195

srun `sed -n "$SLURM_ARRAY_TASK_ID"p satcommandsDEC`
