import os
import sys
import yaml

yamlfile = sys.argv[1]

with open(yamlfile, 'r') as f:
    params = yaml.load(f)

from sumatra.projects import load_project
project = load_project(os.getcwd())
record = project.get_record(params["sumatra_label"])
output = record.datastore.root

with open(os.path.join(output, "file.txt"), 'w') as f:
    f.write("eeny")

