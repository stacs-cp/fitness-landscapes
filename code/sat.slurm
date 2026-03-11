#!/bin/sh

#SBATCH  --partition=debug
#SBATCH --job-name=rh347SAT
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=50G

#SBATCH --array=1-5

python3 data/satinput.py

mkdir -p SATresults 

srun `sed -n "$SLURM_ARRAY_TASK_ID"p satcommands`