from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import logging
from nltk.corpus import stopwords


def get_topic_keywords(features, X):
	features_with_weights = sorted([ {"keyword":features[i], "count": X[0,i], "index":i} for i in range(len(features)) ], key=lambda x:-x["count"] )[:50]
	features = {}
	feature_indices = {}
	for fww in features_with_weights:
		features[fww["keyword"]] = fww["count"]
		feature_indices[fww["keyword"]] = fww["index"]
	return features, feature_indices


def create_and_save_model(subtopics, output_file, language='en'):
	data = []
	output = ()
	all_texts = []
	if language == 'es':
		vec = TfidfVectorizer(ngram_range=(1, 3), stop_words=set(stopwords.words('spanish')))
	else:
		vec = TfidfVectorizer(ngram_range=(1,3), stop_words="english")

	subtopic_names = list(subtopics.keys())
	no_data_subtopic_names = []
	for topic in subtopic_names:
		text = subtopics[topic]
		'''Starts new code'''
		logging.basicConfig(filename='log_SM.txt', filemode='w', level=logging.DEBUG)
		logging.debug("Text:")
		logging.debug(text)

		logging.debug("Topic:")
		logging.debug(topic)
		'''Ends new code'''

		if len(text.strip()) >0 :
			all_texts.append(text)
		else:
			no_data_subtopic_names.append(topic)
	X = vec.fit_transform(all_texts)
	global gX
	gX = X
	features = vec.get_feature_names()
	data_subtopic_names = list(set(subtopic_names) - set(no_data_subtopic_names))
	for i in range(len(data_subtopic_names)):
		Xi = X[i, :]
		features_with_weights, feature_indices = get_topic_keywords(features, Xi)
		data.append({"topic": data_subtopic_names[i], "keywords": features_with_weights, "vectorizer": vec, "feature_indices": feature_indices})

	pickle.dump(data, open(output_file, "wb"))
	global gvec
	gvec = vec


def load_model(file_path):
	return pickle.load(open(file_path, "rb"))

gvec = None
gX = None
