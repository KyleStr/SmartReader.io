import os
import traceback
from pymongo import MongoClient
from smart_reader_app.config import get_config_db

"""
    **database_connectivity**
"""


def get_collections(config_file):
    """
        **get_collections**

        Function for collect the information from config.ini
        and initialize the database

        Args:
            config_file: Environment where the code will be executed

        Returns:
            collection, summary_collection: Database collections
    """

    model_collection = ''
    summary_collection = ''
    corpus_collection = ''
    client = ''

    host, port, authsrc, authmech, usr, psswd = get_config_db(config_file)

    try:
        if host == "localhost":
            client = MongoClient()
        else:
            client = MongoClient(
                host=host,
                port=int(port),
                username=usr,
                password=psswd,
                authSource=authsrc,
                authMechanism=authmech)

        db = client.classifier_database
        model_collection = db.model_jobs
        summary_collection = db.summary_jobs

        corpus_db = client.repositories
        corpus_collection = corpus_db['corpus']

    except Exception as e:
        print(traceback.format_exc(e))

    finally:
        client.close()

    return model_collection, summary_collection, corpus_collection
