#!/bin/bash
# invoke with
# $ sbatch --array=0-5 --ntasks=32 threadtest.sh <env> <solver>

#SBATCH --job-name=threads
#SBATCH --workdir=/data/guyer/CHiMaDPhaseFieldVI

CONDAENV=$1
SOLVER=$2

shift
shift

/data/guyer/miniconda3/bin/activate $CONDAENV

NTHREADS=$(( 2**SLURM_ARRAY_TASK_ID ))
NSLOTS=$SLURM_NTASKS
NCPUS=$(( NSLOTS / NTHREADS ))


export OMP_NUM_THREADS=$NTHREADS
FIPY_SOLVERS=$SOLVER /data/guyer/miniconda3/envs/$CONDAENV/bin/mpiexec -n 1 smt run --tag thread3 -n $NCPUS --main threadtest.py params.yaml nthreads=$NTHREADS ncpus=$NCPUS nslots=$NSLOTS solver=$SOLVER $@
