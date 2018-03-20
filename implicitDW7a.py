
# script based on 
# https://pages.nist.gov/pfhub/benchmarks/benchmark7.ipynb

# sympy knows that 1/2 is 0.5, but by the time we're eval'ing
# eta_str, that information is lost
from __future__ import division

import os
import pickle
import sys
import yaml

import datreant.core as dtr

import fipy as fp
from fipy.tools import parallelComm

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
    eq_str = data.categories["eq"]
    eta_str = data.categories["eta"]
    kappa_fp = data.categories["kappa"]
else:
    eq_str = eta_str = kappa_fp = None

eq_str, eta_str, kappa_fp = parallelComm.bcast((eq_str, eta_str, kappa_fp))

from fipy.tools.numerix import tanh, sqrt, sin, cos, pi
eq_fp = eval(eq_str)
eta_fp = eval(eta_str)

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

# linearize double-well
m_eta = 2 * (1 - 2 * eta)
dm_eta_deta = -4.
DW = m_eta * eta * (eta - 1)
dDW_deta = dm_eta_deta * eta * (eta - 1) + m_eta * (2 * eta - 1)
eq = (fp.TransientTerm() == 
      (DW - dDW_deta * eta) + fp.ImplicitSourceTerm(coeff=dDW_deta)
      + fp.DiffusionTerm(coeff=kappa_fp) + eq_fp(xx, yy, elapsed))

solver = eq.getDefaultSolver()
print "solver:", repr(solver)

for step in range(1, numsteps+1):
    eta.updateOld()
    for sweep in range(params['sweeps']):
        res = eq.sweep(var=eta, dt=dt, solver=solver)
    elapsed.value = elapsed() + dt

del solver

error = eta - eta_fp(xx, yy, elapsed - dt)
error.name = r"$\Delta\eta$"

if parallelComm.procID == 0:
    fname = data["step{}.tar.gz".format(startfrom + step)].make().abspath
else:
    fname = None
fname = parallelComm.bcast(fname)

fp.tools.dump.write((eta, error), filename=fname)
