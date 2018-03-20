#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

solvers=("Bicgstab" "CGS" "GMRES" "LU" "PCG")
preconditioners=("None" "DomDecomp" "IC" "Jacobi" "MultilevelDDML" "MultilevelDD" "MultilevelNSSA" "MultilevelSAS" "MultilevelSGS" "MultilevelSolverSmoother")
tolerances=(1.e-4 1.e-6 1.e-8 1.e-10 1.e-12)
iterationses=(100 316 1000 3162)
sweepses=(1 2 4 8 16)

RANDOM=$$$(date +%s)

solver=${solvers[$RANDOM % ${#solvers[@]} ]}
preconditioner=${preconditioners[$RANDOM % ${#preconditioners[@]} ]}
tolerance=${tolerances[$RANDOM % ${#tolerances[@]} ]}
iterations=${iterationses[$RANDOM % ${#iterationses[@]} ]}
sweeps=${sweepses[$RANDOM % ${#sweepses[@]} ]}

export OMP_NUM_THREADS=1

if [ "$SGE_TASK_ID" == "undefined" ]; then
    OUTPUT="${JOB_ID}"
else
    OUTPUT="${JOB_ID}.${SGE_TASK_ID}"
fi

OUTPUT="mprofile_${OUTPUT}"

mprof run --include-children --multiprocess --output $OUTPUT smt run --tag optimize --main optimizer7b.py optimizer.yaml nthreads=$OMP_NUM_THREADS ncpus=$NSLOTS nslots=$NSLOTS nproc=$NSLOTS solver=$solver preconditioner=$preconditioner tolerance=$tolerance iterations=$iterations sweeps=$sweeps $@
