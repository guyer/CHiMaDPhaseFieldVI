#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

NTHREADS=$SGE_TASK_ID
NCPUS=4

export OMP_NUM_THREADS=$NTHREADS
mprof run --include-children --multiprocess mpiexec -n 1 smt run --tag threads -n $NCPUS --main threadtest.py params.yaml nthreads=$NTHREADS ncpus=$NCPUS nslots=$NSLOTS $@
