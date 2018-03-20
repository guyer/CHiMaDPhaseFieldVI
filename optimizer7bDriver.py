# script based on 
# https://pages.nist.gov/pfhub/benchmarks/benchmark7.ipynb

import os
import pickle
import platform
import subprocess
import sys
import time
import yaml

import datreant.core as dtr

import fipy as fp

yamlfile = sys.argv[1]

with open(yamlfile, 'r') as f:
    params = yaml.load(f)

try:
    from sumatra.projects import load_project
    project = load_project(os.getcwd())
    record = project.get_record(params["sumatra_label"])
    output = record.datastore.root
except:
    # either there's no sumatra, no sumatra project, or no sumatra_label
    # this will be the case if this script is run directly
    output = os.getcwd()

print "storing results in {0}".format(output)
data = dtr.Treant(output)

# initialize and store variables

totaltime = params['totaltime']
dt = float(params['dt'])

data.categories["numsteps"] = int(totaltime / dt)
data.categories["dt_exact"] = totaltime / data.categories["numsteps"]

if params['nproc'] > 1:
    cmd = ["mpirun", "-n", str(params['nproc']), "--wdir", os.getcwd()]
else:
    cmd = []
    
cmd += [sys.executable, params['script'], yamlfile]

start = time.time()

chunk = 1000

for startfrom in range(0, data.categories["numsteps"], chunk):
    thischunk = min(chunk, data.categories["numsteps"] - startfrom)
    cmdstr = " ".join(cmd + [str(startfrom), str(thischunk)])
    p = subprocess.Popen(cmdstr, shell=True, 
                         close_fds=(platform.system() == 'Linux'))
    ret = p.wait()
    if ret != 0:
        raise RuntimeError("""\
{}
returned: {}""".format(cmdstr, ret))

end = time.time()

data.categories["solvetime"] = end - start



