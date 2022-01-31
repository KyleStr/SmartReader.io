from itertools import chain
from nltk.corpus import wordnet


def get_synonyms(keyword):
    """ Function to obtain a list of synonyms of a given keyword using wordnet

    Args:
        keyword (str): Keyword to obtain synonyms

    Returns:
        list: List of synonyms

    """
    synonyms = wordnet.synsets(keyword)
    lemmas = list(set(chain.from_iterable([word.lemma_names() for word in synonyms])))

    return lemmas
