import os
import shutil
import json

import networkx as nx
import numpy as np
import pandas as pd
from gensim.utils import flatten
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from random import sample


fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir)))))
DATA_PATH = os.path.join(parentDir, "data", "glove")


def txt2df(logger, path):
    """
    Function to aggregate source txt documents into a DataFrame.

    Args:
        logger (Logger): Logger file
        path (str): path to the txt documents.

    Returns:
        pandas.DataFrame: with a row for each txt document

    """
    dir_path = path
    df = pd.DataFrame(columns=['full_text'])
    k = 0
    try:
        for file in os.listdir(dir_path):
            if file.endswith(".txt"):
                k += 1
                with open(os.path.join(dir_path, file)) as txt_file:
                    data = txt_file.read()
                df.loc[k, 'full_text'] = data
    except Exception as e:
        logger.error(e)
    return df


def extract_sentences(df, max_sent):
    """
    Function that extracts the sentences from the texts.

    Args:
        df (pandas.DataFrame): DataFrame with a document in each row.
        max_sent (int): Maximum number of sentences that will be used to make the summary

    Returns:
        list: List with the sentences of all documents.

    """
    sentences = []
    for s in df['full_text']:
        sentences.append(sent_tokenize(s))
    sentences = flatten(sentences)
    if len(sentences) > max_sent:
        sentences = sample(sentences, max_sent)
    return list(set(sentences))


def remove_stopwords(sen, stop_words):
    """
    Function that removes the stopwords from the sentences.

    Args:
        sen (list): List with a splitted sentence.
        stop_words (list): List of stopwords.

    Returns:
        list: sentence without stopwords.

    """
    sen_new = " ".join([i for i in sen if i not in stop_words])
    return sen_new


def process(sentences, language='en'):
    """
    Function that processes the sentences. Removes punctuation, numbers and symbols,
    converts to lowercase and removes stopwords.

    Args:
        sentences (list): List of all sentences.
        language (str): Selected language. (English by default)

    Returns:
        list: list of cleaned sentences.

    """
    clean_sentences = pd.Series(sentences).str.replace("[^a-zA-Z]", " ")
    clean_sentences = [s.lower() for s in clean_sentences]

    if language == 'es':
        stop_words = stopwords.words("spanish")
    else:
        stop_words = stopwords.words("english")

    clean_sentences = [remove_stopwords(r.split(), stop_words) for r in clean_sentences]
    return clean_sentences


def extract_embeddings(logger, language='en'):
    """
    Function that gets the word embeddings from a pretrained GloVe.

    Args:
        logger (Logger): Logger file
        language (str): Selected language. (English by default)

    Returns:
        dict: Dictionary that has words as keys and embedding vectors as values.

    """
    model_name = {'en': 'glove.6B.100d.txt',
                  'es': 'glove-sbwc.i25.txt'}

    word_embeddings = {}
    if model_name[language] not in os.listdir(DATA_PATH):
        logger.info("You do not have GloVe downloaded, please follow the instructions")

    f = open(os.path.join(DATA_PATH, model_name[language]), encoding='utf-8')
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        word_embeddings[word] = coefs
    f.close()
    return word_embeddings


def make_matrix(clean_sentences, word_embeddings, language='en'):
    """
    Function that efficiently computes the similarity matrix between clean sentences.

    Args:
        clean_sentences (list): List of clean sentences.
        word_embeddings (dict): Dictionary with the word embeddings.
        language (str): Selected language. (English by default)

    Returns:
        matrix: Cosine similarity matrix for each pair of sentences.

    """
    sentence_vectors = []
    ss = 0
    len_embeddings = {'en': 100, 'es': 300}

    for i in clean_sentences:
        if len(i) != 0:
            # if the word w does not have an embedding, return array of 0s
            v = sum([word_embeddings.get(w, np.zeros((len_embeddings[language],))) for w in i.split()]) / (len(i.split()) + 0.001)
            if (v == np.zeros(len_embeddings[language], )).all():
                ss += 1
        else:
            v = np.zeros((len_embeddings[language],))
        sentence_vectors.append(v)
    sim_mat = cosine_similarity(sentence_vectors)
    return sim_mat


def sort_files(logger, data_path, id_path, num_topics):
    """
    Function that sorts the files into the topics computed by the LDA.

    Args:
        logger (Logger): Logger file
        data_path (str): Path to the files that must be summarized.
        id_path (str): Path to the csv that has de document ids and their respective topics.
        num_topics (int): Number of topics that the LDA made.

    Returns:
        None: The function makes a topic directory structure.

    """
    id_docs = pd.read_csv(id_path)
    for k in range(num_topics):
        topic_docs = list(id_docs[id_docs['top_id'] == k]['file_id'])
        try:
            os.mkdir(os.path.join(data_path, 'topic_{}'.format(k)))
        except FileExistsError:
            logger.info('The directory already exists.')
        for doc in topic_docs:
            if doc in os.listdir(data_path):
                shutil.copy(os.path.join(data_path, doc), os.path.join(data_path, 'topic_{}'.format(k), doc))


def rank_sentences(df, glove_embeddings, max_sent, language='en'):
    """
    Function that performs the textrank process.

    Args:

        df (pandas.DataFrame): DataFrame that has the a text per row.
        glove_embeddings (dict): Dictionary with words as keys and embedding vectors as values.
        max_sent (int): Maximum number of sentences that will be used to make the summary
        language (str): Selected language. (English by default)

    Returns:
        list: list of ranked sentences for the texts in the DataFrame.

    """
    sentences = extract_sentences(df, max_sent)
    clean_sentences = process(sentences, language)
    sim_mat = make_matrix(clean_sentences, glove_embeddings, language)

    nx_graph = nx.from_numpy_matrix(sim_mat)
    scores = nx.pagerank_numpy(nx_graph)

    ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    return ranked_sentences


def make_textrank(logger, data_path, num_topics, num_sentences, lda_topic_name, max_sent, language='en'):
    """
    Main function that calls the rest to perform the textrank algorithm. The output is a
    txt file that has a summary of all the documents in the data_path.

    Args:
        logger (Logger): Logger file
        data_path (str): Path to the files that must be summarized.
        num_topics (int): Number of topics that the LDA made.
        num_sentences (int): Number of sentences to show for the summary.
        lda_topic_name (str): Name of the csv where the topic distribution is defined.
        max_sent (int): Maximum number of sentences that will be used to make the summary
        language (str): Selected language. (English by default)

    Returns:
        None: The function saves a txt file with the summary of the documents.

    """
    id_path = os.path.join(data_path, lda_topic_name)
    sort_files(logger, data_path, id_path, num_topics)
    glove_embeddings = extract_embeddings(logger, language)
    tr_topic_dict = {}

    for k in range(num_topics):
        tr_topic_dict['topic_{}'.format(k)] = []
        df = txt2df(logger, os.path.join(data_path, 'topic_{}'.format(k)))

        if len(df) > 0:
            textrank_list = []
            ranked_sentences = rank_sentences(df, glove_embeddings, max_sent, language)
            printrange = min(num_sentences, len(ranked_sentences))
            for i in range(printrange):
                textrank_list.append(ranked_sentences[i][1])

            tr_topic_dict['topic_{}'.format(k)] = textrank_list

    with open(os.path.join(data_path, 'textrank_summaries.json'), 'w') as fp:
        json.dump(tr_topic_dict, fp)
