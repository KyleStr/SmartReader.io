import pandas as pd
from smart_reader_app.exceptions.empty_results import EmptyResultsException
import re
from nltk.stem.snowball import SnowballStemmer


def idb_repo_search(logger, idb_collection, subtopics, user_keywords, language, n_docs, dir_path):
    """
    Function to select documents in the IDB corpus according to the search criteria defined in the user's model.

    Args:
        * logger (Logger): Logger file
        * idb_collection: MongoDB collection for IDB repositories and blogs.
        * subtopics (list): List of subtopics that the user insert in model definition
        * user_keywords (list): List of keywords that the user insert in model definition
        * language (str): Selected language
        * dir_path (str): Path where the documents will be saved
        * n_docs (int): Minimum number of files to be downloaded (given by user in config.ini)
    """
    if language == 'es':
        stemmer = SnowballStemmer(language='spanish')

    else:
        stemmer = SnowballStemmer(language='english')

    search_fields = ["title", "description", "subjects", "keywords", "topics"]
    df = term_search(idb_collection, stemmer, search_fields, subtopics, language)
    df["priority"] = 1

    if df.empty | (df.shape[0] < n_docs):
        df_keywords = term_search(idb_collection, stemmer, search_fields, user_keywords, language)
        df_keywords["priority"] = 2
        df = df.append(df_keywords)
        df = df.drop_duplicates(subset='_id')

    if df.empty:
        raise EmptyResultsException("EMPTY_RESULTS")

    df.sort_values(by=["priority", "publicationDate"], inplace=True, ascending=[True, False])

    df = df.head(n_docs)

    subjects = []
    document_urls = {}

    doc_source = {"repositories": "identifier" in df.columns,
                  "blogs": "blogId" in df.columns}

    df.fillna("", inplace=True)

    for index, row in df.iterrows():
        if (doc_source["repositories"]) & (doc_source["blogs"]):
            if row['blogId'] == '':
                subjects += row["subjects"]
            else:
                subjects += row["topics"]
        elif (doc_source["repositories"]) & (not doc_source["blogs"]):
            subjects += row["subjects"]
        elif (doc_source["blogs"]) & (not doc_source["repositories"]):
            subjects += row['topics'].replace("\'", "").replace("[", "").replace("]", "").split(", ")

        subjects = [item for item in subjects if item != '']

        file_name = "IDB_{}_{}.txt".format("_".join(subtopics), index)
        document_urls[file_name] = row['url']
        text_to_save = text_preprocess(str(row["content"]))

        with open("{}/{}".format(dir_path, file_name), "w") as f:
            f.write(str(text_to_save))
            f.close()

    docs_count = df.shape[0]
    logger.info("{} documents are saved as .txt files".format(docs_count))

    pending_docs = n_docs - docs_count

    while (pending_docs > 0) & (subjects != []):
        selected_subject, subjects = next_subject(subjects)

        iter_search_fields = ["subjects", "topics"]
        iter_data = pd.DataFrame()

        for isf in iter_search_fields:
            iter_query = {isf: {"$regex": selected_subject, "$options": "i"},
                          "contentLanguage": language}

            iter_result = idb_collection.find(iter_query)
            iter_data = iter_data.append(pd.DataFrame(list(iter_result)), ignore_index=True)

        iter_df = iter_data.drop_duplicates(subset='_id')

        if iter_df.empty:
            break

        iter_df.sort_values(by="publicationDate", inplace=True, ascending=False)

        cond = iter_df['_id'].isin(df['_id'])
        iter_df.drop(iter_df.loc[cond].index, inplace=True)

        iter_df = iter_df.head(pending_docs)

        for index, row in iter_df.iterrows():
            file_name = "IDB_{}_{}.txt".format(selected_subject, index)
            text_to_save = text_preprocess(str(row["content"]))
            document_urls[file_name] = row['url']

            with open("{}/{}".format(dir_path, file_name), "w") as f:
                f.write(str(text_to_save))
                f.close()

        logger.info("{} documents (subject: {}) are saved as .txt files".format(iter_df.shape[0], selected_subject))

        pending_docs = pending_docs - iter_df.shape[0]

    return document_urls


def term_search(idb_collection, stemmer, search_fields, terms, language):
    """
    Auxiliary function to search for documents in the IDB corpus according to the search criteria defined in the user's model.

    Args:
        * idb_collection: MongoDB collection for IDB repositories and blogs.
        * stemmer:
        * search_fields (list):
        * terms (list): List of terms (topic, subtopics and keywords) that the user insert in model definition
        * language (str): Selected language
    """
    stemmed_search = []

    for token in terms:
        stemmed_search += [stemmer.stem(token).lower()]

    joined_query = "|".join(list(dict.fromkeys(stemmed_search)))

    data = pd.DataFrame()

    for sf in search_fields:
        query = {sf: {"$regex": joined_query, "$options": "i"},
                 "contentLanguage": language}

        result = idb_collection.find(query)
        data = data.append(pd.DataFrame(list(result)), ignore_index=True)

    return data.drop_duplicates(subset='_id')


def next_subject(subjects):
    """
    Auxiliary function to select the most repeated subject to use it in the next search.

    Args:
        * subjects (list): List of subjects for the downloaded documents.

    Returns:
        * selected_subject (str): Most repeated subject in downloaded documents.
        * subjects (list): List of subjects for the downloaded documents without the selected subject.
    """
    selected_subject = max(subjects, key=subjects.count)
    subjects = [item for item in subjects if item != selected_subject]
    return selected_subject, subjects


def text_preprocess(parsed_txt):
    """
    Auxiliary function to pre-process the document content.

    Args:
        * parsed_txt (str): Original document content.

    Returns:
        * parsed_txt (str): Pre-processed content.
    """
    try:
        str_len = len(parsed_txt)

        # Removing Table of Contents, etc.
        if parsed_txt.find("Contents") != -1:
            str_start = parsed_txt.find("Contents")
            parsed_txt = parsed_txt[str_start:str_len]

        # Search and removing References starting from the half of the document
        if parsed_txt.find("References", int(str_len * .5), str_len) != -1:
            str_end = parsed_txt.find("References", int(str_len * .5), str_len)
            to_cut = str_len - str_end
            parsed_txt = parsed_txt[0:-to_cut]

        # Search and removing References starting from the half of the document (for spanish texts)
        if parsed_txt.find("Referencias", int(str_len * .5), str_len) != -1:
            str_end = parsed_txt.find("Referencias", int(str_len * .5), str_len)
            to_cut = str_len - str_end
            parsed_txt = parsed_txt[0:-to_cut]

        # Search and removing References starting from the half of the document (for spanish texts)
        if parsed_txt.find("Bibliografía", int(str_len * .5), str_len) != -1:
            str_end = parsed_txt.find("Bibliografía", int(str_len * .5), str_len)
            to_cut = str_len - str_end
            parsed_txt = parsed_txt[0:-to_cut]

        parsed_txt = re.sub(r"(?:https?|ftp)://[\w_-]+(?:\.[\w_-]+)+(?:[\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", "",
                            parsed_txt)
        parsed_txt = re.sub(r"-\n\n", "", parsed_txt)
        parsed_txt = re.sub(r"-\n", "", parsed_txt)
        parsed_txt = re.sub(r"\n", " ", parsed_txt)
        # removing extra spaces
        parsed_txt = re.sub(r"\s{2,}", " ", parsed_txt)
        # removing excesive punctuation
        parsed_txt = re.sub(r"\n(\.{3,})", "\\1", parsed_txt)
        # trying to remove content of table of contents
        parsed_txt = re.sub(r"(\.{2,} \d{1,}) ([^.!?]*[.!?])", "", parsed_txt)
        # parsed_txt = re.sub(r" (\.{3,})","", parsed_txt)
        # creating paragraphs of 6 sentences - 6 was a random number
        parsed_txt = re.sub(r"(([^.!?]*[.!?]){1,6})", "\\1\n", parsed_txt)

        # Limit the maximum text length
        parsed_txt = parsed_txt[:90000]

    except Exception as e:
        print("Error on text_preprocess (download_idb_corpus.py). An exception occurred: ", e)

    return parsed_txt
