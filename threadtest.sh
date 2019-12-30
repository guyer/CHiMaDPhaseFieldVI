#!/bin/bash
# invoke with
# $ sbatch --array=0-5 --ntasks=32 threadtest.sh

#SBATCH --job-name=threads
#SBATCH --workdir=/data/guyer/CHiMaDPhaseFieldVI

source activate petsc27

NTHREADS=$(( 2**SLURM_ARRAY_TASK_ID ))
NSLOTS=$SLURM_NTASKS
NCPUS=$(( NSLOTS / NTHREADS ))

export OMP_NUM_THREADS=$NTHREADS
FIPY_SOLVERS=trilinos /data/guyer/miniconda3/envs/petsc27/bin/mpiexec -n 1 smt run --tag trilinos -n $NCPUS --main threadtest.py params.yaml nthreads=$NTHREADS ncpus=$NCPUS nslots=$NSLOTS $@
