import matplotlib
matplotlib.use('TkAgg') 
from matplotlib import pyplot as plt
import datreant.core as dtr
import pandas as pd
from scipy import stats

import fipy as fp

from sumatreant import load_sumatreant

df = load_sumatreant(project_name='benchmark7')

df = df[df['tags'].map(lambda x: '_finished_' in x and 'meshsize' in x)]

# print df[['label', 'timestamp', '--ncpus', '--nthreads', '--nslots', '--nx', 'duration', 'solvetime']] 

data = dtr.Treant("Data/")
data = data[list(df.index)]

errors = []
for d in data:
    eta, error = fp.tools.dump.read(filename=d["step80000.tar.gz"].make().abspath)
    errors.append(fp.tools.numerix.sqrt((error**2).cellVolumeAverage * error.mesh.cellVolumes.sum()).value)

error_df = pd.DataFrame(index=df.index, data={"error": errors})

df = df.merge(error_df, left_index=True, right_index=True)
df["dx"] = df["Lx"] / df["nx"]

plt.loglog(df["dx"], df["error"], linestyle="", marker="x", color='blue')

slope, intercept, r_value, p_value, std_err = stats.linregress(fp.tools.numerix.log10(df["dx"]),
                                                               fp.tools.numerix.log10(df["error"]))

print "slope:", slope
print "intercept:", intercept
print "r_value:", r_value
print "p_value:", p_value
print "std_err:", std_err

x = fp.tools.numerix.array([min(df["dx"]), max(df["dx"])])
y = x**slope * 10**intercept
                            
plt.loglog(x, y)

plt.xlabel("mesh size")
plt.ylabel("$\|\|\mathrm{error}\|\|_2$")

plt.text(2e-3, 4e-3, """scaling = {:.3f}
$R^2 = {:.3f}$""".format(slope, r_value**2))

plt.savefig("meshsize.png")

plt.show()
