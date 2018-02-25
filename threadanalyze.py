import matplotlib
matplotlib.use('TkAgg') 
from matplotlib import pyplot as plt

from sumatreant import load_sumatreant

df = load_sumatreant(project_name='benchmark7')

df = df[df['tags'].map(lambda x: '_finished_' in x and 'threads' in x)]

# print df[['label', 'timestamp', '--ncpus', '--nthreads', '--nslots', '--nx', 'duration', 'solvetime']] 

slots16 = df[df['nslots'] == 16]
slots32 = df[df['nslots'] == 32]

plt.plot(slots16['nthreads'], slots16['duration'], linestyle="", marker="x", color='blue')
plt.plot(slots16['nthreads'], slots16['solvetime'], linestyle="", marker="+", color='blue')
plt.plot(slots32['nthreads'], slots32['duration'], linestyle="", marker="x", color='red')
plt.plot(slots32['nthreads'], slots32['solvetime'], linestyle="", marker="+", color='red')

plt.show()
