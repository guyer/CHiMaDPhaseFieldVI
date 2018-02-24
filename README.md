ATTENTION: In `distributed` launch_mode, Sumatra *must* be invoked with::

  mpiexec -n 1 smt run -n 2 --main benchmark7a.py params.yaml

to keep MPICH happy.


# 2018-02-23T17:15:11-05:00

PyTrilinos seems to hog resources it's not entitled to due to squabbling between OpenMP and MPI. 
A job launched with $NSLOTS seems to want to create $NSLOTS MPI processes, each of which wants
to fire up as many as(?) $NSLOTS threads. Solution appears to be `export OMP_NUM_THREADS=1`.

The model may be to run 1 MPI process per rank(?), but this runs afoul of the Python GIL(?).

  https://www.mail-archive.com/fipy@nist.gov/msg03393.html

threadtest.py and threadtest.sh are designed to see of there's benefit to running, e.g., 
4 processes with 4 threads apiece on 16 slots.