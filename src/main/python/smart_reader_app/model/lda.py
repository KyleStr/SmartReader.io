import os
import re
import warnings
from glob import glob

import funcy as fp
import nltk
import numpy as np
import pandas as pd
import pyLDAvis
import pyLDAvis.gensim as gensimvis
from gensim import models
from gensim.corpora import Dictionary

warnings.filterwarnings("ignore", category=DeprecationWarning)

email_re = re.compile(r"[a-z0-9\.\+_-]+@[a-z0-9\._-]+\.[a-z]*")
url_re = re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")
filter_re = re.compile(r"[^a-záéíóúüñ '#]")
filter_sep = re.compile(r"- ")
token_mappings = [(url_re, ""), (email_re, "#email"), (filter_re, ' '), (filter_sep, "")]


def tokenize_line(line):
    """
    Function that substitutes some common regular expressions and splits the text into tokens.

    Args:
        line (str): String of a document.

    Returns:
        list: Splitted elements of the string.

    """
    res = line.lower()
    for regexp, replacement in token_mappings:
        res = regexp.sub(replacement, res)
    return res.split()


def tokenize(lines, token_size_filter=2):
    """
    Function that tokenizes a document.

    Args:
        lines (list): List of strings. Each element of the list is one line of a document.
        token_size_filter (int): Minimum size to consider a token valid.

    Returns:
        list: tokens of a document.

    """
    tokens = fp.mapcat(tokenize_line, lines)
    return [t for t in tokens if len(t) > token_size_filter]


def load_doc(filename):
    """
    Function to load a document, read it and call the functions necessary to process it.

    Args:
        filename (str): path to a .txt document.

    Returns:
        dict: Dictionary with key the content of the document and value its tokens.

    """
    with open(filename, errors='ignore') as f:
        doc = f.readlines()
    head, tail = os.path.split(filename)
    return {'doc': doc, 'tokens': tokenize(doc), 'file_id': tail}


def prep_corpus(logger, docs, below=1, above=0.5, language='en'):
    """
    Function to build the dictionary and corpus. Filters the stopwords, makes the dictionary and corpus.

    Args:
        logger (Logger): Logger file
        docs (pandas.Series): Series with the tokens for each document.
        below (int): Minimum number of distinct documents where a token appears for it to be considered.
        above (float): Maximum fraction of distinct documents where a token appears for it to be considered.
        language (str): Language of the model. Can be either 'english' or 'spanish'
    Returns:
        tuple: dictionary (token, token_id), corpus list(token_id, token_count).

    """
    logger.info('Building dictionary...')
    dictionary = Dictionary(docs)
    if language == 'es':
        stopwords = set(nltk.corpus.stopwords.words("spanish"))
    else:
        stopwords = set(nltk.corpus.stopwords.words("english"))
    stopword_ids = map(dictionary.token2id.get, stopwords)
    dictionary.filter_tokens(stopword_ids)
    dictionary.compactify()
    dictionary.filter_extremes(no_below=below, no_above=above, keep_n=None)
    dictionary.compactify()

    logger.info('Building corpus...')
    corpus = [dictionary.doc2bow(doc) for doc in docs]

    return dictionary, corpus


def make_lda(logger, data_path, lda_id, lda_topics, html_path, num_topics, show_topics, language='en'):
    """
    Main function that calls the rest and performs the LDA, saving at the end the html with the LDA visualization.

    Args:
        logger (Logger): Logger file
        data_path (str): Path to the folder that contains the text files.
        lda_id (str): Name of the LDA visualization file.
        lda_topics (str): Name of the LDA topic distribution file.
        html_path (str): Path to the folder that contains the html files.
        num_topics (int): Number of topics that will be computed by the LDA.
        show_topics (int): How many topics considered in the top.

    Returns:
        None: The function saves a file with the resulting html to display it in the front end.

    """
    docs = pd.DataFrame(list(map(load_doc, glob(data_path + '/*.txt'))))
    docs['topic_id'] = 'TBC'
    docs['top_id'] = 'TBC'
    try:
        below = int(np.ceil((len(docs)*5)/88))
        dictionary, corpus = prep_corpus(logger, docs['tokens'], below, language=language)
    except Exception as e:
        logger.error(e)
        logger.info('Using default argument no_below = 1')
        dictionary, corpus = prep_corpus(logger, docs['tokens'])

    lda = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, passes=10, random_state=1)

    for k, row_list in enumerate(lda[corpus]):
        try:
            topic_id = sorted(row_list, key=lambda item: item[1], reverse=True)
            top_id = max(row_list, key=lambda item: item[1])[0]
            flat_list = topic_id + [('Na', 'Na')]*(show_topics - len(topic_id))
            docs.loc[k, 'topic_id'] = str(flat_list[0:show_topics])
            docs.loc[k, 'top_id'] = top_id
        except Exception as e:
            logger.error(e)

    docs = docs[docs['top_id']!='TBC']
    docs[['file_id', 'topic_id', 'top_id']].to_csv(os.path.join(data_path, lda_topics), index=False)

    vis_data = gensimvis.prepare(lda, corpus, dictionary)
    pyLDAvis.save_html(vis_data, os.path.join(html_path, lda_id))
