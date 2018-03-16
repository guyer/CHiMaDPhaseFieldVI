#!/bin/bash

jobid=$1
prefix="Record label for this run: "
line=$(grep "$prefix" qsublogs/*.o${jobid})
if [ "$line" != "" ]; then
    line=${line/$prefix/}
    echo ${line//\'/}
else
    prefix="storing results in /data/guyer/CHiMaDPhaseFieldVI/Data/"
    line=$(grep "$prefix" qsublogs/*.o${jobid})
    echo ${line/$prefix/}
fi
