from sumatra.commands import run

run(['--tag', 'troubleshoot', '-n', '1', '--main', 'threadtest.py', 'params.yaml', 'nthreads=1', 'nncpus=1', 'nslots=1'])
