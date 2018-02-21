# script based on 
# https://pages.nist.gov/pfhub/benchmarks/benchmark7.ipynb

import fipy as fp

from sympy import Symbol, symbols, simplify, init_printing
from sympy import Eq, sin, cos, tanh, sqrt, pi
from sympy.printing import pprint
from sympy.abc import kappa, S, t, x, xi, y, alpha

from sympy.physics.vector import ReferenceFrame, dynamicsymbols, time_derivative, divergence, gradient
N = ReferenceFrame('N')
t = symbols('t')

init_printing(use_unicode=True)

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

parameters = ((kappa, 0.0004), 
              (A1, 0.0075), (B1, 8.0 * pi), 
              (A2, 0.03), (B2, 22.0 * pi), 
              (C2, 0.0625 * pi))
              
subs = [sub.subs(parameters) for sub in (eq_sol, eta_sol)]

# generate FiPy lambda functions

from sympy.utilities.lambdify import lambdify

(eq_fp, eta_fp) = [lambdify((N[0], N[1], t), sub, modules=fp.numerix) for sub in subs]
kappa_fp = float(kappa.subs(parameters))

# solve

dt = 1e-2
Lx = 1.
Ly = 0.5

nx = 100

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
    
deta = eta - eta_fp(xx, yy, time - dt)

