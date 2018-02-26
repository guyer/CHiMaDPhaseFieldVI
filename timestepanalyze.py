import matplotlib
matplotlib.use('TkAgg') 
from matplotlib import pyplot as plt
import datreant.core as dtr
import pandas as pd

import fipy as fp

from sumatreant import load_sumatreant

df = load_sumatreant(project_name='benchmark7')

df = df[df['tags'].map(lambda x: '_finished_' in x and 'timestep' in x)]

# print df[['label', 'timestamp', '--ncpus', '--nthreads', '--nslots', '--nx', 'duration', 'solvetime']] 

data = dtr.Treant("Data/")
data = data[list(df.index)]

errors = []
for d in data:
    eta, error = fp.tools.dump.read(filename=d["eta.tar.gz"].make().abspath)
    errors.append(fp.tools.numerix.sqrt((error**2).cellVolumeAverage * error.mesh.cellVolumes.sum()).value)

error_df = pd.DataFrame(index=df.index, data={"error": errors})

df = df.merge(error_df, left_index=True, right_index=True)

plt.loglog(df["dt"], df["error"], linestyle="", marker="x", color='blue')

plt.show()
