ATTENTION: In `distributed` launch_mode, Sumatra *must* be invoked with::

  mpiexec -n 1 smt run -n 2 --main benchmark7a.py params.yaml

to keep MPICH happy.

ATTENTION: In `serial` launch_mode, Sumatra *must* *not* be invoked with::

  mpiexec -n 1 smt run --main initializer7a.py params.yaml nproc=2

to keep MPICH happy even though `initializer7a.py` invokes `mpirun`.


# Sumatra configuration

smt init --store datreant://.smt/records benchmark7
smt configure --executable python --addlabel parameters \
  --labelgenerator uuid --launch_mode distributed



# timestep.sh

Invoked on Sun Grid Engine with:

    qsub -t 1-10 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=8.
