#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

NTHREADS=$SGE_TASK_ID
NCPUS=4

export OMP_NUM_THREADS=$NTHREADS
mpiexec -n 1 mprof run --include-children --multiprocess smt run --tag threads -n $NCPUS --main threadtest.py params.yaml nthreads=$NTHREADS ncpus=$NCPUS nslots=$NSLOTS $@
