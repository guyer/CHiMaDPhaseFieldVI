#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

NTHREADS=$(( 2**(SGE_TASK_ID-1) ))
NCPUS=$(( NSLOTS / NTHREADS ))

export OMP_NUM_THREADS=$NTHREADS
mpiexec -n 1 smt run --tag threads -n $NCPUS --main threadtest.py params.yaml nthreads=$NTHREADS ncpus=$NCPUS nslots=$NSLOTS $@
