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
df = df[(df["totaltime"] == 8.0) & (df["nx"] == 800)]

# print df[['label', 'timestamp', '--ncpus', '--nthreads', '--nslots', '--nx', 'duration', 'solvetime']] 

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

plt.loglog(df["dt"], df["error"], linestyle="", marker="x", color='blue')
plt.loglog(df["dt"][:-1], df["error"][:-1] - df["error"][-1], linestyle="", marker="x", color='green')

dftrunk = df[df["dt"] >= 1e-2]

plt.loglog(dftrunk["dt"], dftrunk["error"], linestyle="", marker="o", color='red', markerfacecolor="none")

slope, intercept, r_value, p_value, std_err = stats.linregress(fp.tools.numerix.log10(dftrunk["dt"]),
                                                               fp.tools.numerix.log10(dftrunk["error"]))

print "slope:", slope
print "intercept:", intercept
print "r_value:", r_value
print "p_value:", p_value
print "std_err:", std_err

x = fp.tools.numerix.array([min(dftrunk["dt"]), max(dftrunk["dt"])])
y = x**slope * 10**intercept

plt.loglog(x, y, color='blue')

plt.text(2e-3, 1e-3, """scaling = {:.3f}
$R^2 = {:.4f}$""".format(slope, r_value**2))

slope, intercept, r_value, p_value, std_err = stats.linregress(fp.tools.numerix.log10(dftrunk["dt"][:-1]),
                                                               fp.tools.numerix.log10(dftrunk["error"][:-1] - df["error"][-1]))

print "slope:", slope
print "intercept:", intercept
print "r_value:", r_value
print "p_value:", p_value
print "std_err:", std_err

x = fp.tools.numerix.array([min(dftrunk["dt"]), max(dftrunk["dt"])])
y = x**slope * 10**intercept

plt.loglog(x, y, color='green')

plt.xlabel("time step")
plt.ylabel("$\|\|\mathrm{error}\|\|_2$")

plt.savefig("timestep.png")


plt.show()
