#!/bin/sh

#SBATCH  --partition=debug
#SBATCH --job-name=rh347test
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G

#SBATCH --array=1-$(wc -l testcommands)

echo test > test.txt
echo test1 > test1.txt
echo test2 > test2.txt  

srun `sed -n "$SLURM_ARRAY_TASK_ID"p testcommands`