import glob
import os

import matplotlib
matplotlib.use('TkAgg') 
from matplotlib import pyplot as plt
import datreant.core as dtr
import pandas as pd
from scipy import stats

import fipy as fp

from sumatreant import load_sumatreant

df = load_sumatreant(project_name='benchmark7')

df = df[df['tags'].map(lambda x: '_finished_' in x and 'timestep' in x)]
# df = df[(df["totaltime"] == 1.0) & (df["nx"] == 400)]
df = df[(df["nx"] == 400)]

# some (unsuccessful) runs recorded nonsensical timesteps as string type
df["dt"] = df["dt"].astype(float)

data = dtr.Treant("Data/")
data = data[list(df.index)]

errors = []
for d in data:
    try:
        fn = glob.glob(os.path.join(d.make().abspath, "step*.tar.gz"))[-1]
        eta, error = fp.tools.dump.read(filename=fn)
        errors.append(fp.tools.numerix.sqrt((error**2).cellVolumeAverage * error.mesh.cellVolumes.sum()).value)
    except:
        try:
            eta, error = fp.tools.dump.read(filename=d["eta.tar.gz"].make().abspath)
            errors.append(fp.tools.numerix.sqrt((error**2).cellVolumeAverage * error.mesh.cellVolumes.sum()).value)
        except:
            errors.append(fp.tools.numerix.nan)

error_df = pd.DataFrame(index=df.index, data={"error": errors})

df = df.merge(error_df, left_index=True, right_index=True)

plt.loglog(df["dt"], df["error"], linestyle="", marker="x", color='red')
plt.loglog(df["dt"][:-1], df["error"][:-1] - df["error"][-1], linestyle="", marker="+", color='red')

plt.xlabel("time step")
plt.ylabel("$\|\|\mathrm{error}\|\|_2$")

plt.savefig("timestepforoptimize.png")


plt.show()
