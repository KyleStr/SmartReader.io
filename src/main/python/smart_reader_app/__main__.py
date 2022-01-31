import argparse
import os
import threading
import logging

from smart_reader_app.app import define_globals, create_application
from smart_reader_app.config import get_dirs_execution, get_config_application, get_config_google_analytics, get_config_core
from smart_reader_app.database.database_connectivity import get_collections
from smart_reader_app.logger.logger import Logger
from smart_reader_app.processor import run_processor
from smart_reader_app.summary_processor import run_summary

fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir))))
CONFIG_PATH = os.path.join(parentDir, "config", "")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-e', '--environment_config', type=str, required=False, default=CONFIG_PATH + 'config.ini')

    parser.add_argument('-lf', '--log_config', type=str, required=False, default=CONFIG_PATH + 'log.conf')

    args = parser.parse_args()

    environment_config = args.environment_config
    log_config = args.log_config

    init_config(environment_config, log_config)


def wsgi():
    environment_config = CONFIG_PATH + 'config.ini'
    log_config = CONFIG_PATH + 'log.conf'

    init_config(environment_config, log_config)

def gensim_logging_to_error():
    # Gensim INFO logging is too verbose
    gensim_lsimodel_logger = logging.getLogger('gensim.models.lsimodel')
    gensim_lsimodel_logger.setLevel(logging.ERROR)
    gensim_ldamodel_logger = logging.getLogger('gensim.models.ldamodel')
    gensim_ldamodel_logger.setLevel(logging.ERROR)
    gensim_utils_logger = logging.getLogger('gensim.utils')
    gensim_utils_logger.setLevel(logging.ERROR)
    gensim_matutils_logger = logging.getLogger('gensim.matutils')
    gensim_matutils_logger.setLevel(logging.ERROR)
    gensim_corpora_indexedcorpus_logger = logging.getLogger('gensim.corpora.indexedcorpus')
    gensim_corpora_indexedcorpus_logger.setLevel(logging.ERROR)
    gensim_corpora_dictionary_logger = logging.getLogger('gensim.corpora.dictionary')
    gensim_corpora_dictionary_logger.setLevel(logging.ERROR)
    gensim_corpora_mmcorpus_logger = logging.getLogger('gensim.corpora.mmcorpus')
    gensim_corpora_mmcorpus_logger.setLevel(logging.ERROR)
    gensim_similarities_docsim_logger = logging.getLogger('gensim.similarities.docsim')
    gensim_similarities_docsim_logger.setLevel(logging.ERROR)


def init_config(environment_config, log_config):
    
    gensim_logging_to_error()

    model_collection, summary_collection, corpus_collection = get_collections(environment_config)  # Save collections from MongoDB

    base_dir, models_path, summary_path, data_path, html_path = get_dirs_execution(environment_config)

    min_files, num_topics, num_sentences, show_topics, alpha_keywords, n_keywords_ranking, max_sentences = \
        get_config_application(environment_config)

    id_google_analytics = get_config_google_analytics(environment_config)

    core_api_key = get_config_core(environment_config)

    cfg_params = {"num_topics": num_topics, "num_sentences": num_sentences,
                  "show_topics": show_topics, "alpha_keywords": alpha_keywords,
                  "n_keywords_ranking": n_keywords_ranking, "max_sentences": max_sentences}

    collections = {"model": model_collection, "summary": summary_collection, "corpus": corpus_collection}

    logger_instance = Logger(log_conf=log_config)
    logger = logger_instance.set_logger_by_name(__name__).logger

    logger.info("Executing SmartReader")
    logger.info('------------------------------------------------------')
   
    run_api_cfg_params = {"base_dir": base_dir, "data_exec_path": data_path, "summary_exec_path": summary_path,
                          "html_exec_path": html_path,
                          "min_files": min_files, "id_google_analytics": id_google_analytics }

    logger.info("API")
    logger.info('------------------------------------------------------')    
    define_globals(logger_instance, collections, run_api_cfg_params, core_api_key)

    logger.info("PROCESSOR")
    logger.info('------------------------------------------------------')
    th_processor = threading.Thread(name='Processor', target=run_processor,
                                    args=(logger_instance, model_collection, models_path))
    th_processor.setDaemon(True)

    logger.info("SUMMARY")
    logger.info('------------------------------------------------------')
    th_summary = threading.Thread(name='Summary', target=run_summary,
                                  args=(logger_instance, summary_collection, summary_path, models_path, html_path,
                                        cfg_params))
    th_summary.setDaemon(True)

    th_processor.start()
    th_summary.start()


if __name__ == '__main__':
    main()
    app = create_application()
    app.run(debug=True, host="0.0.0.0", port=8080, use_reloader=False)

else:
    wsgi()
    app = create_application()

