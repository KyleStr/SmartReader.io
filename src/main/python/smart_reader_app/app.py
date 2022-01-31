import json
from bson import ObjectId
import os
import re
import zipfile
import webbrowser
import glob

from datetime import datetime
import requests
from flask import Flask, render_template, request, Response
from werkzeug.utils import secure_filename

from smart_reader_app.data_handling.user_data_handling import download_documents
from smart_reader_app.exceptions.empty_results import EmptyResultsException

fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir))))
DATA_PATH = os.path.join(parentDir, "data", "temporal", "")

collection = ""
summary_collection = ""
corpus_collection = ""
current_lang = "es"

def create_application():

    app = Flask(__name__)

    @app.context_processor
    def inject_analytics():
        return dict(id_google_analytics=google_analytics)

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    @app.route("/", methods=["GET"])
    @app.route("/<string:lang>/", methods=["GET"])
    def index_page(lang=current_lang):
        html = "lda_landing_es.html"
        if lang in languages:
            html = "lda_landing_" + lang + ".html"

        return render_template("landing_page.html", language=getLang(lang), lda_html = html)


    @app.route("/app", methods=["GET"])
    @app.route("/<string:lang>/app", methods=["GET"])
    def home_page(lang=current_lang):
        return render_template("index.html", language=getLang(lang))


    @app.route("/lda", methods=["GET"])
    def lda():
        lda = request.args["lda"]
        with open((html_path + lda), "r") as lda_html:
            return lda_html.read()

        return "Error"


    @app.route("/app/GenerateDataCollection", methods=["GET"])
    @app.route("/<string:lang>/app/GenerateDataCollection", methods=["GET"])
    def data_collection_page(lang=current_lang):
        return render_template("data_collection.html", language=getLang(lang))


    @app.route("/app/GenerateSummary", methods=["GET"])
    @app.route("/<string:lang>/app/GenerateSummary", methods=["GET"])
    def generate_summary_page(lang=current_lang):
        return render_template("generate_summary.html", language=getLang(lang))


    @app.route("/app/ModelsStatus")
    @app.route("/<string:lang>/app/ModelsStatus", methods=["GET"])
    def get_model_status_page(lang=current_lang):
        return render_template("models_status.html", language=getLang(lang))


    @app.route("/app/SummariesStatus")
    @app.route("/<string:lang>/app/SummariesStatus", methods=["GET"])
    def get_summary_status_page(lang=current_lang):
        return render_template("summaries_status.html", language=getLang(lang))


    @app.route("/app/VisualizeSummary", methods=["GET"])
    @app.route("/<string:lang>/app/VisualizeSummary", methods=["GET"])
    def visualize_summary(lang=current_lang):

        summary_obj = summary_collection.find_one({"_id": ObjectId(request.args["_id"])})
        with open((summary_path + summary_obj["summary_filename"]), "r") as sj:
            output_json = json.load(sj)

        summary_json = json.dumps(output_json)
        return render_template(
            "visualize_summary.html",
            summary=summary_obj,
            summary_json=summary_json,
            lda_html=summary_obj.get("lda_filename"),
            language=getLang(lang)
        )


    @app.route("/DownloadSummary", methods=["GET"])
    def download_summary():
        summary_filename = request.args["summary_filename"]
        with open((summary_path + summary_filename), "r") as sj:
            summary_json = json.load(sj)

        summary_json = json.dumps(summary_json)
        return Response(
            summary_json,
            mimetype="application/json",
            headers={"Content-disposition": "attachment; filename=" + summary_filename},
        )


    @app.route("/returnjson")
    def return_json():
        filename = request.args["filename"]
        with open((summary_path + filename), "r") as sj:
            summary_json = json.load(sj)
        summary_json = json.dumps(summary_json)
        return summary_json


    @app.route("/generate_data_model", methods=["POST"])
    def get_data():
        try:
            json_obj = {}

            json_obj["model_name"] = request.form["model"]
            json_obj["topic_name"] = [request.form["topic"]]
            json_obj["language"] = request.form["radioLang"]
            json_obj["subtopics"] = []
            if request.form["topic2"]:
                json_obj["topic_name"].append(request.form["topic2"])
            if request.form["topic3"]:
                json_obj["topic_name"].append(request.form["topic3"])

            num_subtopics = int(request.form["youcantseeme"])
            for i in range(num_subtopics):
                subtopic_i = {}
                if request.form["subtopic" + str(i)]:
                    subtopic_i["subtopic_name"] = request.form["subtopic" + str(i)]
                    subtopic_i["keywords"] = [
                        re.sub("[^A-Za-z0-9 ]+", "", x.strip())
                        for x in request.form["keywords" + str(i)].split(",")
                    ]
                    json_obj["subtopics"].append(subtopic_i)

            model_name = json_obj["model_name"]
            output_model_file_name = (
                "model_"
                + json_obj["topic_name"][0].replace(" ", "_")
                + "_"
                + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                + ".pkl"
            )
            timestamp = datetime.now()
            collection.insert(
                {
                    "input": json_obj,
                    "model_name": model_name,
                    "output_model_file": output_model_file_name,
                    "timestamp": timestamp,
                    "status": "Queued",
                }
            )

            return Response(
                json.dumps({"success": True}), 200, {"contentType": "application/json"}
            )

        except:
            return json.dumps({"error": False}), 500, {"contentType": "application/json"}


    @app.route("/get_status")
    def get_status():
        models = []
        cursor = collection.find({}).sort([("timestamp", -1)])
        for document in cursor:
            models.append(
                [
                    document["model_name"],
                    document["status"],
                    document["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    str(document["_id"])
                ]
            )
        model_json = json.dumps(models)
        return model_json


    @app.route("/get_models")
    def get_models():
        models = []
        cursor = collection.find({"status": "Done"})
        for document in cursor:
            models.append(
                [
                    document["model_name"],
                    document["output_model_file"],
                    document["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        model_json = json.dumps(models)
        return model_json


    @app.route("/create_summary", methods=["POST"])
    def upload_file():
        try:
            model = request.form.get("model")
            model_name = " ".join(model.split(",")[:-1]).strip()
            model_file_name = model.split(",")[
                -1
            ].strip()  # storing the model name with the model's creation date
            idb_core = request.form.get("idb_core")

            subtopics = []
            user_keywords = []
            user_topic = []
            language = []
            cursor = collection.find({"output_model_file": model_file_name})
            for document in cursor:
                user_topic += document["input"]["topic_name"]
                language = document["input"]["language"]
                for stp in document["input"]["subtopics"]:
                    subtopics += [stp["subtopic_name"]]
                    user_keywords += stp["keywords"]

            user_keywords += subtopics
            user_keywords += user_topic
            user_keywords = list(set(user_keywords))

            subtopics = user_topic + subtopics

            (
                file_topic_zip,
                file_path,
                summary_filename,
                response,
                api_keywords,
                time,
                documents_url
            ) = download_documents(
                logger, corpus_collection, api_key_core, idb_core, language, data_path, subtopics, model_name,
                int(minimum_files), user_keywords
            )

            keywords = {"api": api_keywords, "user": user_keywords}

            upload_input_files(file_topic_zip, file_path)

            timestamp = datetime.now()
            lda_filename = time + "_lda.html"
            lda_topic = time + "_lda_topic_id.csv"

            summary_collection.insert(
                {
                    "file_path": file_path,
                    "language": document["input"]["language"],
                    "summary_filename": summary_filename,
                    "model_name": model_name,
                    "model_file_name": model_file_name,
                    "status": "Queued",
                    "timestamp": timestamp,
                    "lda_filename": lda_filename,
                    "lda_topic": lda_topic,
                    "keywords": keywords,
                    "textrank_summary": "TBC",
                    "document_ranking": "TBC",
                    "documents_url": json.dumps(documents_url)
                }
            )
        except EmptyResultsException as e:
            logger.error("Empty search")
            response = Response(json.dumps(e.to_dict()), 404, {'contentType': 'application/json'})
        except Exception as e:
            logger.error(e)
            response = Response(json.dumps({'error': False}), 500, {'contentType': 'application/json'})

        return response


    @app.route("/summary_status")
    def get_summary_status():
        summary = []
        cursor = summary_collection.find({}).sort([("timestamp", -1)])
        for document in cursor:
            summary.append(
                [
                    document["summary_filename"],
                    document["model_name"],
                    document["status"],
                    document["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    document.get("lda_filename"),
                    str(document["_id"]),
                ]
            )

        summary_json = json.dumps(summary)
        return summary_json


    @app.route("/download", methods=["GET", "POST"])
    def download():
        summary_filename = request.form.get("summary_filename")

        with open(("Summaries/" + summary_filename), "r") as sj:
            summary_json = json.load(sj)

        summary_json = json.dumps(summary_json)
        return Response(
            summary_json,
            mimetype="application/json",
            headers={"Content-disposition": "attachment; filename=" + summary_filename},
        )


    @app.route("/show_summaries", methods=["GET", "POST"])
    def show_summaries():
        url = request.data.decode("utf-8")
        try:
            with open(url, "r") as html:
                return html.read()
        except Exception as e:
            logger.error(e)


    return app


def upload_input_files(filename, file_path):
    try:
        with zipfile.ZipFile(os.path.join(filename), "r") as zip_ref:
            zip_ref.extractall(file_path)
    except Exception as e:
        logger.error(e)
    try:  # removing original name of zip file
        for root, dirs, files in os.walk(file_path, topdown=False):
            if root != file_path:
                for name in files:
                    source = os.path.join(root, name)
                    target = os.path.join(file_path, name)
                    os.rename(source, target)
    except Exception as e:
        logger.error(e)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
        os.remove(filename)


def define_globals(logger_instance, collections, run_api_cfg_params, core_api_key):
    """
    Define global variables
    """
    global logger
    global collection
    global summary_collection
    global corpus_collection
    global data_path
    global summary_path
    global html_path
    global minimum_files
    global exec_data
    global google_analytics
    global languages
    global current_lang
    global api_key_core

    logger = logger_instance.set_logger_by_name(__name__).logger
    summary_path = run_api_cfg_params["summary_exec_path"]
    collection = collections["model"]
    summary_collection = collections["summary"]
    corpus_collection = collections["corpus"]
    data_path = run_api_cfg_params["data_exec_path"]
    minimum_files = run_api_cfg_params["min_files"]  
    exec_data = run_api_cfg_params["base_dir"]
    html_path = run_api_cfg_params["html_exec_path"]
    google_analytics = run_api_cfg_params["id_google_analytics"]
    api_key_core = core_api_key

    languages = {}
    language_list = glob.glob("src/main/python/smart_reader_app/langs/*.json")

    for lang in language_list:
        filename = lang.split('/')
        count = len(filename)
        lang_code = filename[count-1].split('.')[0]
        with open(lang, 'r', encoding='utf8') as file:
            languages[lang_code] = json.loads(file.read())


# Obtiene las traducciones para el idioma indicado. 
# Si no existe retorna las traducciones para el idioma por defecto
def getLang(lang):
    if lang in languages :
        return languages[lang]
    else :
        return languages[current_lang]
