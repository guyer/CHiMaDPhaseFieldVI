import matplotlib
matplotlib.use('TkAgg') 
from matplotlib import pyplot as plt

from sumatreant import load_sumatreant

df = load_sumatreant(project_name='benchmark7')

df = df[df['tags'].map(lambda x: '_finished_' in x and 'threads' in x)]

# print df[['label', 'timestamp', '--ncpus', '--nthreads', '--nslots', '--nx', 'duration', 'solvetime']] 

slots16 = df[df['nslots'] == 16]
slots32 = df[df['nslots'] == 32]
cpus4 = df[df['ncpus'] == 4]

duration, = plt.plot(slots16['nthreads'], slots16['duration'], linestyle="", marker="x", color='blue', label="16 slots")
solvetime, = plt.plot(slots16['nthreads'], slots16['solvetime'], linestyle="", marker="+", color='blue', label="_")
plt.plot(slots32['nthreads'], slots32['duration'], linestyle="", marker="x", color='red', label="32 slots")
plt.plot(slots32['nthreads'], slots32['solvetime'], linestyle="", marker="+", color='red', label="_")
plt.plot(cpus4['nthreads'], cpus4['duration'], linestyle="", marker="x", color='green', label="4 cpus")
plt.plot(cpus4['nthreads'], cpus4['solvetime'], linestyle="", marker="+", color='green', label="_")

first_legend = plt.legend(loc="lower center")

ax = plt.gca().add_artist(first_legend)

plt.legend((duration, solvetime), ('total time', 'solve time'), loc="upper right")

plt.xlabel("# threads")
plt.ylabel("time / s")

plt.show()
