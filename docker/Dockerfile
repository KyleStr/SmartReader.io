FROM python:3.9-slim-bullseye

LABEL maintainer="IDB"

RUN apt-get update && apt-get install -y gettext-base default-jdk awscli

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download es_core_news_sm
RUN python -m nltk.downloader all

# Configure awscli using the environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
ENV AWS_DEFAULT_REGION=us-east-1
ENV SERVICE_HOME="/code"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3.9/site-packages:${SERVICE_HOME}/src/main/python"
ENV FLASK_ENV production

# Copy project
COPY config ${SERVICE_HOME}/config
COPY src ${SERVICE_HOME}/src
COPY docker ${SERVICE_HOME}/docker

WORKDIR ${SERVICE_HOME}

EXPOSE 8080

ENTRYPOINT [ "docker/entrypoint.sh" ]
CMD gunicorn -c ${SERVICE_HOME}/config/gunicorn.conf.py --pythonpath ${SERVICE_HOME}/src/main/python smart_reader_app.__main__:app