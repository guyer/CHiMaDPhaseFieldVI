# script based on 
# https://pages.nist.gov/pfhub/benchmarks/benchmark7.ipynb

import os
import pickle
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

from sympy import Symbol, symbols, simplify, init_printing
from sympy import Eq, sin, cos, tanh, sqrt, pi
from sympy.printing import pprint
from sympy.abc import kappa, S, t, x, xi, y, alpha

from sympy.physics.vector import ReferenceFrame, dynamicsymbols, time_derivative, divergence, gradient
N = ReferenceFrame('N')
t = symbols('t')

# symbolic form

# alpha = symbols('a')
A1, A2 = symbols('A1 A2')
B1, B2 = symbols('B1 B2')
C2 = symbols('C2')

# Define interface offset (alpha)
alpha = 0.25 + A1 * t * sin(B1 * N[0]) + A2 * sin(B2 * N[0] + C2 * t)

# Define the solution equation (eta)
xi = (N[1] - alpha) / sqrt(2*kappa)
eta_sol = (1 - tanh(xi)) / 2

eq_sol = simplify(time_derivative(eta_sol, N)
                  + 4 * eta_sol * (eta_sol - 1) * (eta_sol - 0.5) 
                  - divergence(kappa * gradient(eta_sol, N), N))

parameters = ((kappa, params['kappa']),
              (A1, 0.0075), (B1, 8.0 * pi), 
              (A2, 0.03), (B2, 22.0 * pi), 
              (C2, 0.0625 * pi))

with open(data["symbolic.pickle"].make().abspath, 'wb') as f:
    pickle.dump((eq_sol, eta_sol, kappa, N, t, parameters), f, pickle.HIGHEST_PROTOCOL)

# initialize and store variables

totaltime = params['totaltime']
dt = params['dt']
Lx = params['Lx']
Ly = params['Ly']

nx = params['nx']

ny = int(nx * Ly / Lx)
dx = Lx / nx
dy = Ly / ny

mesh = fp.PeriodicGrid2DLeftRight(nx=nx, dx=dx, ny=ny, dy=dx)
xx, yy = mesh.cellCenters[0], mesh.cellCenters[1]

eta = fp.CellVariable(mesh=mesh, name="$eta$", hasOld=True)
eta.value = eta_fp(xx, yy, 0.)

error = eta - eta_fp(xx, yy, 0.)
error.name = r"$\Delta\eta$"

fname = data["step0.tar.gz"].make().abspath
fp.tools.dump.write((eta, error), filename=fname)

dt.categories["numsteps"] = int(totaltime / dt)
data.categories["dt_exact"] = totaltime / dt.categories["numsteps"]

if params['nproc'] > 1:
    cmd = ["mpirun", "-n", params['nproc'], "--wdir", os.getcwd()]
else:
    cmd = []
    
cmd += [sys.executable, "leaker7a.py", yamlfile]
       
start = time.time()

chunk = 1000
numchunks = int(data["numsteps"] / chunk)
chunk = int(data["numsteps"] / numchunks)

for startfrom in range(0, data["numsteps"], chunk):
    p = subprocess.Popen(cmd + [str(startfrom), str(chunk)], cwd=os.getcwd(), shell=True, 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=(platform.system() == 'Linux'))
    p.wait()

end = time.time()

data.categories["solvetime"] = end - start



