#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI
export OMP_NUM_THREADS=$NSLOTS
mpiexec -n 1 smt run -n $NSLOTS --main benchmark7a.py params.yaml $@
