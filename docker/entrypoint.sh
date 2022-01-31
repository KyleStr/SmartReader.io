#!/bin/bash

# Environment variables substitution
envsubst < docker/config.ini.template > docker/config.ini.temp && cp -f docker/config.ini.temp config/config.ini
envsubst < docker/log.conf.template > docker/log.conf.temp && cp -f docker/log.conf.temp config/log.conf

download="${DOWNLOAD_MODELS:-true}"

# Download models
if [ "$download" = true ] ; then
    echo 'Downloading models and publications...'
    aws s3 cp s3://smart-reader-app-models/glove.6B.100d.txt data/glove/glove.6B.100d.txt
    aws s3 cp s3://smart-reader-app-models/glove-sbwc.i25.txt data/glove/glove-sbwc.i25.txt
    aws s3 cp s3://smart-reader-app-publications/publications.tar.gz data/publications.tar.gz
    aws s3 cp s3://smart-reader-app-publications/blogs/blogs.json data/repositories/blogs.json
    tar --strip-components 1 -xzf data/publications.tar.gz -C data/repositories/
    rm data/publications.tar.gz
    echo 'Inserting corpus into database'
    python ${SERVICE_HOME}/src/main/python/smart_reader_app/mongo_insert_corpus.py
    echo 'Models and publications downloaded!'
else
    echo 'Models and publications not downloaded.'
fi

echo 'Launching SmartReader App...'
exec "$@"
