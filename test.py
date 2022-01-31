import tika
from tika import parser
from pathlib import *
# centos
# filename = str(Path.cwd()) + "/ejemplo_esp.pdf"
# windows
filename = str(Path.cwd()) + "\\ejemplo_esp.pdf"

try:
	parsed = parser.from_file(filename, xmlContent=False)
	parsed_txt = parsed["content"]
	str_len = len(parsed_txt)
	print(parsed_txt)
except Exception as e:
	print(e)