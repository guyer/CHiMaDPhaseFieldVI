#!/bin/bash

changed="Code has changed, please commit your changes"

for f in mprofile_*
do
    jobid=${f/mprofile_/}
    if label=$(./find_sumatra_for_jobid.sh $jobid); then
	if [ "$label" != "" ]; then
	    echo mv $f Data/${label}/mprofile.dat
	    mv $f Data/${label}/mprofile.dat
	elif grep --quiet "$changed" qsublogs/*.o${jobid}; then
	    echo rm $f
	    rm $f
	fi
    fi
done
