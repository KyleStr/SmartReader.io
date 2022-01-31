from smart_reader_app.model.lda import make_lda
from smart_reader_app.model.textrank import make_textrank
from smart_reader_app.utils.convert_dataset import *
from smart_reader_app.utils.process import *
from smart_reader_app.model.document_ranking import document_ranking
import pandas as pd


def getJob():
    result = summary_collection.find({'status': "Queued"}).limit(1)
    return result


def updateJobStatus(jobid, status):
    summary_collection.update(
        {"_id": jobid},
        {
            "$set": {
                "status": status
            }
        }
    )


def saveSummaries(jobid, summaries):
    with open(summaries) as json_file:
        data = json.load(json_file)

    summary_collection.update(
        {"_id": jobid},
        {
            "$set": {
                "textrank_summary": data
            }
        }
    )

def saveRanking(jobid, rankings):
    df = pd.read_csv(rankings)
    data = []

    for index, row in df.iterrows():
        data += [{row['document_name']: row['url']}]

    summary_collection.update(
        {"_id": jobid},
        {
            "$set": {
                "document_ranking": data
            }
        }
    )


def run_job(job):
    jobid = ""
    '''
    A document is an object of this form:
    {
    '_id': ObjectId('5c9b842ea1c0a02dea101856'), 
    'file_path': '/app/AIResearchHelper/SmartReader/Data/text_files_2019-03-27_10-09-50',
    'summary_filename': 'summary_json_2019-03-27_10-09-50.json',
    'model_name': 'test_1',
    'model_file_name': 'model_Artificial_Intelligence_2019-03-25_14_38_33.pkl',
    'status': 'Queued',
    'timestamp': datetime.datetime(2019, 3, 27, 10, 9, 50, 24000),
    'lda_filename': 2019-03-27_10-09-50_lda.html,
    'lda_topic': 1,
    'textrank_summary': 'TBC'
    'document_ranking': 'TBC'
    }
    '''
    for document in job:
        try:

            jobid = document["_id"]
            updateJobStatus(jobid, "Processing")
            logger.info('*********************CREATING SUMMARY*********************')
            output_json = create_summary(models_path, document["file_path"], document["model_file_name"], document['language'])
            logger.info('*********************CREATING SUMMARY DONE*********************')

            convert_txt_html(html_path, output_json)

            logger.info('*********************DOCUMENT RANKING*********************')
            document_ranking(document["file_path"], get_keywords(output_json, document["keywords"]),
                             alpha=float(alpha_keywords), language=document['language'], urls=document['documents_url'])
            saveRanking(jobid, os.path.join(document['file_path'], 'document_ranking.csv'))
            logger.info('*******************DOCUMENT RANKING DONE*******************')

            json.dump(output_json, open(os.path.join(summary_path, document["summary_filename"]), "w"))

            logger.info('*************************LDA*************************')
            make_lda(logger, document["file_path"], document["lda_filename"], document["lda_topic"],
                     html_path, int(num_topics), int(show_topics), language=document['language'])
            logger.info('*************************LDA DONE*************************')

            logger.info('*************************TEXTRANK*************************')
            make_textrank(logger, document["file_path"], int(num_topics),
                          int(num_sentences), document["lda_topic"], int(max_sentences), language=document['language'])

            saveSummaries(jobid, os.path.join(document['file_path'], 'textrank_summaries.json'))
            logger.info('*************************TEXTRANK DONE*************************')

            updateJobStatus(jobid, "Done")

        except Exception as e:
            logger.error(e)
            updateJobStatus(jobid, "Error")


def processNextJob():
    logger.debug("**********************")
    logger.debug("fetching summary job")
    job = getJob()
    jobs_len = job.count()

    if jobs_len == 0:
        logger.debug("no more summary jobs to process")
        logger.debug("**********************")
    else:
        run_job(job)
    return jobs_len


def get_keywords(js, keywords_api_user):
    """ Function to get the keywords from the summary_json and those that are obtained from user and api.
    Builds the set list of keywords

    Args:
        js (list):
        keywords_api_user (dict): Dictionary with the keywords obtained from model definition (user) and APIs

    Returns:
        list: Set list of keywords
    """
    kw = []
    for i in range(len(js)):
        kw += [js[i]["topic"]]
        for k in js[i]["keywords"]:
            kw += [k["keyword"]]

    # The list of keywords is created by the following priority: user, api and model
    kw = list(set(keywords_api_user['user'] + keywords_api_user['api'] + kw))

    return kw[:int(n_keywords_ranking)]


def run_summary(logger_instance, summary_collection_db, summary_exec_path,
                models_exec_path, html_exec_path, config_params):
    global logger
    global summary_collection
    global summary_path
    global html_path
    global models_path
    global num_topics
    global num_sentences
    global show_topics
    global alpha_keywords
    global n_keywords_ranking
    global max_sentences

    logger = logger_instance.set_logger_by_name(__name__).logger
    logger.info("Executing " + __name__)

    summary_collection = summary_collection_db
    summary_path = summary_exec_path
    models_path = models_exec_path
    html_path = html_exec_path
    num_topics = config_params['num_topics']
    num_sentences = config_params['num_sentences']
    show_topics = config_params['show_topics']
    alpha_keywords = config_params['alpha_keywords']
    n_keywords_ranking = config_params['n_keywords_ranking']
    max_sentences = config_params['max_sentences']

    while True:
        jobs_check = processNextJob()
        if jobs_check == 0:
            time.sleep(10)
