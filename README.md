ATTENTION: In `distributed` launch_mode, Sumatra *must* be invoked with::

  mpiexec -n 1 smt run -n 2 --main benchmark7a.py params.yaml

to keep MPICH happy.

ATTENTION: In `serial` launch_mode, Sumatra *must* *not* be invoked with::

  mpiexec -n 1 smt run --main initializer7a.py params.yaml nproc=2

to keep MPICH happy even though `initializer7a.py` invokes `mpirun`.

# Needed for simulation

conda install --channel conda-forge sympy
pip install -e /data/guyer/fipy

# Sumatra installation

pip install -e /data/guyer/sumatra
conda install --channel conda-forge datreant "gitpython>=2.1.8" pyyaml
cp /data/guyer/sumatra/sumatra/pfi.py /path/to/conda/env/bin/

NOTE: As of 2019-12-28, Sumatra has not been updated to Python 3.8 and has a number of incompatibilities

# Sumatra configuration

smt init --store datreant://.smt/records benchmark7
smt configure --executable python --addlabel parameters \
  --labelgenerator uuid --launch_mode distributed



# timestep.sh

Invoked on Sun Grid Engine with:

    qsub -t 1-10 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=8.
