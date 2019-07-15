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
#from utils import Service, encode_image
import argparse
import string
import re
import telegram_send
import traceback
from retrying import retry

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

#hostname = "shrini_server"
	
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




if not os.path.isdir("./error_1"):
    os.mkdir("./error_1")



if not os.path.isdir("./error_2"):
    os.mkdir("./error_2")



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


for temp_folder in glob.glob("OCR*"):
    shutil.rmtree(temp_folder, ignore_errors=True)


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

hostname =  config.get("settings", "hostname")

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


## Renaming the input files by clearing all special charecters

delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())


lv_path =  input_folder


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
    newname = newname.replace('\'', '-')
    newname = newname.replace('"', '')
    newname = newname.replace('\'', '')
    newname = newname.replace('Å', 'ś')
    newname = newname.replace('Å', 'ń')
    newname = newname.replace(' ', '_')
    newname = newname.replace("'", '_')
    newname = newname.replace('(', '_')
    newname = newname.replace(')', '_')
    newname = newname.replace('[', '_')
    newname = newname.replace(']', '_')
    newname = newname.replace('{', '_')
    newname = newname.replace('}', '_')
    newname = newname.replace('`', '_')
    newname = newname.replace('~', '_')
    newname = newname.replace('@', '_')
    newname = newname.replace('}', '_')

    newname = newname.replace('^', '_')
    newname = newname.replace('&', '_')

    newname = newname.replace('+', '_')
    newname = newname.replace('=', '_')

    newname = newname.replace('"', '_')
    newname = newname.replace("'", '_')
    newname = newname.replace(",", '_')

    newname = newname.replace("\\", '_')
    newname = newname.replace("|", '_')




    #newname = path.translate(str.maketrans("","",delchars))

    #re.sub('[^\w\-_\. ]', '_', newname)

    if newname != path:
        # print(path)
        print(os.path.dirname(path.encode('utf8').decode(sys.stdout.encoding)) + "\t" + os.path.basename(path.encode('utf8').decode(sys.stdout.encoding)) +
              "\t\t\t -> " + os.path.basename(newname.encode('utf8').decode(sys.stdout.encoding)))
        os.rename(path, newname)



telegram_send.send(messages=["Starting OCR on " + hostname])


file_number = 0
total_files = len(glob.glob(input_folder+"/*"))

telegram_send.send(messages=["Total files = " + str(total_files)])


#for input_file in glob.glob(input_folder+"/*"):


#@retry(stop_max_attempt_number=7, wait_fixed=20000)
def do_ocr(input_file,temp_folder):
   
    # Upload the file on Goggle Drive
    folder_id = new_folder_id
    mime = 'application/vnd.google-apps.document'
    file_metadata = {'name': input_file, 'mimeType': mime, 'parents': [folder_id] }
    print(file_metadata)
    media = MediaFileUpload(input_file, mimetype= mime, chunksize=256 * 1024, resumable=True )
    print(media)
    Imgfile = service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id')


    response = None
    while response is None:
        status, response = Imgfile.next_chunk()
        time.sleep(1)
        if status:
            print("Uploaded %d%%." % int(status.progress() * 100))
    print("Upload of {} is complete.".format(input_file))

    basename = "".join(os.path.basename(input_file).split(".")[:-1])
    

    filename = temp_folder + "/" + basename + ".txt"
    time.sleep(10)

    # Download the file in txt format from Google Drive
    getTxt = service.files().export_media( fileId = response['id'], mimeType='text/plain')
    fh = io.FileIO( filename , 'wb' )
    downloader = MediaIoBaseDownload(fh, getTxt)
#    downloader.next_chunk()
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))


    

def prepare_file(source_file, split_number):

    global file_number

    file_number = file_number + 1

    input_filename = source_file.split(input_folder+"/")[1] 
    filetype = input_filename.split(".")[-1].lower()

    logger.info("File Type = " + filetype)


    temp_folder = "OCR-" + input_filename + "-temp-" + timestamp
    logger.info("Created Temp folder " + temp_folder)

    if not os.path.isdir(temp_folder):
        os.mkdir(temp_folder)


    if filetype.lower() == "pdf":



        split_command = "qpdf --split-pages=" + str(split_number) + " " + source_file + " " + temp_folder + "/pg_%d.pdf"
        logging.info("Spliting the PDF file")
        logging.info(split_command)
        os.system(split_command)

    files = []
    for filename in glob.glob(temp_folder + "/" + "pg_*.pdf"):
        files.append(filename)

#    print(files)


# Upload the PDF files to google drive and OCR

    upload_counter = 1

    for pdf_file in sorted(files):
        
        basename = "".join(os.path.basename(pdf_file).split(".")[:-1])
    
        if not os.path.isfile(temp_folder + "/" + basename + ".upload"):

            message = (
                "\n\nuploading " + pdf_file + " to google.   " + str(file_number) +"/" + str(total_files)
            )  # File " + str(upload_counter) + " of " + str(len(files)) + " \n\n"
            logger.info(message)


            try:

                do_ocr(pdf_file, temp_folder)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                telegram_send.send(messages=["ALERT : Error on " + filename + ". Script Stopped at " + hostname +". Rerun again"])
#                sys.exit()
#                os.system("python3 pdf2text.py")

                error_message = "Got issues on " + source_file + " " + str(file_number) +"/" + str(total_files) + " on " + hostname
                telegram_send.send(messages=[error_message])
                traceback_text = traceback.format_exc()
                message = "Error on " + __file__ +  "\n" + traceback_text
                telegram_send.send(messages=[error_message])


            f= open(temp_folder + "/" + basename + ".upload","w+")
            f.close()
            logger.info("Creating temp file "  + "\n")
        

        #   	    move_file(pdf_file)
            logger.info("\n\n========\n\n")
            upload_counter = upload_counter + 1


    pdf_count = len(glob.glob(temp_folder + "/" + "pg_*.pdf"))
    text_count = len(glob.glob(temp_folder + "/"  + "pg_*.txt"))

    missing_files = open("missing_files.txt", "w")

    if not pdf_count == text_count:

        logger.info("\n\n=========ERROR===========\n\n")

        for i in range(1, int(pdf_count) + 1):
            txt_file = "page_" + str(i).zfill(5) + ".txt"
            if not os.path.isfile(txt_file):
                missing_files.write(txt_file + "\n")
                logger.info("Missing " + txt_file)
                logger.info("pg_" + str(i).zfill(5) + ".pdf" + " should be reuploaded ")

        logger.info(
            " \n\nText files are not equal to JPG files. Some JPG files not OCRed. Run this script again to complete OCR all the JPG files \n\n"
        )

#	os.system("telegram-send " + "FAIL : Error on " + input_filename)
        telegram_send.send(messages=["FAIL : Error on " + input_filename])
	


    missing_files.close()

    '''
    files = []
    for textfile in glob.glob(temp_folder  +"/" + "pg*.txt"):
        files.append(textfile)
        files.sort()


    single_file = open("all_text_for_" + input_filename + ".txt", "w")

#    counter = 1 
    for filename in files:
        content = open(filename).read()
#        single_file.write("\n\n")
#        single_file.write("Page " + str(counter))
        single_file.write("\n\n")
        single_file.write(content)
        single_file.write("\n\n")
#        single_file.write("xxxxxxxxxx")
#        counter = counter + 1

    single_file.close()

    shutil.move("all_text_for_" + input_filename + ".txt", output_folder + "/" + "all_text_for_" + input_filename + ".txt" )
    
    logger.info("Merged all OCRed files to  all_text_for_" + input_filename + ".txt")
    '''

    result_text_count = len(glob.glob(temp_folder + "/" + "pg_*.txt"))

    if not pdf_count == result_text_count:
        logger.info("\n\n=========ERROR===========\n\n")
        logger.info(
        " \n\nText files are not equal to PDF files. Some PDF files not OCRed. Run this script again to complete OCR all the PDF files \n\n"
        )
	#os.system("telegram-send " + "FAIL : Error on " + input_filename)
        telegram_send.send(messages=["FAIL : Error on " + source_file])
#        sys.exit()
#        os.system("python3 pdf2text.py")

        
        if "input" in source_file:
            shutil.move(source_file, "./error_1/" )
        
        if "error_1" in source_file:
            shutil.move(source_file, "./error_2/" )


    else:


        files = []
        for textfile in glob.glob(temp_folder  +"/" + "pg*.txt"):
            files.append(textfile)
            files.sort()


        single_file = open("all_text_for_" + input_filename + ".txt", "w")

#    counter = 1 
        for filename in files:
            content = open(filename).read()
#        single_file.write("\n\n")
#        single_file.write("Page " + str(counter))
            single_file.write("\n\n")
            single_file.write(content)
            single_file.write("\n\n")
#        single_file.write("xxxxxxxxxx")
#        counter = counter + 1

        single_file.close()

        shutil.move("all_text_for_" + input_filename + ".txt", output_folder + "/" + "all_text_for_" + input_filename + ".txt" )
    
        logger.info("Merged all OCRed files to  all_text_for_" + input_filename + ".txt")




        message = "\nMoving all temp files to " + temp_folder + "\n"
        logger.info(message)

        for file in glob.glob("*.log"):
            shutil.move(file, temp_folder)

        shutil.move(source_file, "./completed_source_files/" )

        telegram_send.send(messages=["PASS : OCR Done on " + source_file + " "  + "Result file = all_text_for_" + source_file + ".txt " + str(file_number) +"/" + str(total_files) + " on " + hostname])

        shutil.rmtree(temp_folder, ignore_errors=True)



try:
    for source_file in glob.glob(input_folder+"/*"):
        prepare_file(source_file, 20)


    for source_file in glob.glob("error_1/*"):
        prepare_file(source_file, 1)




except Exception as e:
    print(e)
    print(traceback.format_exc())
    error_message = "Got issues on " + source_file + " " + str(file_number) +"/" + str(total_files) + " on " + hostname
    telegram_send.send(messages=[error_message])
    traceback_text = traceback.format_exc()
    message = "Error on " + __file__ +  "\n" + traceback_text
    telegram_send.send(messages=[error_message])

#    os.system("python3 pdf2text.py")



service.files().delete(fileId=new_folder_id).execute()



#for temp_folder in glob.glob("OCR*"):
#    shutil.rmtree(temp_folder, ignore_errors=True)


telegram_send.send(messages=["All files done on " + hostname + ". Add next batch"])    
