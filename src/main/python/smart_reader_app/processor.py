import os
import time

from smart_reader_app.model.create_model import *
from smart_reader_app.google.search_data import *

collection = ''


def getJob():
    # retrieving what is in the database with the status
    # 'Queued'. e.g.: topics, subtopics, model_name, ect. 
    # result is a dictionary
    result = collection.find({'status': "Queued"}).limit(1)
    return result


def updateJobStatus(jobid, status):
    collection.update(
        {"_id": jobid},
        {
            "$set": {
                "status": status
            }
        }
    )


def run_job(job):
    # Group of 'Queued' jobs retrieved from the database
    for document in job:
        try:
            logger.debug(document["model_name"])
            jobid = document["_id"]
            updateJobStatus(jobid, "Processing")
            topic_text = get_data(document["input"])
            language = document['input']['language']
            # joined text from the results of querying the topics on the internet
            all_text = " ".join([topic_text[text] for text in topic_text])
            if len(all_text.strip()) > 0:
                logger.info("----------------- Creating Model -----------------")
                create_and_save_model(topic_text, os.path.join(models_path, document["output_model_file"]),
                                      language=language)
                logger.info("----------------- Model Created -----------------")
                updateJobStatus(jobid, "Done")
            else:
                updateJobStatus(jobid, "No data")
        except Exception as e:
            logger.error(e)
            updateJobStatus(jobid, "Error")


def processNextJob():
    logger.debug("**********************")
    logger.debug("fetching processor job")
    job = getJob()  # job is a group of jobs that have the 'Queued' status in the database
    jobs_len = job.count()

    if jobs_len == 0:  # excecuted once there are no more 'Queued' jobs in the database
        logger.debug("no more processor jobs to process")
        logger.debug("**********************")
    else:
        run_job(job)
    return jobs_len


def run_processor(logger_instance, model_collection, models_exec_path):
    global logger
    global collection
    global models_path

    logger = logger_instance.set_logger_by_name(__name__).logger
    logger.info("Executing " + __name__)

    models_path = models_exec_path
    collection = model_collection
    cursor = collection.find()

    for document in cursor:
        logger.debug("this is the status " + document["status"])

    while True:
        jobs_check = processNextJob()
        if jobs_check == 0:
            time.sleep(10)
