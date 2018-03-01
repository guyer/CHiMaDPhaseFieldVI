#!/bin/bash
#SBATCH --partition rack1  # -p, partition
#SBATCH --time 12:00:00    # -t, time (hh:mm:ss or dd-hh:mm:ss)
#SBATCH --nodes=1          # total number of machines
#SBATCH --ntasks=2         # 64 MPI ranks per rack6 node
#SBATCH -J benchmark7
#SBATCH -D /data/guyer/CHiMaDPhaseFieldVI

source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI
mpiexec -n 1 smt run -n $SLURM_CPUS_PER_TASK --main benchmark7a.py params.yaml
