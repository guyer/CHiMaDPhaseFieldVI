#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

export OMP_NUM_THREADS=1

nx=`python -c "print 100 * 2**($SGE_TASK_ID - 1)"`

if [ "$SGE_TASK_ID" == "undefined" ]; then
    OUTPUT="${JOB_ID}"
else
    OUTPUT="${JOB_ID}.${SGE_TASK_ID}"
fi

OUTPUT="mprofile_${OUTPUT}"

mprof run --include-children --multiprocess --output $OUTPUT smt run --tag meshsize --main initializer7a.py params.yaml  nx=$nx dt=1.e-4 checkpoint=1.e-2 nthreads=$OMP_NUM_THREADS ncpus=$NSLOTS nslots=$NSLOTS $@
