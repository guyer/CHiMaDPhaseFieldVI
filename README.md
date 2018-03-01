ATTENTION: In `distributed` launch_mode, Sumatra *must* be invoked with::

  mpiexec -n 1 smt run -n 2 --main benchmark7a.py params.yaml

to keep MPICH happy.

# Sumatra configuration

smt init --store datreant://.smt/records benchmark7
smt configure --executable python --addlabel parameters \
  --labelgenerator uuid --launch_mode distributed

# 2018-02-23T17:15:11-05:00

PyTrilinos seems to hog resources it's not entitled to due to squabbling between OpenMP and MPI. 
A job launched with $NSLOTS seems to want to create $NSLOTS MPI processes, each of which wants
to fire up as many as(?) $NSLOTS threads. Solution appears to be `export OMP_NUM_THREADS=1`.

The model may be to run 1 MPI process per rank(?), but this runs afoul of the Python GIL(?).

  https://www.mail-archive.com/fipy@nist.gov/msg03393.html

threadtest.py and threadtest.sh are designed to see of there's benefit to running, e.g., 
4 processes with 4 threads apiece on 16 slots.

# 2018-02-28T12:34:18-05:00

Something is leaking like a sieve (4 MiB / s for a 400x200 mesh). 
Killed runs and try to diagnose with memory_profiler.py.

# 2018-03-01T17:13:00-05:00

Leaking seems to be in `_PysparseMeshMatrix.asTrilinosMeshMatrix()`,
specifically with `_TrilinosMeshMatrixKeepStencil` and
`self.trilinosMatrix.addAt`. It's reasonable enough that these use memory,
but we never regain any with `_TrilinosMeshMatrixKeepStencil.flush()`.

Leaking also happens in `TrilinosAztecOOSolver._solve_()` in call to
`Solver.Iterate`.
