import pandas as pd
from sumatra.projects import load_project
import datreant.core as dtr
import yaml

def load_sumatreant(project_name, path=None):
    """load data from Sumatra record and Datreant data store

    returns Pandas DataFrame
    """
    project = load_project(path)
    smt_df = pd.read_json(project.record_store.export(project_name),
                          convert_dates=['timestamp'])
    smt_df = smt_df.set_index(['label'])

    prm_df = smt_df.parameters
    prm_df = prm_df.apply(lambda x: pd.Series(yaml.load(x['content'])))
    smt_df.drop(columns=['parameters'])

    smt_df = smt_df.merge(prm_df, left_index=True, right_index=True)

    data = dtr.Treant(project.data_store.root)
    data = data[list(smt_df.index)]

    dtr_df = pd.DataFrame(index=data.names, data=data.bundle.categories.any)

    return smt_df.merge(dtr_df, left_index=True, right_index=True)
