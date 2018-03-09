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

Filed https://github.com/trilinos/Trilinos/issues/2327

# 2018-03-05-10:00:00-05:00

Implemented a scheme to dispatch job in chunks (`initializer7a.py` calls
`leaker7a.py`) so that we can periodically clear the PyTrilinos memory
leak.

Note: Sloppy development practice led to way too much time debugging
red herrings. Call chain needs to be `mpiexec` -> `mprof` ->
`smt` -> `python initializer7a.py` -> `mpirun` -> `python leaker7a.py`.
Because of all of this redirection, spent a lot of time trying to decypher
broken pipes, mpi behavior, and how sumatra stores things, when the
reality was that `leaker7a.py` was just buggy.

**BREAK THINGS INTO PIECES AND DIAGNOSE EACH ONE!!!**


# 2018-03-05-13:47:00-05:00

Script failed to pickle checkpoints in parallel:

    Traceback (most recent call last):
      File "leaker7a.py", line 96, in <module>
        fp.tools.dump.write((eta, error), filename=fname)
      File "/Users/guyer/Documents/research/FiPy/fipy/fipy/tools/dump.py", line 83, in write
        cPickle.dump(data, fileStream, 0)
      File "/Users/guyer/anaconda/envs/fipy/lib/python2.7/copy_reg.py", line 84, in _reduce_ex
        dict = getstate()
      File "/Users/guyer/Documents/research/FiPy/fipy/fipy/variables/cellVariable.py", line 533, in __getstate__
        'value' : self.globalValue,
      File "/Users/guyer/Documents/research/FiPy/fipy/fipy/variables/cellVariable.py", line 162, in globalValue
        self.mesh._globalNonOverlappingCellIDs)
      File "/Users/guyer/Documents/research/FiPy/fipy/fipy/variables/meshVariable.py", line 152, in _getGlobalValue
        globalIDs = numerix.concatenate(self.mesh.communicator.allgather(globalIDs))
    ValueError: zero-dimensional arrays cannot be concatenated

Initially, I thought this was due to
https://github.com/usnistgov/fipy/issues/518, but it happens with a
`Grid2D` as well.

Ultimately determined that this is caused by `initializer7a.py` running in
serial, and so `step0.tar.gz` is pickled with a generic
`ParallelCommWrapper`, which doesn't know how to gather the result when
it's unpickled in parallel. There's no reason to pickle the communicator
with the mesh... which [Wheeler identified four years
ago](https://github.com/usnistgov/fipy/pull/420). Accepted this pull
request and pickling/unpickling works.


# 2018-03-06-16:08:00-05:00

## What is impact of running `mprof` on performance?

### With `mprof`, 2 process parallel

4:04 for 100 steps

### Without `mprof`, 2 process parallel

4:39 for 100 steps

(was running YouTube in background)

### Without `mprof`, serial, PySparse

2:52 for 100 steps

### Without `mprof`, 2 process parallel, `OMP_NUM_THREADS=1`

4:18 for 100 steps

### Conclusion

`mprof` doesn't affect performance (at least at default 0.1 s sampling
rate).

`OMP_NUM_THREADS` doesn't matter, at least on my little 2 core MacBook Pro


# 2018-03-08T16:00:00+19:00

Running time order of accuracy. Scheme for calculating chunk size is too 
complicated (and doesn't work); ditch it.

# 2018-03-08T23:10:09+19:00

`smt run --tag` - the tag is not applied until the end?

