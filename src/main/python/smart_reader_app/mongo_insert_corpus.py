from smart_reader_app.database.database_connectivity import get_collections
import glob
import os
import argparse
import json

fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir))))
CONFIG_PATH = os.path.join(parentDir, "config", "")
DATA_PATH = os.path.join(parentDir, "data", "")


def insert_corpus(environment_config):
    _, _, corpus_collection = get_collections(environment_config)

    file_list = glob.glob("{}/repositories/*".format(DATA_PATH))
    num_files = len(file_list)
    print(num_files)

    corpus_collection.remove({})

    print(environment_config)

    for i, json_file in enumerate(file_list):
        print("File {}/{}: {}".format(i + 1, num_files, json_file))
        with open(json_file, encoding='utf-8-sig') as f:
            file_data = json.load(f)

        if json_file == "{}/repositories/blogs.json".format(DATA_PATH):
            for d in file_data:
                d['publicationDate'] = d.pop("sourceCreationDate")
            corpus_collection.insert_many(file_data)
        else:
            corpus_collection.insert_one(file_data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--environment_config', type=str, required=False, default=CONFIG_PATH + 'config.ini')
    args = parser.parse_args()
    environment_config = args.environment_config

    insert_corpus(environment_config)


if __name__ == '__main__':
    main()
