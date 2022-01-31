import requests
import pandas as pd
import os
from smart_reader_app.utils.pdf2txt import formatPdf2Txt
from smart_reader_app.exceptions.empty_results import EmptyResultsException


def core_repo_search(logger, api_key, subtopics, language, n_docs, dir_path):
    """
    Function to search for documents in CORE repository according to the search criteria defined in the user's model.

    Args:
        * logger (Logger): Logger file
        * api_key (str): IDB KEY for CORE API.
        * subtopics (list): List of subtopics that the user insert in model definition
        * language (str): Selected language
        * dir_path (str): Path where the documents will be saved
        * n_docs (int): Minimum number of files to be downloaded (given by user in config.ini)
    """

    headers = {"Authorization": "Bearer " + api_key}

    downloaded_files = 0
    result_urls = []
    document_urls = {}

    logger.info("Request to CORE")
    try:
        get_query = requests.get(
            f"https://api.core.ac.uk/v3/search/works?q={'+'.join(subtopics)}&entity_type=journals&exclude=fullText&limit={n_docs}&language={language}",
            headers=headers)
        get_query.raise_for_status()

        if get_query.status_code == 200:
            result = pd.DataFrame(get_query.json()['results'])

            if result.empty:
                raise EmptyResultsException("EMPTY_RESULTS")

            result = result.drop(result[result['downloadUrl'] == ''].index)
            result_urls = list(result['downloadUrl'].values)

    except requests.exceptions.HTTPError as err:
        logger.error(err)

    except Exception as e:
        logger.error(e)

    logger.info("Downloading documents")
    for idx, ru in enumerate(result_urls):
        if "arxiv" in ru:
            ru = ru.replace("abs", "pdf") + ".pdf"

        logger.debug("Downloading {}".format(ru))

        try:
            singlework = requests.get(ru)

            if singlework.status_code == 200:
                temporal_pdf = open('{}/CORE_{}_{}.pdf'.format(dir_path, "_".join(subtopics), idx), 'wb')
                temporal_pdf.write(singlework.content)
                temporal_pdf.close()

                formatPdf2Txt('CORE_{}_{}.pdf'.format("_".join(subtopics), idx), dir_path)
                os.remove(temporal_pdf.name)

                document_urls['CORE_{}_{}.txt'.format("_".join(subtopics), idx)] = ru

                downloaded_files += 1

        except requests.exceptions.ConnectionError:
            continue

    if downloaded_files == 0:
        raise EmptyResultsException("EMPTY_RESULTS")
    
    logger.info("Downloaded {} documents".format(downloaded_files))

    return document_urls
