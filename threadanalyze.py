import pandas as pd
from sumatra.projects import load_project
import datreant.core as dtr

import matplotlib
matplotlib.use('TkAgg') 
from matplotlib import pyplot as plt


def parameters2columns(parameters):
    import yaml

    d_orig = yaml.load(parameters['content'])
    d = dict()
    for k, v in d_orig.iteritems():
        d["--" + k] = v
    return pd.Series(d)

project = load_project('.')
df = pd.read_json(project.record_store.export('benchmark7'),
                  convert_dates=["timestamp"])

df = df[df['tags'].map(lambda x: '_finished_' in x)][['dependencies', 'diff', 'label', 'timestamp', 'duration', 'tags', 'version', 'parameters']]

df2 = df.merge(df.parameters.apply(parameters2columns), left_index=True, right_index=True)

df2 = df2[df2['tags'].map(lambda x: 'threads' in x)]

data = dtr.Treant('Data/')

data = data[list(df2['label'])]

df3 = pd.DataFrame(index=data.names, data={'solvetime': data.bundle.categories['solvetime']})

df4 = df2.merge(df3, left_on='label', right_index=True)

# print df4[['label', 'timestamp', '--ncpus', '--nthreads', '--nslots', '--nx', 'duration', 'solvetime']] 

plt.plot(df4['--nthreads'], df4['duration'], linestyle="", marker="x")
plt.plot(df4['--nthreads'], df4['solvetime'], linestyle="", marker="+")

plt.show()
