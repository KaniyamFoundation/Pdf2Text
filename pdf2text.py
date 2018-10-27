#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import requests
import os
import glob
import shutil
import time
import datetime
import configparser
import logging
import os.path
from utils import Service, encode_image

# from urllib.request import urlopen


version = "1"


config = configparser.ConfigParser()
config.read("config.ini")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ts = time.time()
timestamp = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d-%H-%M-%S")


if not os.path.isdir("./log"):
    os.mkdir("./log")


# create a file handler
log_file = "./log/pdf2text_" + timestamp + "_log.txt"

handler = logging.FileHandler(log_file)
handler.setLevel(logging.INFO)

# create a logging format

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# add the handlers to the logger

logger.addHandler(handler)


latest_version = (
    requests.get(
        "https://raw.githubusercontent.com/KaniyamFoundation/Pdf2Text/master/VERSION"
    )
    .text.strip("\n")
    .split(" ")[1]
)

print(latest_version)


if not float(version) == float(latest_version):
    logger.info(
        "\n\nYour pdf2text version is "
        + version
        + ". This is old. The latest version is "
        + latest_version
        + ". Update from https://github.com/KaniyamFoundation/Pdf2Text \n\n"
    )
    sys.exit()


logger.info("Running pdf2text.py " + version)



# Read the config file

input_filename = config.get("settings", "file_name")
#input_folder = config.get("settings", "folder_name")
columns = config.get("settings", "columns")
#working_directory = config.get("settings", "working_directory")

google_vision_api_key = config.get("settings", "google_vision_api_key")



MUTOOL = config.get("application_path","mutool")
PDFSEPARATE = config.get("application_path",  "pdfseparate")
PDFUNITE = config.get("application_path",  "pdfunite")
GS = config.get("application_path",  "gs")




logger.info("File name = " + input_filename)
#logger.info("Folder name = " + input_folder)
logger.info("Columns = " + columns)


filetype = input_filename.split(".")[-1].lower()

logger.info("File Type = " + filetype)


#pdf_dir = working_directory + "/" +  input_filename
#os.mkdir(pdf_dir)
#os.chdir(working_directory)
#shutil.copy(input_filename, pdf_dir +"/" + input_filename)




temp_folder = "OCR-" + input_filename + "-temp-" + timestamp
logger.info("Created Temp folder " + temp_folder)

if not os.path.isdir(temp_folder):
    os.mkdir(temp_folder)


if filetype.lower() == "pdf":

    # split the PDF files vertically based on the column numbers

    message = "Aligining the Pages of PDF file. \n"
    logger.info(message)
    command = (
        MUTOOL + " poster -x "
        + str(columns)
        + " "
        + '"'
        + input_filename
        + '"'
        + "  currentfile.pdf"
    )
    logger.info("Running " + command)

    os.system(command.encode("utf-8"))

    # https://blog.alivate.com.au/poppler-windows/

    message = "Spliting the PDF into single pages. \n"
    logger.info(message)
    burst_command = PDFSEPARATE + " currentfile.pdf pg-%05d.pdf"
    os.system(burst_command)
    logger.info("Running " + burst_command)

    files = []
    for filename in glob.glob("pg*.pdf"):
        files.append(filename)
        files.sort()

    chunks = [files[x : x + int(columns)] for x in range(0, len(files), int(columns))]

    counter = 1
    message = "Joining the PDF files ...\n"
    logger.info(message)

    if columns == "1":
        counter = 1
        for pdf in files:
            shutil.copy(pdf, "page_" + str(counter).zfill(5) + ".pdf")
            # command = "cp " + pdf +  " page_" + str(counter).zfill(5) + ".pdf"
            # logger.info("Running Command " + command)
            counter = counter + 1
            # os.system(command)

    if columns == "2":

        chunks = [
            files[x : x + int(columns)] for x in range(0, len(files), int(columns))
        ]

      
        counter = 1
        message = "Joining the PDF files ...\n"
        logger.info(message)

        for i in chunks:
            com = " ".join(i)
            command = PDFUNITE + " " + com + " " + "page_" + str(counter).zfill(5) + ".pdf"
            logger.info("Running " + command)
            counter = counter + 1
            os.system(command)


def move_file(file):
    source = file
    destination = temp_folder

    if os.path.isdir(temp_folder):
        shutil.move(source, destination)
    else:
        os.mkdir(temp_folder)
        shutil.move(source, destination)
        message = "Moving the file " + file + " to the folder " + temp_folder + "\n"
        logger.info(message)


def get_text(image_file):
    """Run a text detection request on a single image"""

    access_token = google_vision_api_key
    if access_token == "None":
        print("set VISION API KEY in config.ini")
        sys.exit()

    service = Service("vision", "v1", access_token=access_token)
    with open(image_file, "rb") as image:
        base64_image = encode_image(image)
        body = {
            "requests": [
                {
                    "image": {"content": base64_image},
                    "features": [{"type": "TEXT_DETECTION", "maxResults": 1}],
                }
            ]
        }
        response = service.execute(body=body)
        #print(response)
        if "error" in response:
            print(response["error"]["message"])
            sys.exit()

        if response["responses"][0]:
            text = response["responses"][0]["textAnnotations"][0]["description"]
            # print('Found text: {}'.format(text))
        else:
            text = " "

    return text


logger.info("Converting all the PDF files to JPEG images")
for pdf in glob.glob("page_*.pdf"):
    basename = pdf.split(".")[0]
    pdf_to_jpg = (
        GS + " -q -DNOPAUSE -DBATCH -r800 -SDEVICE=jpeg  -sOutputFile="
        + basename
        + ".jpg "
        + pdf
    )
    logger.info(pdf_to_jpg)
    os.system(pdf_to_jpg)


files = []
for filename in glob.glob("page_*.jpg"):
    files.append(filename)


# Upload the PDF files to google drive and OCR

upload_counter = 1

for jpg_file in sorted(files):

    if not os.path.isfile(jpg_file.split(".")[0] + ".upload"):

        message = (
            "\n\nuploading " + jpg_file + " to google. "
        )  # File " + str(upload_counter) + " of " + str(len(files)) + " \n\n"
        logger.info(message)

        text = get_text(jpg_file)

        filename = jpg_file.split(".")[0] + ".txt"

        file1 = open(filename, "a")
        # file1.write(text,'\n')
        file1.write("{}\n".format(text))
        file1.close()

        f= open(jpg_file.split(".")[0] + ".upload","w+")
        f.close()
        logger.info("Creating temp file "  + "\n")
        

        #   	    move_file(pdf_file)
        logger.info("\n\n========\n\n")
        upload_counter = upload_counter + 1


jpg_count = len(glob.glob("page_*.jpg"))
text_count = len(glob.glob("page_*.txt"))

missing_files = open("missing_files.txt", "w")

if not jpg_count == text_count:

    logger.info("\n\n=========ERROR===========\n\n")

    for i in range(1, int(jpg_count) + 1):
        txt_file = "page_" + str(i).zfill(5) + ".txt"
        if not os.path.isfile(txt_file):
            missing_files.write(txt_file + "\n")
            logger.info("Missing " + txt_file)
            logger.info("page_" + str(i).zfill(5) + ".jpg" + " should be reuploaded ")

    logger.info(
        " \n\nText files are not equal to JPG files. Some JPG files not OCRed. Run this script again to complete OCR all the JPG files \n\n"
    )
    sys.exit()


missing_files.close()


files = []
for filename in glob.glob("page_*.txt"):
    files.append(filename)
    files.sort()


# chunks=[files[x:x+int(columns)] for x in xrange(0, len(files), int(columns))]

# counter = 1

# for i in chunks:
#    com =  ' '.join(i)
#    command = "cat  " + com + " > " + "text_for_page_" + str(counter).zfill(5) + ".txt"
#    counter = counter + 1
#    logger.info("Running " + command)
#    os.system(command)


files = []
for textfile in glob.glob("page*.txt"):
    files.append(textfile)
    files.sort()


single_file = open("all_text_for_" + input_filename + ".txt", "w")

counter = 1 
for filename in files:
    content = open(filename).read()
    single_file.write("\n\n")
    single_file.write("Page " + str(counter))
    single_file.write("\n\n")
    single_file.write(content)
    single_file.write("\n\n")
    single_file.write("xxxxxxxxxx")
    counter = counter + 1

single_file.close()


logger.info("Merged all OCRed files to  all_text_for_" + input_filename + ".txt")


# if not os.path.isdir("text-for-" + filename):
#    os.mkdir("text-for-" + filename)

# command = "cp *.txt text-for-" + filename
# logger.info("Making a copy of all text files to text-for-" + filename)
# logger.info("Running " + command.encode('utf-8'))
# os.system(command.encode('utf-8'))


# message =  "\n\nDone. Check the text files start with text_for_page_ "
# logger.info(message)


result_text_count = len(glob.glob("page_*.txt"))

if not jpg_count == result_text_count:
    logger.info("\n\n=========ERROR===========\n\n")
    logger.info(
        " \n\nText files are not equal to JPG files. Some JPG files not OCRed. Run this script again to complete OCR all the JPG     files \n\n"
    )
    sys.exit()


else:

    message = "\nMoving all temp files to " + temp_folder + "\n"
    logger.info(message)

    for file in glob.glob("*.log"):
        shutil.move(file, temp_folder)

    shutil.move("currentfile.pdf", temp_folder)

    for file in glob.glob("pg*.pdf"):
        shutil.move(file, temp_folder)

    for file in glob.glob("page*"):
        shutil.move(file, temp_folder)

    for file in glob.glob("txt*"):
        shutil.move(file, temp_folder)

    for file in glob.glob("*.jpg"):
        shutil.move(file, temp_folder)
