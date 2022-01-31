from sklearn.feature_extraction.text import TfidfVectorizer
import glob
import os
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
import json


def document_ranking(documents_path, keywords, urls, alpha=0.8, language='es'):
    """ Function to implement a ranking of documents. Implements a TF-IDF where rows are the text of the documents
    and columns are all the ngrams that compose the corpus. The ngrams that are considered keywords are weighted with
    `alpha`, the rest of the corpus with (1-`alpha`). In this way, the documents ara ranked from the extracted keywords,
    but taking into account the full corpus.

    Args:
        * documents_path (str): Path where documents are saved
        * keywords (list): List of keywords that will be (over/under)-weighted to get the ranking
        * alpha (float): Weight for the keywords. The rest of the ngrams will take the complementary weight, i.e, (1 - `alpha`)
        * language (str): Selected language. (English by default)

    Returns:
        None
    """
    data = []

    documents = glob.glob("{}/*.txt".format(documents_path))

    for doc in documents:
        with open(doc, "rb") as file:
            data += [file.read()]

    if language == 'es':
        vec = TfidfVectorizer(ngram_range=(1, 3), stop_words=set(stopwords.words('spanish')))
    else:
        vec = TfidfVectorizer(ngram_range=(1, 3), stop_words="english")

    model = vec.fit_transform(data)
    vocabulary = vec.vocabulary_
    keywords_idx = get_index(keywords, vocabulary)
    doc_word_matrix = model.todense()

    weight_matrix = np.ones((doc_word_matrix.shape[0], doc_word_matrix.shape[1]))*(1-alpha)
    weight_matrix[:, keywords_idx] = alpha

    weighted_doc_word_matrix = np.multiply(doc_word_matrix, weight_matrix)

    doc_sum = np.squeeze(np.asarray(weighted_doc_word_matrix.sum(axis=1)))

    sorted_idx = np.argsort(doc_sum)

    sorted_docs = {}
    for idx, i in enumerate(sorted_idx):
        head, tail = os.path.split(documents[i])
        sorted_docs[idx] = tail

    df = pd.DataFrame.from_dict(sorted_docs, orient="index", columns=['document_name'])
    url_dict = json.loads(urls)
    df['url'] = df['document_name'].map(url_dict)
    df.to_csv(os.path.join(documents_path, 'document_ranking.csv'))


def get_index(keywords, vocabulary):
    """ Auxiliary function to obtain the list of indices in TF-IDF matrix for a given list of keywords

    Args:
        keywords (list): List of keywords
        vocabulary (list): List of all the ngrams that compose the corpus

    Returns:
        list: List of indices of the keywords in the TF-IDF columns

    """
    keywords_idx = []
    for k in keywords:
        if k in vocabulary:
            keywords_idx += [vocabulary[k]]
    return keywords_idx
