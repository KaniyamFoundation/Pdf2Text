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
import io
import string
import re
#from utils import Service, encode_image
import argparse

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload, MediaFileUpload

#parser = argparse.ArgumentParser(description="PDF to Text Convertor", parents=[tools.argparser])

#tools.argparser._action_groups[1].title = 'authentication options'






version = "1.1"

#parser.add_argument('--noauth_local_webserver',help = "noauth_local_webserver")

#parser.add_argument('-p','--pdf-file', help='PDF file name', required=True)
#parser.add_argument('-c','--columns', help='Number of Columns', default="1", required=False)
#parser.parse_known_args(['-p','--pdf-file','-c', '--columns','--noauth_local_webserver'])

#args = parser.parse_args()


#input_filename = args.pdf_file
#columns = args.columns



config = configparser.ConfigParser()
config.read("config.ini")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ts = time.time()
timestamp = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d-%H-%M-%S")


if not os.path.isdir("./log"):
    os.mkdir("./log")


if not os.path.isdir("./completed_source_files"):
    os.mkdir("./completed_source_files")

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




SCOPES = 'https://www.googleapis.com/auth/drive.file'
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flags= tools.argparser.parse_args([])
#flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    #flags=tools.argparser.parse_args(args=[])
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store, flags)
service = build('drive', 'v3', http=creds.authorize(Http()))


file_metadata = {'name': 'ocr_files_shrini',
                  'mimeType': 'application/vnd.google-apps.folder'
                }
folder = service.files().create(body=file_metadata,
                                                    fields='id').execute()
new_folder_id=folder.get('id')




# Read the config file

#input_filename = config.get("settings", "file_name")
input_folder = config.get("settings", "input_folder_name")
output_folder = config.get("settings", "output_folder_name")
columns = config.get("settings", "columns")
#working_directory = config.get("settings", "working_directory")

#google_vision_api_key = config.get("settings", "google_vision_api_key")



MUTOOL = config.get("application_path","mutool")
PDFSEPARATE = config.get("application_path",  "pdfseparate")
PDFUNITE = config.get("application_path",  "pdfunite")
GS = config.get("application_path",  "gs")


if not os.path.isdir(output_folder):
    os.mkdir(output_folder)



if not os.path.isdir(input_folder):
    print("Input Folder does not exist.")
    sys.exit()


logger.info("Input Folder name = " + input_folder)
logger.info("Output Folder name = " + output_folder)
#logger.info("Folder name = " + input_folder)
logger.info("Columns = " + columns)



## Renaming all input files to remove all special charecters and spaces.

delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())


lv_path = input_folder

paths = (os.path.join(root, filename)
         for root, _, filenames in os.walk(lv_path)
         for filename in filenames)

print ("Search at " + lv_path)


for path in paths:
    newname = path.replace('#', '')
    newname = newname.replace('%', '')
    newname = newname.replace('*', '')
    newname = newname.replace('<', '')
    newname = newname.replace('>', '')
    newname = newname.replace('*', '')
    newname = newname.replace('?', '')
    newname = newname.replace('$', '')
    newname = newname.replace('!', '')
    newname = path.replace('\'', '-')
    newname = newname.replace('"', '')
    newname = newname.replace('\'', '')
    newname = path.replace('Å', 'ś')
    newname = path.replace('Å', 'ń')

    newname = path.replace(' ', '_')
    newname = path.replace("'", '_')
    newname = path.replace('(', '_')
    newname = path.replace(')', '_')
    newname = path.replace('[', '_')
    newname = path.replace(']', '_')
    newname = path.replace('{', '_')
    newname = path.replace('}', '_')
    newname = path.replace('`', '_')
    newname = path.replace('~', '_')
    newname = path.replace('@', '_')
    newname = path.replace('}', '_')

    newname = path.replace('^', '_')
    newname = path.replace('&', '_')

    newname = path.replace('+', '_')
    newname = path.replace('=', '_')

    newname = path.replace('"', '_')
    newname = path.replace("'", '_')



    #newname = path.translate(str.maketrans("","",delchars))

    #re.sub('[^\w\-_\. ]', '_', newname)

    if newname != path:
        # print(path)
        print(os.path.dirname(path.encode('utf8').decode(sys.stdout.encoding)) + "\t" + os.path.basename(path.encode('utf8').decode(sys.stdout.encoding)) +
              "\t\t\t -> " + os.path.basename(newname.encode('utf8').decode(sys.stdout.encoding)))
        os.rename(path, newname)




for input_file in glob.glob(input_folder+"/*"):
    print(input_file)


    input_filename = input_file.split(input_folder+"/")[1] 
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
        + input_file
        + '" '
        + temp_folder + "/currentfile.pdf"
        )
        logger.info("Running " + command)

        os.system(command.encode("utf-8"))

    # https://blog.alivate.com.au/poppler-windows/

        message = "Spliting the PDF into single pages. \n"
        logger.info(message)
        burst_command = PDFSEPARATE +   " " + temp_folder + "/currentfile.pdf " + temp_folder + "/pg-%05d.pdf"
        os.system(burst_command)
        logger.info("Running " + burst_command)

        files = []
        for filename in glob.glob(temp_folder + "/" + "pg*.pdf"):
            files.append(filename)
            files.sort()

        chunks = [files[x : x + int(columns)] for x in range(0, len(files), int(columns))]

        counter = 1
        message = "Joining the PDF files ...\n"
        logger.info(message)

        if columns == "1":
            counter = 1
            for pdf in files:
                shutil.copy(pdf, temp_folder +"/" + "page_" + str(counter).zfill(5) + ".pdf")
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
                command = PDFUNITE + " " + com + " " +  temp_folder +"/" + "page_" + str(counter).zfill(5) + ".pdf"
                logger.info("Running " + command)
                counter = counter + 1
                os.system(command)






    logger.info("Converting all the PDF files to JPEG images")
    for pdf in glob.glob(temp_folder +"/" + "page_*.pdf"):

        print(pdf)
        basename = "".join(os.path.basename(pdf).split(".")[:-1])
        print(basename)
        pdf_to_jpg = (
            GS + " -q -DNOPAUSE -DBATCH -r800 -SDEVICE=jpeg  -sOutputFile="
            + temp_folder + "/" + basename
            + ".jpg "
            + pdf
        )

        logger.info(pdf_to_jpg)
        os.system(pdf_to_jpg)


    files = []
    for filename in glob.glob(temp_folder + "/" + "page_*.jpg"):
        files.append(filename)




# Upload the PDF files to google drive and OCR

    upload_counter = 1

    for jpg_file in sorted(files):
        basename = "".join(os.path.basename(jpg_file).split(".")[:-1])
    
        if not os.path.isfile(temp_folder + "/" + basename + ".upload"):

            message = (
                "\n\nuploading " + jpg_file + " to google. "
            )  # File " + str(upload_counter) + " of " + str(len(files)) + " \n\n"
            logger.info(message)



        # Upload the file on Goggle Drive
            folder_id = new_folder_id
            mime = 'application/vnd.google-apps.document'
            file_metadata = {'name': jpg_file, 'mimeType': mime, 'parents': [folder_id] }
            print(file_metadata)
            media = MediaFileUpload( jpg_file, mimetype= mime )
            print(media)
            Imgfile = service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()


            filename = temp_folder + "/" + basename + ".txt"

        # Download the file in txt format from Google Drive
            getTxt = service.files().export_media( fileId = Imgfile.get('id'), mimeType='text/plain')
            fh = io.FileIO( filename , 'wb' )
            downloader = MediaIoBaseDownload(fh, getTxt)
            downloader.next_chunk()



        #text = get_text(jpg_file)



        #file1 = open(filename, "a")
        # file1.write(text,'\n')
        #file1.write("{}\n".format(text))
        #file1.close()

            f= open(temp_folder + "/" + basename + ".upload","w+")
            f.close()
            logger.info("Creating temp file "  + "\n")
        

        #   	    move_file(pdf_file)
            logger.info("\n\n========\n\n")
            upload_counter = upload_counter + 1


    jpg_count = len(glob.glob(temp_folder + "/" + "page_*.jpg"))
    text_count = len(glob.glob(temp_folder + "/"  + "page_*.txt"))

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
    for filename in glob.glob(temp_folder + "/" + "page_*.txt"):
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
    for textfile in glob.glob(temp_folder  +"/" + "page*.txt"):
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

    shutil.move("all_text_for_" + input_filename + ".txt", output_folder + "/" + "all_text_for_" + input_filename + ".txt" )
    
    logger.info("Merged all OCRed files to  all_text_for_" + input_filename + ".txt")


# if not os.path.isdir("text-for-" + filename):
#    os.mkdir("text-for-" + filename)

# command = "cp *.txt text-for-" + filename
# logger.info("Making a copy of all text files to text-for-" + filename)
# logger.info("Running " + command.encode('utf-8'))
# os.system(command.encode('utf-8'))


# message =  "\n\nDone. Check the text files start with text_for_page_ "
# logger.info(message)


    result_text_count = len(glob.glob(temp_folder + "/" + "page_*.txt"))

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

    #shutil.move("currentfile.pdf", temp_folder)

    #for file in glob.glob("pg*.pdf"):
    #    shutil.move(file, temp_folder)

    #for file in glob.glob("page*"):
    #    shutil.move(file, temp_folder)

    #for file in glob.glob("txt*"):
    #    shutil.move(file, temp_folder)

    #for file in glob.glob("*.jpg"):
    #    shutil.move(file, temp_folder)

    shutil.move(input_file, "./completed_source_files/" )

service.files().delete(fileId=new_folder_id).execute()

for temp_folder in glob.glob("OCR*"):
    shutil.rmtree(temp_folder, ignore_errors=True)
