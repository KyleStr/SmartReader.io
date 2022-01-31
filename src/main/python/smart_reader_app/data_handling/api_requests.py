from bs4 import BeautifulSoup as bs
import requests
import os
import pandas as pd
import numpy as np
import re
from collections import Counter
from smart_reader_app.utils.pdf2txt import formatPdf2Txt

fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir)))))
DATA_PATH = os.path.join(parentDir, "data", "temporal", "")
USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)'


def api2txt(logger, subtopics, path, pending_files=200):
    """
    Function to get pdfs from the following APIs: DSpace MIT, Harvard and Cornell. Takes as input the subtopic,
    gets the links to the MIT webpage and analyses the html looking for the document download link. Downloads the pdfs
    and parses them to convert them to text

    Args:
        * logger (Logger): Logger file
        * subtopics (list): List of subtopics that the user insert in model definition
        * path (str): Path where the documents will be saved
        * pending_files (int): Number of files to download

    Returns:
        * file_names (list): List of text files that are generated after download and parse them
        * keywords_dict (dict): Dictionary of keywords extracted from the API tags
    """
    # Get results from the APIs
    id = 0
    APIS = {'DSpace':  'https://dspace.mit.edu',
            'Harvard': 'https://dash.harvard.edu',
            'Cornell': 'https://ecommons.cornell.edu'}

    file_names = []
    keywords_dict = []

    # When rpp is higher than 100, automatically rpp parameter is set to 20
    rpp = min(int(np.ceil(pending_files / 3)), 100)

    query, query_name = get_query(subtopics)

    logger.info('Searching in APIs...')
    for api in APIS:
        logger.info(api + ' API: {}'.format(APIS[api]))

        url = '{}/open-search/?query=title%3D{}%20OR%20summary%3D{}&rpp={}'.format(APIS[api], query, query, rpp)
        r = requests.get(url, headers={'User-agent': USER_AGENT})
        logger.debug('API status: {}'.format(r))

        if r.status_code == 200:

            bs_content = bs(r.text, "lxml")

            links = [a.get('href').replace("http://nrs.harvard.edu/",
                                           "https://dash.harvard.edu/handle/") for a in bs_content.find_all('link',
                                                                                                            href=True)]
            titles = [a.text for a in bs_content.find_all('title')]
            summaries = [a.text for a in bs_content.find_all('summary')]
            authors = get_authors(bs_content)

            links = links[1:]
            titles = titles[1:]

            df = pd.DataFrame(list(zip(titles, links, authors, summaries)),
                              columns=['title', 'link', 'authors', 'summary'])

            df['content'] = None

            for index, row in df.iterrows():
                try:
                    f = requests.get(row['link'], headers={'User-agent': USER_AGENT}, timeout=10)
                    logger.debug("Searching '{}': {}".format(query, f))
                    # Find the link that leads to the pdf file
                    bs_content = bs(f.text, "html.parser")
                    links_page = [a.get('href') for a in bs_content.find_all('a', href=True)]

                    # Obtain keywords from article
                    keywords = bs_content.find_all('meta',
                                                   attrs={'name': 'citation_keywords'})[0].attrs['content'].split(";")
                    keywords_dict += [re.sub(r'[^\w\s]', '', kw.strip().lower()) for kw in keywords]

                    matching = [s for s in links_page if "bitstream/handle" in s]
                    pdf_link = matching[0]

                    # Download and save the linked pdf
                    download_pdf_link = APIS[api] + pdf_link

                    pdf_file = requests.get(download_pdf_link, headers={'User-agent': USER_AGENT}, timeout=(5, 10))

                    if pdf_file.status_code == 200:
                        temporal_pdf = open(path + '{}_{}_{}.pdf'.format(api, query_name, id), 'wb')
                        temporal_pdf.write(pdf_file.content)
                        temporal_pdf.close()

                        formatPdf2Txt('{}_{}_{}.pdf'.format(api, query_name, id), path)
                        os.remove(temporal_pdf.name)

                        f = open(path + '{}_{}_{}.txt'.format(api, query_name, id))

                        id += 1

                        file_names += ['{}{}_{}_{}.txt'.format(path, api, query_name, id)]

                    elif pdf_file.status_code == 429:
                        logger.error('API does not allow more requests')

                except Exception as e:
                    logger.error(e)
                    logger.info('The document is not linked')

    keywords_dict = {x: keywords_dict.count(x) for x in keywords_dict}
    return file_names, keywords_dict


def get_query(subtopics):
    """ Create the query to get the documents that are related with the subtopics given by user. If the list is composed
    by more than one subtopic: the query will be the intersection of all of them

    Args:
        * subtopics (list): List of subtopics to create the query

    Returns:
        * query (str): Subtopics query for the APIs
        * query_name (str): Query identifier for the downloaded files

    """
    if len(subtopics) > 1:
        query = ""
        query_name = ""
        for stp in subtopics:
            query += "'" + stp + "' "
            query_name += stp + " "
        query = query.lstrip().replace("' '", "%22AND%22").replace("'", "%22").replace(" ", "%20")
        query_name = query_name.lstrip().rstrip().replace(" ", "_")

    else:
        query = subtopics[0]
        query_name = subtopics[0]
    return query, query_name


def get_authors(bs_content):
    """ Gets a list of authors extracting this information from the API responses

    Args:
        bs_content (BeautifulSoup): BeutifulSoup content from the API response

    Returns:
        list: List of authors

    """
    authors = []
    for j in bs_content.find_all('entry'):
        lis = ''
        for i in j.find_all('name'):
            lis += i.text + ';'
        authors.append(lis)
    return authors


def keywords_filter(keywords):
    """ Auxiliary function that returns a filtered dictionary. This step is necessary, since API tags contains words as
    'thesis', 'article', 'paper', etc.

    Args:
        * keywords (dict): Keywords obtained from APIs

    Returns:
        dict: Filtered dictionary of keywords


    """
    words2filter = ['thesis', 'dissertation', 'journal', 'article', 'paper', 'publication', 'review', 'essay',
                    'thesis or dissertation', 'dissertation or thesis', 'technical report', 'journal article', 'other',
                    'working paper', 'research paper or report', 'conference paper', 'monograph or book',
                    'cornell university library administration', 'memorial statement', 'cornell university',
                    'biography', 'overview description', 'academic libraries', 'collections',
                    'cornell university library cul', 'sloan school of management', 'administrative record',
                    'periodical', 'weekly', 'academic document', 'scholarly communication', 'report', 'newsletter',
                    'poster', 'book chapter', 'presentation', 'topic', 'institute for data systems and society',
                    'joint program in applied ocean science and engineering', 'woods hole oceanographic institution',
                    'title academic style research essay rhetoric', 'architecture program in media arts and sciences',
                    'system design and management program', 'center for real estate program in real estate development']

    return dict((k, v) for k, v in keywords.items() if (k not in words2filter))


def iterative_search(logger, subtopics, path, pending_files=200, first_search_rate=0.7):
    """
    Function to implement an iterative search: If the model has been created with several subtopics, the first search
    will be the intersection of all of them, then, each subtopic will be independently searched. The rate of documents
    that will be downloaded by the first search is stablished by the `first_search_rate` parameter (70% by default)

    Args:
        * logger (Logger): Logger file
        * subtopics (list): List of subtopics that the user insert in model definition subtopics
        * path (str): Path where the documents will be saved
        * pending_files (int): Number of files to download
        * first_search_rate (float): Rate of downloaded documents by the first search (intersection)

    Returns:
        * f_names (list): List of text files that are generated after download and parse them
        * keywords_dict (dict): Filtered dictionary of keywords extracted from the API tags

    """
    f_names = []

    if len(subtopics) > 1:
        files2search = int(pending_files*first_search_rate)
        file_names, keywords = api2txt(logger, subtopics, path, pending_files=files2search)
        f_names += file_names
        files2search = max(int((files2search - len(file_names))/len(subtopics)), 1)
        for subtopic in subtopics:
            file_names_iter, keywords_iter = api2txt(logger, [subtopic], path, pending_files=files2search)
            f_names += file_names_iter
            keywords = Counter(keywords) + Counter(keywords_iter)
    else:
        file_names, keywords = api2txt(logger, subtopics, path, pending_files=pending_files)
        f_names += file_names

    keywords = keywords_filter(dict(keywords))

    return f_names, keywords
