import os
from smart_reader_app.utils.document import *

# dataset_location = "datasets/informal_economy/text"

def read_dataset_text(dataset_location):
	dataset = []
	locs = []
	for path, subdirs, files in os.walk(dataset_location):
		for name in files:
			locs.append(os.path.join(path, name))
	for f in locs:
		doc = Document()
		doc.read_text(f)
		dataset.append(doc)
	return dataset
