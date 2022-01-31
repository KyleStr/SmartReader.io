import time

import numpy as np
import pickle
from geopy.geocoders import Nominatim

from smart_reader_app.model import create_model
from smart_reader_app.utils import dataset_reader
from smart_reader_app.utils.sumytest import *

geolocator = Nominatim()

a, b = None, None


def get_entities(nlp, text):
	entities = defaultdict(lambda: [])
	for t in text.split(". "):
		doc = nlp(t)
		for ent in doc.ents:
			entities[ent.label_].append({"type": ent.label_, "text": ent.text})
	return entities


def score_doc(model, doc, nlp, language):
	'''
	generating a list of paragraphs per document. len(texts) 
	returns the number of paragraphs in a document
	'''
	texts = [par.text for par in doc.paragraphs]

	if language == 'es':
		entity_types_non_loc = ['PER', "ORG", "MISC"]
		entity_types_loc = ["LOC"]

	else:
		entity_types_non_loc = ['PERSON', "ORG", "PRODUCT", "EVENT", "WORK_OF_ART", "LANGUAGE", "NORP"]
		entity_types_loc = ["LOC", "GPE"]

	for topic in model:
		'''
		storing the TfidfVectorizer function of 
		the model with its corresponding parameters
		'''
		vec = topic['vectorizer']
		'''
		transforming the documents(text) to a
		document-term matrix. It returns X which
		is a sparse matrix, [n_samples, n_features]
		'''
		X = vec.transform(texts)

		feature_indices = topic["feature_indices"]
		'''
		X.shape[0] is the number of rows, e.g.: 126 rows or 
		paragraphs. From now, "topic" refers to the information 
		in the model and "X" refers to text file
		'''
		for i in range(X.shape[0]):
			# scores[i, 0]
			score = 0
			hits = []
			# feat returns the keyword itself
			for feat in feature_indices:
				# j returns the index of the keyword
				j = feature_indices[feat]
				# Calculating the score of each feature
				if feat in topic["keywords"] and X[i, j] > 0:
					sc = (X[i, j] * topic["keywords"][feat])
					hits.append({"keyword": feat, "count": sc})
					score = score + sc

			doc.paragraphs[i].classification[topic["topic"]] = score
			doc.paragraphs[i].topic_keywords[topic["topic"]] = hits

			entities = get_entities(nlp, u'%s' % texts[i])

			doc.paragraphs[i].locations = []
			for et in entity_types_loc:
				doc.paragraphs[i].locations.extend(entities[et])

			doc.paragraphs[i].entities = []
			for et in entity_types_non_loc:
				doc.paragraphs[i].entities.extend(entities[et])

	for i in range(len(doc.paragraphs)):
		sm = 1.0*sum( doc.paragraphs[i].classification.values() )
		if sm == 0 or True:
			sm = 1
		for topic_name in doc.paragraphs[i].classification:
			doc.paragraphs[i].classification[topic_name] /= sm


para_g = None


def consolidate_data(dataset, model):
	output_prelim = defaultdict(lambda: [])
	global para_g
	# dataset is of type list
	for doc in dataset:
		for para in doc.paragraphs:
			para_g = para
			best_topic = max(para.classification, key=para.classification.get)
			output_prelim[best_topic].append({"para": para, "score": para.classification[best_topic]})
	output = []
	for topic in output_prelim:
		d = {"topic": topic, "paragraphs": sorted(output_prelim[topic], key=lambda x: -x["score"])}
		output.append(d)
	return output


def create_summary(models_path, dataset_location, model_name, language='en'):

	if language == 'es':
		nlp = spacy.load("es_core_news_sm")

	else:
		nlp = spacy.load('en_core_web_sm')

	model_name = os.path.join(models_path, model_name)
	dataset = dataset_reader.read_dataset_text(dataset_location)
	model = create_model.load_model(model_name)

	for doc in dataset:
		score_doc(model, doc, nlp, language)
	# storing paragraphs and scores in descending order
	output = consolidate_data(dataset, model)

	# serializing output
	pickle.dump(output, open("prelim_output_informal_economy_new.bin", "wb"))

	get_lat_lng = False
	location_history = {}
	js = []
	for topic in output:
		topic_name = topic["topic"]
		d = {"topic":topic_name}

		# creating dictionary
		all_keywords = defaultdict(lambda:0)
		# creating dictionary
		all_locations = defaultdict(lambda:0)
		# creating dictionary
		all_entities = defaultdict(lambda:0)
		# creating dictionary
		all_entities_type = defaultdict(lambda:0)
		summary_points = []
		paragraphs = topic["paragraphs"]

		# iterating through the 50 most relevant paragraphs
		for p in paragraphs[0:50]:
			try:
				# storing the paragraph
				full_text = p["para"].text

				# storing the tokenized paragraph
				sentences = sent_tokenize(full_text)

				# storing the most revelant sentence in paragraph
				if language == 'es':
					summary = get_summary(full_text, 1, len(sentences), nlp, 'spanish')[0]
				else:
					summary = get_summary(full_text, 1, len(sentences), nlp, 'english')[0]
				original_sentence = summary
				summary_index = sentences.index(summary)

				if summary_index == 0:
					if len(sentences) > 1:
						context = sentences[summary_index] + sentences[summary_index+1]
					else:
						context = sentences[summary_index]
				elif summary_index == (len(sentences) - 1):
					context = sentences[summary_index - 1] + sentences[summary_index]
				else:
					context = sentences[summary_index-1] + sentences[summary_index] + sentences[summary_index+1]

				summary_points.append({"summary": summary, "context": context, "original_sentence": original_sentence, "text": full_text, "doc_id": p["para"].document.name.split('/')[-1], "para_id": p["para"].para_id, "score": p["score"]})
				for kwo in p["para"].topic_keywords[topic_name]:
					kw = kwo["keyword"]
					all_keywords[kw] += kwo["count"]
				for eto in p["para"].locations:
					all_locations[ eto["text"] ] += 1
				for eto in p["para"].entities:
					all_entities[ eto["text"] ] += 1
					all_entities_type[eto["text"]] = eto["type"]
			except Exception as e:
				print("Error on create_summary (process.py). An exception occurred: ", e)
				pass
		d['summary_points'] = summary_points
		d["keywords"] = [{"keyword": k, "count": all_keywords[k]} for k in all_keywords]
		sm = np.sum([kw["count"] for kw in d["keywords"]])
		for kw in d["keywords"]:
			kw["count"] = int(1000*kw["count"]/sm)
		d["locations"] = [ {"keyword": k, "count": all_locations[k], "type": "LOCATION"} for k in all_locations if len(k) > 1]

		if get_lat_lng:
			for l in d["locations"]:
				count = 0
				while count <= 3:
					count = count + 1
					try:
						if l['keyword'] in location_history:
							latlng = location_history[l['keyword']]
						else:
							latlng = geolocator.geocode(l['keyword'])
							location_history[l['keyword']] = latlng

						break
						if latlng:
							l["lat"] = latlng.latitude
							l["lng"] = latlng.longitude
					except:
						pass
		d["entities"] = [{"keyword": k, "count": all_entities[k], "type": all_entities_type[k]} for k in all_entities if len(k) > 1]
		d["folder"] = dataset_location
		d["folder_name"] = dataset_location.split("/")[-1]
		js.append(d)

	os.remove("prelim_output_informal_economy_new.bin")

	return js
