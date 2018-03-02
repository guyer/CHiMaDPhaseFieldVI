# script based on 
# https://pages.nist.gov/pfhub/benchmarks/benchmark7.ipynb

import os
import pickle
import sys
import yaml

import datreant.core as dtr

import fipy as fp
from fipy.tools import parallelComm

print "got here"

yamlfile = sys.argv[1]
startfrom = int(sys.argv[2])
numsteps = int(sys.argv[3])

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

if parallelComm.procID == 0:
    data = dtr.Treant(output)
else:
    class dummyTreant(object):
        categories = dict()

    data = dummyTreant()

if parallelComm.procID == 0:
    with open(data["symbolic.pickle"].make().abspath, 'rb') as f:
        eq_sol, eta_sol, kappa, N, t, parameters = pickle.load(f)

eq_sol, eta_sol, kappa, N, t, parameters = parallelComm.bcast((eq_sol, eta_sol, kappa, N, t, parameters))

print "and here"

# substitute coefficient values

subs = [sub.subs(parameters) for sub in (eq_sol, eta_sol)]

# generate FiPy lambda functions

from sympy.utilities.lambdify import lambdify

(eq_fp, eta_fp) = [lambdify((N[0], N[1], t), sub, modules=fp.numerix) for sub in subs]
kappa_fp = float(kappa.subs(parameters))

# load checkpoint

if parallelComm.procID == 0:
    fname = data["step{}.tar.gz".format(startfrom)].make().abspath
else:
    fname = None
fname = parallelComm.bcast(fname)

eta, _ = fp.tools.dump.read(filename=fname)

mesh = eta.mesh
xx, yy = mesh.cellCenters[0], mesh.cellCenters[1]
XX, YY = mesh.faceCenters[0], mesh.faceCenters[1]

eta.constrain(1., where=YY==0.)
eta.constrain(0., where=YY==0.5)

if parallelComm.procID == 0:
    dt = data.categories["dt_exact"]
else:
    dt = None
    
dt = parallelComm.bcast(dt)

elapsed = fp.Variable(name="$t$", value=startfrom * dt)

eq = (fp.TransientTerm() == 
      - 4 * eta * (eta - 1) * (eta - 0.5) 
      + fp.DiffusionTerm(coeff=kappa_fp) + eq_fp(xx, yy, elapsed))

for step in range(numsteps):
    eta.updateOld()
    eq.solve(var=eta, dt=dt)
    elapsed.value = elapsed() + dt

error = eta - eta_fp(xx, yy, elapsed - dt)
error.name = r"$\Delta\eta$"

if parallelComm.procID == 0:
    fname = data["step{}.tar.gz".format(startfrom + step)].make().abspath
else:
    fname = None
fname = parallelComm.bcast(fname)

print fname

fp.tools.dump.write((eta, error), filename=fname)
