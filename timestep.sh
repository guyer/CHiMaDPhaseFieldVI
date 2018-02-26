#!/bin/bash
source activate fipy
cd /data/guyer/CHiMaDPhaseFieldVI

export OMP_NUM_THREADS=1

exp=$(awk "BEGIN {print $SGE_TASK_ID / 2}")

mpiexec -n 1 smt run --tag timestep -n $NSLOTS --main benchmark7a.py params.yaml  dt=1.e-${exp} $@
