#!/bin/bash

jobid=$1
prefix="Record label for this run: "
line=$(grep "$prefix" qsublogs/*.o${jobid})
line=${line/$prefix/}
echo ${line//\'/}
