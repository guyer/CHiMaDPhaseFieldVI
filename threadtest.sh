#!/bin/bash
# invoke with
# $ sbatch --array=0-5 --ntasks=32 threadtest.sh <env> <solver> <tag>

#SBATCH --job-name=threads
#SBATCH --workdir=/data/guyer/CHiMaDPhaseFieldVI

CONDAENV=$1
SOLVER=$2
TAG=$3

shift
shift
shift

source /data/guyer/miniconda3/bin/activate $CONDAENV

NTHREADS=$(( 2**SLURM_ARRAY_TASK_ID ))
NSLOTS=$SLURM_NTASKS
NCPUS=$(( NSLOTS / NTHREADS ))


export OMP_NUM_THREADS=$NTHREADS
# mprof run --interval 1.0 --include-children --multiprocess --output "/working/guyer/mprofile-${SOLVER}-${NCPUS}cpus-${NTHREADS}threads.dat"
FIPY_SOLVERS=$SOLVER mpiexec -n 1 smt run --tag $TAG -n $NCPUS --executable python --main threadtest.py params.yaml nthreads=$NTHREADS ncpus=$NCPUS nslots=$NSLOTS solver=$SOLVER $@
