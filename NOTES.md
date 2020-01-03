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

# 2018-03-12T15:49:43-04:00

Forked `leaker7a.py` into `explicitDW7a.py` (unchanged) and
`implicitDW7a.py`, which uses a linearized source and `ImplicitSourceTerm`.
At least for a coarse mesh (`nx = 100`) and moderately large timesteps (`dt
= 1.e-2`), there is no benefit, in the form of reduced error, for paying
the additional cost of sweeping.

With explicit double well, L2 error     = 0.006718338421993382
With semiimplicit double well, L2 error = 0.0067417573984172039

Daniel thinks timestep is too *small* to benefit from sweeping.

# 2018-03-13T12:00:00-04:00

Daniel's hypothesis confirmed. For large timesteps, semi-implicit error is 
O(1/10) of explicit error. Doesn't seem to scale O(1) at any point; 
smoothly varies from O(0) to something > 1.

# 2018-03-15T08:55:02-04:00

YAML has a particular and restrictive notion of [scientific 
notation](http://yaml.org/type/float.html). Interestingly, the regexp 
`[-+]?([0-9][0-9_]*)?\.[0-9.]*([eE][-+][0-9]+)?` does not agree with the 
"canonical" form `[-]?0\.([0-9]*[1-9])?e[-+](0|[1-9][0-9]+)`. 

Sticking with the regexp, since that's what's [implemented in
PyYAML](https://github.com/yaml/pyyaml/blob/93694d3e42b0cfd460f42beb75910aacacd9b5d2/lib3/yaml/resolver.py#L179):
`[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?`, we see that the 
significand *must* include a decimal point and the exponent *must* include a sign. 
Thus, "`1e3`" would not be accepted:

    >>> yaml.load("""
    ... a: 1.e+3
    ... b: 1e+3
    ... c: 1.e3
    ... d: 1e3
    ... """)
    {'a': 1000.0, 'c': '1.e3', 'b': '1e+3', 'd': '1e3'}

As this is less considerably less tolerant than Python:

    >>> dict(
    ... a=1.e+3,
    ... b=1e+3,
    ... c=1.e3,
    ... d=1e3)
    {'a': 1000.0, 'c': 1000.0, 'b': 1000.0, 'd': 1000.0}

I must ensure that my imput files are properly formatted and that 
Sumatra(?) isn't doing anything to muck things up.

# 2018-03-16T09:55:37-04:00

I still don't understand piping. 

Branched to `piiping` and created `caller.py` and `callee.py` to test 
things.

## ba9b2ef81e5241b1b1e496bd5b091615e2095f0c

    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 0 10
    0
    1
    2
    3
    4
    5
    6
    7
    8
    9
    0
    1
    2
    3
    4
    5
    6
    7
    8
    9
    0
    1
    2
    3
    4
    5
    6
    7
    8
    9
    0
    1
    2
    3
    4
    5
    6
    7
    8
    9
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 10 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 20 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 30 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 40 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 50 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 60 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 70 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 80 10
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 90 10

## 13cc7eb9042dd17bdfb504bbca41312f760f4ff7

reduced output

    $ python caller.py
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 0 3
    0
    1
    2
    0
    1
    2
    0
    1
    2
    0
    1
    2
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 3 3
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 6 3

## edd8b09129cad865d93e4b785eb03405a8bd230c

Took out pipes and used default dispatching of STDOUT/STDERR

    $ python caller.py
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 0 3
    0
    1
    2
    0
    1
    2
    0
    1
    2
    0
    1
    2
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 3 3
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 6 3

## 6da97c7164c42ab6721fb1fded15930b94a5b801

Raised an exception in `callee.py`

    $ python caller.py
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 0 3
    0
    Traceback (most recent call last):
     File "callee.py", line 8, in <module>
    0
    Traceback (most recent call last):
     File "callee.py", line 8, in <module>
       raise Exception("STOP!!!")
    Exception: STOP!!!
    0
    Traceback (most recent call last):
     File "callee.py", line 8, in <module>
    0
    Traceback (most recent call last):
     File "callee.py", line 8, in <module>
       raise Exception("STOP!!!")
    Exception: STOP!!!
       raise Exception("STOP!!!")
    Exception: STOP!!!
       raise Exception("STOP!!!")
    Exception: STOP!!!
    Traceback (most recent call last):
     File "caller.py", line 28, in <module>
       returned: {}""".format(cmdstr, ret))
    RuntimeError: mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 0 3
    returned: 1

## 

Removed the re-raise in `caller.py`

    $ python caller.py
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 0 3
    0
    Traceback (most recent call last):
      File "callee.py", line 8, in <module>
    0
    Traceback (most recent call last):
      File "callee.py", line 8, in <module>
    0
    Traceback (most recent call last):
      File "callee.py", line 8, in <module>
        raise Exception("STOP!!!")
    Exception: STOP!!!
        raise Exception("STOP!!!")
    Exception: STOP!!!
        raise Exception("STOP!!!")
    Exception: STOP!!!
    0
    Traceback (most recent call last):
      File "callee.py", line 8, in <module>
        raise Exception("STOP!!!")
    Exception: STOP!!!
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 3 3
    mpirun -n 4 --wdir /data/guyer/CHiMaDPhaseFieldVI /data/guyer/miniconda2/envs/fipy/bin/python callee.py 6 3

It's odd that the loop keeps iterating (not odd) but the subprocesses 
don't raise any more errors (odd).

Seems like it's uneccessary (and undesirable) to connect the PIPEs and 
rebroacast them (since we're not trying to do anything with them in 
`caller.py`, but we do need to catch script failure and raise an exception.


# 2018-03-20T09:59:47-04:00

Experiment with working around the [PyTrilinos memory leak](https://github.com/trilinos/Trilinos/issues/2327)

Branched fipy to `reuse_trilinos_matrix`.

## fipy: e8a2a1776758bb97b966fbb78098785e7748ed02

Commented out deletion of matrix and vectors. 

### Run 03c90a76087e

Still leaks. Aha, the solver goes out of scope every sweep.

## CHiMaDPhaseFieldVI: 133da982a480d7f3754597c4257e886817c0d5f8

Create an explicit solver so that matrix doesn't get deleted

### Run 4f07000016ff

Doesn't leak!!!

## Compare run times

ATTENTION: Due to dain bramaged security policy, ssh connections time out 
after ~1800 s (doesn't happen to ruth because it's a "server" and Andrew 
was able to get a waiver). 

Because of this, rerun for only `totaltime=1.`


### CHiMaDPhaseFieldVI: 06934b92acb169d44ab95c2d1a38579f1587127c

maxmem: 3304 MiB
runtime: 7:06

### CHiMaDPhaseFieldVI: 133da982a480d7f3754597c4257e886817c0d5f8

maxmem: 2091 MiB
runtime: 5:43

Great! Saves memory *and* time.

# 2018-03-20T14:57:54-04:00

Raises warning:

    Attempting to use an MPI routine after finalizing MPICH

## f0ee14ece54c064ac550f869edf03d704fd27526

Deleting solver after use prevents complaint from MPI


# 2018-03-20T18:30:00-04:00

`optimizer*.(sh,py,yaml)` developed to randomly sample solvers, 
preconditioners, tolerances, iterations, and sweeps.

Early results show pretty substantial variation in runtime ~4x. After
initial runs, I limit runs to 5 min with `qsub -l h_rt=0:05:00`; with some
finishing in ~40 s, who cares about really slow ones? Could probably
terminate even earlier.

All results caming in with exactly the same error? I've looked to see if 
I'm messing up error calculation, but I don't see how. All run with `nx=400` and 
`dt=1.e-2`. Maybe error is mesh size dominated? Rerun `timestep.sh` with 
`nx=400` to see.


# 2018-03-21T09:29:55-04:00

    $ qsub -t 1-6 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=1. nx=400
    Your job-array 3594192.1-6:1 ("timestep.sh") has been submitted

Error does bottom out at ~dt=1.e-2, but at ~0.00022, not 0.022

# 2018-03-21T22:56:04+20:00

Arghh!!! Ran with `explictDW7a.py`, not `implicitDW7a.py`.

    $ qsub -t 1-6 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=1. nx=400 script=implicitDW7a.py
    Your job-array 3594195.1-6:1 ("timestep.sh") has been submitted

OK, that's the error I was getting before, ~0.022, but it's basically 
constant and gets smaller with increasing timestep?

Try putting error offset back the way it was.

    $ qsub -t 1-6 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=1. nx=400 script=implicitDW7a.py
    Your job-array 3594196.1-6:1 ("timestep.sh") has been submitted

# 2018-03-22T13:47:27-04:00

Criminy! Didn't revert the correct file. Trying again:

    $ qsub -t 1-6 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=1. nx=400 script=implicitDW7a.py
    Your job-array 3594218.1-6:1 ("timestep.sh") has been submitted

Only a subtle difference here

# 2018-03-22T14:59:51-04:00

At some point, error for implicit becomes more like explicit? Try variety 
of total times:

    $ qsub -t 1-6 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=2. nx=400 script=implicitDW7a.py
    Your job-array 3594219.1-6:1 ("timestep.sh") has been submitted
    $ qsub -t 1-6 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=4. nx=400 script=implicitDW7a.py
    Your job-array 3594220.1-6:1 ("timestep.sh") has been submitted
    $ qsub -t 1-6 -e qsublogs/ -o qsublogs/ -pe nodal 16 -l short=TRUE -cwd timestep.sh totaltime=8. nx=400 script=implicitDW7a.py
    Your job-array 3594221.1-6:1 ("timestep.sh") has been submitted

Is 5 sweeps not enough for `nx=400`?


# 2018-03-22T22:46:52+20:00

Failure to converge seems to be due to my attempt to make PyTrilinos stop 
leaking.

    $ smt diff --long 135d0c021b26 4f07000016ff
    Code differences:
      135d0c021b26: main file 'initializer7a.py' at version 7823afe33f1694676490a6fdb1d70a7d832e4a6c in GitRepository at /data/guyer/CHiMaDPhaseFieldVI (upstream: git@github.com:guyer/CHiMaDPhaseFieldVI.git)
      4f07000016ff: main file 'initializer7a.py' at version 133da982a480d7f3754597c4257e886817c0d5f8 in GitRepository at /data/guyer/CHiMaDPhaseFieldVI (upstream: git@github.com:guyer/CHiMaDPhaseFieldVI.git)
    Dependency differences:
      fipy
        A: version=71d82e1cc7b2c4e7c1c996d038fd8542d7e4c5a1
           
        B: version=e8a2a1776758bb97b966fbb78098785e7748ed02
           
    Parameter differences:
      135d0c021b26:
        {u'ncpus': 16, u'nslots': 16, 'nproc': 16}
      4f07000016ff:
        {u'ncpus': 4, u'nslots': 4, 'nproc': 4}
    Output data differences:
      Generated by 135d0c021b26:
        Treant.7d506e7f-6110-443c-8c97-cfe14a8a7b7f.json(4aa48beae45a45e6e1edf201531a54d3cde17d6e [2018-03-12 20:47:38])
        step0.tar.gz(3ecf34507f2a872127065436ed5d2803d21eb24b [2018-03-12 19:53:43])
        Sumatra.135d0c021b26.json(84ea17d652c4e1c7b71f35f521794d51d3aba9b5 [2018-03-12 20:47:38])
        step800.tar.gz(81a605273d6314023ca4870c9c04470cad1d4d64 [2018-03-12 20:47:36])
      Generated by 4f07000016ff:
        Treant.3196a8d3-3e36-4fa1-9569-cc2b922f0491.json(dfe490de83863858139e119bd1fb7d87d1bcf4ff [2018-03-20 10:35:38])
        Sumatra.4f07000016ff.json(78d9cb38bfbed00446a182289a4594116f7f2c4a [2018-03-20 10:35:38])
        step0.tar.gz(3df3c89f54fce5d83b059755c27f4197ea496c72 [2018-03-20 09:52:27])
        .Treant.3196a8d3-3e36-4fa1-9569-cc2b922f0491.json.proxy(da39a3ee5e6b4b0d3255bfef95601890afd80709 [2018-03-20 09:51:37])
        step800.tar.gz(0260d2256068ec97b961d3ec5c6086df94580315 [2018-03-20 10:35:37])


    $ git diff 71d82e1cc7b2c4e7c1c996d038fd8542d7e4c5a1 e8a2a1776758bb97b966fbb78098785e7748ed02
    diff --git a/fipy/solvers/trilinos/trilinosSolver.py b/fipy/solvers/trilinos/trilinosSolver.py
    index ff725a6..10c866b 100644
    --- a/fipy/solvers/trilinos/trilinosSolver.py
    +++ b/fipy/solvers/trilinos/trilinosSolver.py
    @@ -123,9 +123,9 @@ class TrilinosSolver(Solver):
     
             self.var.value = numerix.reshape(numerix.array(overlappingVector), self.var.shape)
     
    -        self._deleteGlobalMatrixAndVectors()
    -        del self.var
    -        del self.RHSvector
    +#         self._deleteGlobalMatrixAndVectors()
    +#         del self.var
    +#         del self.RHSvector
     
         @property
         def _matrixClass(self):
    (fipy) benson[guyer]: git st

# 2019-12-29T12:30:00-05:00

`datreant.Bundle.categories.groupby()` is O(N**2).

    for m, catval in gen:
        groups[catval] += m

in `datreant.metadata.AggCategories.groupby()` results in each Treant 
being added to an empty Bundle, then each element of that Bundle being 
added to a new Bundle, plus the next Treant, then all of those elements 
being added to a new Bundle, plus the next Treant, ...

Just make a list of Treants with a category mask and instantiate a single 
Bundle.

Worked around in sumatra/recordstore/datreant_store by

    mask = [c == project_name for c in records.categories['smt_project']]
    return records[mask]
        
# 2019-12-30T08:55:50-05:00

Running threadanalyze.py reveals that old YAML files can't be read by Py3k:

    $ python threadanalyze.py 
    /data/guyer/sumatra/sumatra/parameters.py:156: YAMLLoadWarning: calling yaml.load() without Loader=... is deprecated, as the default Loader is unsafe. Please read https://msg.pyyaml.org/load for full details.
      self.values = yaml.load(initialiser)
    /data/guyer/sumatra/sumatra/programs.py:77: Warning: Python could not be found. Please supply the path to the /data/guyer/miniconda2/envs/fipy/bin/python executable.
      warnings.warn(errmsg)
    Traceback (most recent call last):
      File "/data/guyer/sumatra/sumatra/parameters.py", line 156, in __init__
        self.values = yaml.load(initialiser)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/__init__.py", line 114, in load
        return loader.get_single_data()
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 43, in get_single_data
        return self.construct_document(node)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 52, in construct_document
        for dummy in generator:
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 404, in construct_yaml_map
        value = self.construct_mapping(node)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 210, in construct_mapping
        return super().construct_mapping(node, deep=deep)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 135, in construct_mapping
        value = self.construct_object(value_node, deep=deep)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 94, in construct_object
        data = constructor(self, tag_suffix, node)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 635, in construct_python_object_new
        return self.construct_python_object_apply(suffix, node, newobj=True)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 624, in construct_python_object_apply
        instance = self.make_python_instance(suffix, node, args, kwds, newobj)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 566, in make_python_instance
        cls = self.find_python_name(suffix, node.start_mark)
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/yaml/constructor.py", line 538, in find_python_name
        "module %r is not imported" % module_name, mark)
    yaml.constructor.ConstructorError: while constructing a Python object
    module 'future.types.newstr' is not imported
      in "<unicode string>", line 16, column 35:
        !!python/unicode 'sumatra_label': !!python/object/new:future.types ... 
                                          ^

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
      File "threadanalyze.py", line 7, in <module>
        df = load_sumatreant(project_name='benchmark7')
      File "/data/guyer/CHiMaDPhaseFieldVI/sumatreant.py", line 12, in load_sumatreant
        smt_df = pd.read_json(project.record_store.export(project_name),
      File "/data/guyer/sumatra/sumatra/recordstore/base.py", line 72, in export
        records = self.list(project_name)
      File "/data/guyer/sumatra/sumatra/recordstore/datreant_store.py", line 110, in list
        records = self._treants2records(records)
      File "/data/guyer/sumatra/sumatra/recordstore/datreant_store.py", line 83, in _treants2records
        return jsons.map(lambda leaf: serialization.decode_record(leaf.read()))
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/datreant/collections.py", line 488, in map
        results = [function(member, **kwargs) for member in self]
      File "/data/guyer/miniconda3/envs/petsc37/lib/python3.7/site-packages/datreant/collections.py", line 488, in <listcomp>
        results = [function(member, **kwargs) for member in self]
      File "/data/guyer/sumatra/sumatra/recordstore/datreant_store.py", line 83, in <lambda>
        return jsons.map(lambda leaf: serialization.decode_record(leaf.read()))
      File "/data/guyer/sumatra/sumatra/recordstore/serialization.py", line 156, in decode_record
        return build_record(json.loads(content))
      File "/data/guyer/sumatra/sumatra/recordstore/serialization.py", line 87, in build_record
        parameter_set = getattr(parameters, pdata["type"])(pdata["content"])
      File "/data/guyer/sumatra/sumatra/parameters.py", line 160, in __init__
        raise SyntaxError("Misformatted YAML file")
    SyntaxError: Misformatted YAML file

The issue is that things like `newstr` aren't in the `future` module under 
Py3k. At least [one report on the 
internets](https://github.com/DLR-RM/RAFCON/issues/12) says the solution 
is to use native strings. Can we back-translate all this crap?

Run under Py2k for now.
