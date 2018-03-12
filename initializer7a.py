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

# substitute coefficient values

subs = [sub.subs(parameters) for sub in (eq_sol, eta_sol)]

# generate FiPy lambda functions

from sympy.utilities.lambdify import lambdify, lambdastr

(eq_fp, eta_fp) = [lambdify((N[0], N[1], t), sub, modules=fp.numerix) for sub in subs]
kappa_fp = float(kappa.subs(parameters))

# Can't pickle lambda functions

(eq_str, eta_str) = [lambdastr((N[0], N[1], t), sub) for sub in subs]

data.categories["eq"] = eq_str
data.categories["eta"] = eta_str
data.categories["kappa"] = kappa_fp

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
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         close_fds=(platform.system() == 'Linux'))

    p.wait()

end = time.time()

data.categories["solvetime"] = end - start



