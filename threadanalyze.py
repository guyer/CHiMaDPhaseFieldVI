import pandas as pd
from sumatra.projects import load_project
import datreant.core as dtr

import matplotlib
matplotlib.use('TkAgg') 
from matplotlib import pyplot as plt


def parameters2columns(parameters):
    import yaml

    d_orig = yaml.load(parameters['content'])
    return pd.Series(d_orig)

project = load_project('.')
df = pd.read_json(project.record_store.export('benchmark7'),
                  convert_dates=["timestamp"])
df = df.set_index(['label'])

df2 = df.merge(df.parameters.apply(parameters2columns), left_index=True, right_index=True)

data = dtr.Treant('Data/')

data = data[list(df2.index)]

df3 = pd.DataFrame(index=data.names, data=data.bundle.categories.any)

df4 = df2.merge(df3, left_index=True, right_index=True)

df4 = df4[df4['tags'].map(lambda x: '_finished_' in x and 'threads' in x)]

# print df4[['label', 'timestamp', '--ncpus', '--nthreads', '--nslots', '--nx', 'duration', 'solvetime']] 

plt.plot(df4['nthreads'], df4['duration'], linestyle="", marker="x")
plt.plot(df4['nthreads'], df4['solvetime'], linestyle="", marker="+")

plt.show()
