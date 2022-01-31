import os
from zipfile import ZipFile
from smart_reader_app.utils.pdf2txt import formatPdf2Txt


def zip2txt(zipfile, path):
    """Function that extracts a zip file that can contain pdf files or txt files, parses them, saves
    all the contents in txt format and generates a csv with one document per row.

    Args:
        * zipfile (str): Path to the .zip file to be extracted
        * path (str): Path where the .zip file will be extracted

    Returns:
        list: List of text files

    """
    file_names = []

    try:
        os.mkdir(path)
    except OSError:
        print('The directory {} already exists'.format(path))
    else:
        print('Created the directory {}'.format(path))

    with ZipFile(zipfile, 'r') as zipObj:
        zipObj.extractall(path)

    for pdf in os.listdir(path):
        if pdf.endswith('.pdf'):
            formatPdf2Txt(pdf, root_dir=path)
            os.remove(path + pdf)

    for file in os.listdir(path):
        if file.endswith('.txt'):
            os.rename(path + file, '{}unzip_{}'.format(path, file))
            file_names += ['unzip_{}'.format(file)]

    return file_names
