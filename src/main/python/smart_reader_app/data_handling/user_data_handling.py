from zipfile import ZipFile
from os.path import basename
import os
import shutil
from flask import Response
import json
from datetime import datetime
from smart_reader_app.data_handling.download_core_corpus import core_repo_search
from smart_reader_app.data_handling.download_idb_corpus import idb_repo_search
import glob


fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir)))))
DATA_PATH = os.path.join(parentDir, "data", "temporal", "")


def data_handling_zip(logger, corpus_collection, core_api_key, model_name, subtopics, path, corpus, language, n_docs,
                      user_keywords):
    """
    Function to create a zip file with the documents extracted from the zip file given by the user and APIs.

    Args:
        * logger (Logger): Logger file
        * corpus_collection: MongoDB collection for IDB repositories and blogs.
        * core_api_key (str): IDB KEY for CORE API.
        * model_name (str): Name of the model
        * subtopics (list): List of subtopics that the user insert in model definition
        * path (str): Path to download the documents
        * corpus (str): Name of the selected corpus
        * language (str): Selected language ("es"/"en")
        * n_docs (int): Minimum number of documents to download
        * user_keywords (list): List of keywords that the user insert in model definition

    Returns:
        * f_names (list): Names of the files that compose the corpus for testing
        * keywords_dict (dict): Keywords extracted from APIs (tags)
        * synonyms (list): Obtained synonyms from the APIs keywords

    """
    path = os.path.join(path, model_name, "")

    if os.path.isdir(path):
        shutil.rmtree(path)
    try:
        os.mkdir(path)
    except OSError:
        logger.info('The directory {} already exists'.format(path))
    else:
        logger.info('Created the directory {}'.format(path))

    keywords_dict = {}
    document_urls = {}

    if corpus == 'idb':
        document_urls = idb_repo_search(logger, corpus_collection, subtopics, user_keywords, language, n_docs, path)

    elif corpus == 'core':
        document_urls = core_repo_search(logger, core_api_key, subtopics, language, n_docs, path)

    f_names = glob.glob("{}*".format(path))

    zip_object = ZipFile('{}{}.zip'.format(path, model_name), 'w')

    for file in os.listdir(path):
        if file.endswith('.txt'):
            zip_object.write(path + file, basename(path + file))
            os.remove(path + file)

    zip_object.close()

    return f_names, keywords_dict, [], document_urls


def download_documents(logger, corpus_collection, core_api_key, corpus, language, data_path, subtopics, model_name,
                       minimum_files, user_keywords):
    """
     Main function that calls the rest and performs the Data Handling.

    Args:
        * logger (Logger): Logger file
        * corpus_collection: MongoDB collection for IDB repositories and blogs.
        * core_api_key (str): IDB KEY for CORE API.
        * corpus (str): Name of the corpus. Possible values: 'idb' or 'core'.
        * language (str): Selected language.
        * data_path (str): Path of the data folder in the execution data directory
        * subtopics (list): List of subtopics that the user insert in model definition
        * model_name (str): Name of the model (given by user in model definition)
        * minimum_files (int): Minimum number of files to be downloaded (given by user in config.ini)
        * user_keywords (list): List of keywords that the user insert in model definition

    Returns:
        * file_topic_zip (str): Path of the zip file that will be created for the topic
        * file_path (str): Path of the text files folder
        * summary_filename (str): Name of the json file that will contain the summary information
        * response (Response): Application response
        * keywords (list): List of keywords extracted from APIs (tags)
        * time (str): Date identifier to differentiate generated summaries from the same model
    """
    file_topic_zip = ''
    file_path = ''
    summary_filename = ''
    keywords = {}
    time = ''
    document_urls = {}

    if len(subtopics) > 0:
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        summary_filename = "summary_json_" + time + ".json"
        folder_name = "text_files_" + time

        file_path = os.path.join(data_path, folder_name)
        os.mkdir(file_path)

        file_names, keywords_dict, synonyms, document_urls = data_handling_zip(logger=logger,
                                                                               model_name=model_name,
                                                                               subtopics=subtopics,
                                                                               path=DATA_PATH,
                                                                               corpus=corpus,
                                                                               language=language,
                                                                               n_docs=minimum_files,
                                                                               corpus_collection=corpus_collection,
                                                                               core_api_key=core_api_key,
                                                                               user_keywords=user_keywords)

        file_topic_zip = '{}{}/{}.zip'.format(DATA_PATH, model_name, model_name)

        logger.debug('\nFile names: {}'.format(file_names))
        logger.debug('\nKeywords: {}'.format(sorted(keywords_dict.items(), key=lambda kv: kv[1], reverse=True)))
        logger.debug('\nSynonyms: {}'.format(synonyms))

        keywords = list(keywords_dict.keys())

        response = Response(json.dumps({'success': True}), 200, {'contentType': 'application/json'})

    else:
        response = Response(json.dumps({'error': False}), 500, {'contentType': 'application/json'})

    return file_topic_zip, file_path, summary_filename, response, keywords, time, document_urls
