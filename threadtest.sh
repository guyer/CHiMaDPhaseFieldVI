#!/bin/bash
# invoke with
# $ sbatch --array=0-5 --ntasks=32 threadtest.sh

#SBATCH --job-name=threads
#SBATCH --workdir=/data/guyer/CHiMaDPhaseFieldVI

source activate petsc37

NTHREADS=$(( 2**SLURM_ARRAY_TASK_ID ))
NSLOTS=$SLURM_NTASKS
NCPUS=$(( NSLOTS / NTHREADS ))

export OMP_NUM_THREADS=$NTHREADS
FIPY_SOLVERS=petsc /data/guyer/miniconda3/envs/petsc37/bin/mpiexec -n 1 smt run --tag threads2 --tag petsc -n $NCPUS --main threadtest.py params.yaml nthreads=$NTHREADS ncpus=$NCPUS nslots=$NSLOTS $@
