import configparser
import os

"""
    **config**
"""


def get_config_db(config_file):
    """
        **get_config_db**

        Obtain the database parameters from configuration file

        Args:
            config_file: Environment where the code will be executed

        Returns:
            host, port, authsrc, authmech, usr, psswd: Database parameters
    """

    config = configparser.ConfigParser()
    config.read(config_file)

    host = config['ENVIRONMENT']['host']
    port = config['ENVIRONMENT']['port']
    authsrc = config['ENVIRONMENT']['authsrc']
    authmech = config['ENVIRONMENT']['authmech']

    usr = config['CREDENTIALS']['usr']
    psswd = config['CREDENTIALS']['psswd']

    return host, port, authsrc, authmech, usr, psswd


def get_config_application(config_file):
    """
        **get_config_application**

        Obtain the API parameters from configuration file

        Args:
            config_file: Environment where the code will be executed

        Returns:
            min_files: APP parameters
    """

    config = configparser.ConfigParser()
    config.read(config_file)

    min_files = config['APP']['min_files']
    num_topics = config['APP']['num_topics']
    num_sentences = config['APP']['num_sentences']
    show_topics = config['APP']['show_topics']
    alpha_keywords = config['APP']['alpha_keywords']
    n_keywords_ranking = config['APP']['n_keywords_ranking']
    max_sentences = config['APP']['max_sentences']

    return min_files, num_topics, num_sentences, show_topics, alpha_keywords, n_keywords_ranking, max_sentences


def get_config_core(config_file):
    """
        **get_config_core**

        Obtain the CORE API-KEY

        Args:
            config_file: Environment where the code will be executed

        Returns:
            core_api_key: CORE API-KEY
    """

    config = configparser.ConfigParser()
    config.read(config_file)

    core_api_key = config['CORE']['core_api_key']

    return core_api_key


def get_config_google_analytics(config_file):
    """
        **get_config_google_analytics**

        Obtain the ID google analytics

        Args:
            config_file: Environment where the code will be executed

        Returns:
            id_google_analytics: GOOGLE parameters
    """

    config = configparser.ConfigParser()
    config.read(config_file)

    id_google_analytics = config['GOOGLE']['id_google_analytics']

    return id_google_analytics


def get_dirs_execution(config_file):
    """
           **get_config_execution**

           Obtain the database parameters from configuration file

           Args:
               config_file: Environment where the code will be executed

           Returns:
               models_path: Database parameters
       """

    config = configparser.ConfigParser()
    config.read(config_file)

    base_dir = config['OUTPUT']['base_dir']
    base_dir = os.path.join(os.getcwd(), base_dir)
    exist_path(base_dir)

    models_path = config['OUTPUT']['models_path']
    models_path = os.path.join(base_dir, models_path)
    exist_path(models_path)

    summary_path = config['OUTPUT']['summary_path']
    summary_path = os.path.join(base_dir, summary_path)
    exist_path(summary_path)

    data_path = config['OUTPUT']['data_path']
    data_path = os.path.join(base_dir, data_path)
    exist_path(data_path)

    html_path = config['OUTPUT']['html_path']
    html_path = os.path.join(base_dir, html_path)
    exist_path(html_path)

    return base_dir, models_path, summary_path, data_path, html_path


def exist_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
