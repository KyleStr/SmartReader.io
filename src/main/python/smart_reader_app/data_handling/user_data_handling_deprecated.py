from smart_reader_app.utils.zip2json import zip2txt
from smart_reader_app.data_handling.api_requests import iterative_search
from smart_reader_app.utils.get_synonyms import get_synonyms
from zipfile import ZipFile
from os.path import basename
import os
import shutil
from flask import Response
import json
from datetime import datetime


fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir)))))
DATA_PATH = os.path.join(parentDir, "data", "temporal", "")


def data_handling_zip(logger, model_name, subtopics, path, zip_file='', n_docs=50):
    """
    Function to create a zip file with the documents extracted from the zip file given by the user and APIs.

    Args:
        * logger (Logger): Logger file
        * model_name (str): Name of the model
        * subtopics (list): List of subtopics that the user insert in model definition
        * path (str): Path to download the documents
        * zip_file (str): Name of the zip file of documents given by user
        * n_docs (int): Minimum number of documents to download

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

    f_names = []
    keywords_dict = {}

    if zip_file.split("/")[-1].endswith('.zip'):
        f_names += zip2txt(zipfile=zip_file, path=path)

    pending_files = n_docs - len(f_names)
    logger.info('{} documents obtained from zip'.format(len(f_names)))

    if pending_files > 0:
        files_from_api, keywords_dict = iterative_search(logger, subtopics, path, pending_files=pending_files)

        f_names += files_from_api

        logger.info('{} documents obtained from APIS'.format(len(files_from_api)))

    synonyms = []
    for key in keywords_dict:
        synonyms += get_synonyms(key)

    zip_object = ZipFile('{}{}.zip'.format(path, model_name), 'w')

    for file in os.listdir(path):
        if file.endswith('.txt'):
            zip_object.write(path + file, basename(path + file))
            os.remove(path + file)

    zip_object.close()

    return f_names, keywords_dict, synonyms


def download_documents(logger, filename, file, data_path, subtopics, model_name, minimum_files):
    """
     Main function that calls the rest and performs the Data Handling.

    Args:
        * logger (Logger): Logger file
        * filename (str): Name of the zip file given by user
        * file (FileStorage): File that stores the zipped files
        * data_path (str): Path of the data folder in the execution data directory
        * subtopics (list): List of subtopics that the user insert in model definition
        * model_name (str): Name of the model (given by user in model definition)
        * minimum_files (int): Minimum number of files to be downloaded (given by user in config.ini)

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

    if (len(filename) > 0) and not(filename.endswith('.zip')):
        response = Response(json.dumps({'error': False}), 400, {'contentType': 'application/json'})

    elif (filename.endswith('.zip')) or (len(subtopics) > 0):
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        summary_filename = "summary_json_" + time + ".json"
        folder_name = "text_files_" + time

        file_path = os.path.join(data_path, folder_name)
        os.mkdir(file_path)

        if filename.endswith('.zip'):
            file.save(DATA_PATH + filename)

        file_names, keywords_dict, synonyms = data_handling_zip(logger=logger,
                                                                model_name=model_name,
                                                                subtopics=subtopics,
                                                                path=DATA_PATH,
                                                                zip_file=DATA_PATH + filename,
                                                                n_docs=minimum_files)

        file_topic_zip = '{}{}/{}.zip'.format(DATA_PATH, model_name, model_name)

        logger.debug('\nFile names: {}'.format(file_names))
        logger.debug('\nKeywords: {}'.format(sorted(keywords_dict.items(), key=lambda kv: kv[1], reverse=True)))
        logger.debug('\nSynonyms: {}'.format(synonyms))

        keywords = list(keywords_dict.keys())

        response = Response(json.dumps({'success': True}), 200, {'contentType': 'application/json'})

    else:
        response = Response(json.dumps({'error': False}), 500, {'contentType': 'application/json'})

    return file_topic_zip, file_path, summary_filename, response, keywords, time
