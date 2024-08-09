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

df = df[df['tags'].map(lambda x: 'optimize' in x)]

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

df[["duration", "solvetime", "error", "solver", "preconditioner", "tolerance", "iterations", "sweeps"]].to_csv("optimize.csv")

plt.plot(df["error"], df["duration"], linestyle="", marker=".", color='blue')

plt.xlabel(r"$\|\|\mathrm{error}\|\|_2$")
plt.ylabel(r"$\mathrm{duration} / \mathrm{s}$")

plt.savefig("optimize.png")


plt.show()
