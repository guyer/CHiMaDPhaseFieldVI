#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

solver="GMRES"
preconditioner="None"
tolerance=1.e-10
iterations=1000
sweeps=5

export OMP_NUM_THREADS=1

if [ "$SGE_TASK_ID" == "undefined" ]; then
    OUTPUT="${JOB_ID}"
else
    OUTPUT="${JOB_ID}.${SGE_TASK_ID}"
fi

OUTPUT="mprofile_${OUTPUT}"

mprof run --include-children --multiprocess --output $OUTPUT smt run --tag optimize --main optimizer7bDriver.py optimizer.yaml nthreads=$OMP_NUM_THREADS ncpus=$NSLOTS nslots=$NSLOTS nproc=$NSLOTS solver=$solver preconditioner=$preconditioner tolerance=$tolerance iterations=$iterations sweeps=$sweeps $@
