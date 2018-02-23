ATTENTION: In `distributed` launch_mode, Sumatra *must* be invoked with::

  mpiexec -n 1 smt run -n 2 --main benchmark7a.py params.yaml

to keep MPICH happy.



# Sumatra configuration

smt init --store datreant://.smt/records benchmark7
smt configure --executable python --addlabel parameters \
  --labelgenerator uuid --launch_mode distributed