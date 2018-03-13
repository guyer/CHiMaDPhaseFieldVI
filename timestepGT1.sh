#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

export OMP_NUM_THREADS=1

dt=$(python -c "print 10**(($SGE_TASK_ID - 1) / 2.)")

if [ "$SGE_TASK_ID" == "undefined" ]; then
    OUTPUT="${JOB_ID}"
else
    OUTPUT="${JOB_ID}.${SGE_TASK_ID}"
fi

OUTPUT="mprofile_${OUTPUT}"

mprof run --include-children --multiprocess --output $OUTPUT smt run --tag timestep --main initializer7a.py params.yaml nx=800 dt=$dt checkpoint=1.e-1 nthreads=$OMP_NUM_THREADS ncpus=$NSLOTS nslots=$NSLOTS nproc=$NSLOTS $@
