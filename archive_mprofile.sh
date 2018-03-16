#!/bin/bash

for f in mprofile_*
do
    if label=$(./find_sumatra_for_jobid.sh ${f/mprofile_/}); then
	if [ "$label" != "" ]; then
	    echo mv $f Data/${label}/mprofile.dat
	    mv $f Data/${label}/mprofile.dat	    
	fi
    fi
done
