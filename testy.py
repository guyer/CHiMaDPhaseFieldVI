import os
import sys
import yaml

yamlfile = sys.argv[1]

with open(yamlfile, 'r') as f:
    params = yaml.load(f)

from sumatra.projects import load_project
project = load_project(os.getcwd())
raise Exception(str(project))
record = project.get_record(params["sumatra_label"])
raise Exception(str(record))
output = record.datastore.root
raise Exception(output)

with open(os.path.join(output, "file.txt"), 'w') as f:
    f.write("eeny")

