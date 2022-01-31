from tika import parser
import os
import re
from os import listdir


fileDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(fileDir)))))
DATA_PATH = os.path.join(parentDir, "data", "temporal", "")


def formatPdf2Txt(filepath, root_dir, sensitivity='private', id=""):
    file_name = root_dir + filepath

    try:
        parsed = parser.from_file(file_name, xmlContent=False)
        parsed_txt = parsed["content"]
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

        with open(root_dir + filepath[0:-4] + ".txt", "a+", encoding="utf-8") as f:
            f.write(parsed_txt)
            f.close()

    except Exception as e:
        print("Error on formatPdf2Txt (pdf2txt.py). An exception occurred: ", e)


if __name__ == "__main__":
    for pdf in listdir(DATA_PATH):
        formatPdf2Txt(pdf, DATA_PATH)
