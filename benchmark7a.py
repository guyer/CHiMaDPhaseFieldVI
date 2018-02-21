# script based on 
# https://pages.nist.gov/pfhub/benchmarks/benchmark7.ipynb

import os
import sys
import yaml

import datreant.core as dtr

import fipy as fp
from fipy.tools import parallelComm

yamlfile = sys.argv[1]

with open(yamlfile, 'r') as f:
    params = yaml.load(f)

try:
    from sumatra.projects import load_project
    print "os.getcwd():", os.getcwd()
    project = load_project(os.getcwd())
    print "project:", project
    print "sumatra_label:", params["sumatra_label"]
    record = project.get_record(params["sumatra_label"])
    print "record:", record
    output = record.datastore.root
    print "output:", output
except:
    # either there's no sumatra, no sumatra project, or no sumatra_label
    # this will be the case if this script is run directly
    output = os.getcwd()

if parallelComm.procID == 0:
    print "storing results in {0}".format(output)
    data = dtr.Treant(output)
else:
    class dummyTreant(object):
        categories = dict()

    data = dummyTreant()

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

                  
# substitute coefficient values

parameters = ((kappa, params['kappa']),
              (A1, 0.0075), (B1, 8.0 * pi), 
              (A2, 0.03), (B2, 22.0 * pi), 
              (C2, 0.0625 * pi))
              
subs = [sub.subs(parameters) for sub in (eq_sol, eta_sol)]

# generate FiPy lambda functions

from sympy.utilities.lambdify import lambdify

(eq_fp, eta_fp) = [lambdify((N[0], N[1], t), sub, modules=fp.numerix) for sub in subs]
kappa_fp = float(kappa.subs(parameters))

# solve

dt = params['dt']
Lx = params['Lx']
Ly = params['Ly']

nx = params['nx']

ny = int(nx * Ly / Lx)
dx = Lx / nx
dy = Ly / ny

mesh = fp.PeriodicGrid2DLeftRight(nx=nx, dx=dx, ny=ny, dy=dx)
xx, yy = mesh.cellCenters[0], mesh.cellCenters[1]
XX, YY = mesh.faceCenters[0], mesh.faceCenters[1]

time = fp.Variable(name="$t$", value=0.)

eta = fp.CellVariable(mesh=mesh, name="$eta$", hasOld=True)
eta.constrain(1., where=YY==0.)
eta.constrain(0., where=YY==0.5)

eta.value = eta_fp(xx, yy, 0.)

eq = (fp.TransientTerm() == 
      - 4 * eta * (eta - 1) * (eta - 0.5) 
      + fp.DiffusionTerm(coeff=kappa_fp) + eq_fp(xx, yy, time))

while time.value <= 8.0:
    eta.updateOld()
    eq.solve(var=eta, dt=dt)
    time.value = time() + dt
    
error = eta - eta_fp(xx, yy, time - dt)
error.name = r"$\Delta\eta$"

fp.tools.dump.write((eta, error),
                    filename=data["eta.tar.gz"].make().abspath)
