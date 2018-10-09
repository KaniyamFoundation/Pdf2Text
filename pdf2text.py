#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import requests
import os
from clint.textui import progress
import glob
import shutil
import time
import datetime
import ConfigParser
import urllib
import logging
import urllib2
import os.path
from utils import Service, encode_image






version = "1"


config = ConfigParser.ConfigParser()
config.read("config.ini")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



ts = time.time()
timestamp  = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')


if not os.path.isdir("./log"):
    os.mkdir("./log")


# create a file handler
log_file = './log/pdf2text_' + timestamp + '_log.txt'

handler = logging.FileHandler(log_file)
handler.setLevel(logging.INFO)

# create a logging format

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger

logger.addHandler(handler)



latest_version =  urllib2.urlopen('https://raw.githubusercontent.com/KaniyamFoundation/Pdf2Text/master/VERSION').read().strip('\n').split(' ')[1]

if not float(version) == float(latest_version):
    logger.info("\n\nYour pdf2text version is " + version + ". This is old. The latest version is " + latest_version + ". Update from https://github.com/KaniyamFoundation/Pdf2Text \n\n")
    sys.exit()




logger.info("Running pdf2text.py " + version)


os_info = open("/etc/lsb-release")
for line in os_info:
	if  "DISTRIB_DESCRIPTION" in line:
		os_version = line.split("=")[1]

logging.info("Operating System = " + os_version)





#Read the config file

input_filename = config.get('settings','file_name').replace(' ','_')
input_folder = config.get('settings','folder_name')
columns = config.get('settings','columns')



logger.info("File name = " + input_filename )
logger.info("Folder name = " + input_folder )
logger.info("Columns = " + columns )



filetype = input_filename.split('.')[-1].lower()

logger.info("File Type = " + filetype)


temp_folder = "OCR-" + input_filename + '-temp-'+ timestamp
logger.info("Created Temp folder " + temp_folder)

if not os.path.isdir(temp_folder):
    os.mkdir(temp_folder)
                            

if filetype.lower() == "pdf":

	# split the PDF files vertically based on the column numbers

    message =  "Aligining the Pages of PDF file. \n"
    logger.info(message)
    command = "mutool poster -x " + str(columns)  + " " + '"' +  input_filename + '"' +  "  currentfile.pdf"
    logger.info("Running " + command.encode('utf-8'))
        
    os.system(command.encode('utf-8'))
                

# https://blog.alivate.com.au/poppler-windows/

    message =  "Spliting the PDF into single pages. \n"
    logger.info(message)
    burst_command = "pdfseparate currentfile.pdf pg-%05d.pdf"
    os.system(burst_command)
    logger.info("Running " + burst_command) 

        
    files = []
    for filename in glob.glob('pg*.pdf'):
        files.append(filename)
        files.sort()

    chunks=[files[x:x+int(columns)] for x in xrange(0, len(files), int(columns))]

    counter = 1
    message =  "Joining the PDF files ...\n"
    logger.info(message)

    if columns == "1":
        counter = 1
        for pdf in files:
            command = "cp " + pdf +  " page_" + str(counter).zfill(5) + ".pdf"
            logger.info("Running Command " + command)
            counter = counter + 1
            os.system(command)


    if columns == "2":

	    chunks=[files[x:x+int(columns)] for x in xrange(0, len(files), int(columns))]

	    counter = 1
	    message =  "Joining the PDF files ...\n"
	    logger.info(message)
	        
	    for i in chunks:
	        com =  ' '.join(i)
	        command = "pdfunite " + com + " " + "page_" + str(counter).zfill(5) + ".pdf"
	        logger.info("Running " + command) 
	        counter = counter + 1
	        os.system(command)
                                

        

def move_file(file):
    source = file
    destination = temp_folder

    if os.path.isdir(temp_folder):
        shutil.move(source,destination)
    else:
        os.mkdir(temp_folder)
        shutil.move(source,destination)
        message =  "Moving the file " + file + " to the folder " + temp_folder + "\n"
        logger.info(message)


def get_text(photo_file):
    """Run a text detection request on a single image"""

    access_token = os.environ.get('VISION_API')
    print(access_token)
    if access_token == 'None':
        print("Import VISION API KEY")
        sys.exit()

    service = Service('vision', 'v1', access_token=access_token)
    with open(photo_file, 'rb') as image:
        base64_image = encode_image(image)
        body = {
            'requests': [{
                'image': {
                    'content': base64_image,
                },
                'features': [{
                    'type': 'TEXT_DETECTION',
                    'maxResults': 1,
                }]

            }]
        }
        response = service.execute(body=body)
        #print(response)
        if response['responses'][0]:
            text = response['responses'][0]['textAnnotations'][0]['description']
            #print('Found text: {}'.format(text))
        else:
            text = " "

    return text

                

logger.info("Converting all the PDF files to JPEG images")
for pdf in glob.glob('page_*.pdf'):
    basename = pdf.split(".")[0]
    pdf_to_jpg = "gs -q -DNOPAUSE -DBATCH -r400 -SDEVICE=jpeg  -sOutputFile=" + basename + ".jpg " + pdf
    logger.info(pdf_to_jpg)
    os.system(pdf_to_jpg)

 
files = []
for filename in glob.glob('page_*.jpg'):
    files.append(filename)




#Upload the PDF files to google drive and OCR

upload_counter = 1

for jpg_file in sorted(files):


    if not os.path.isfile(jpg_file.split('.')[0] + ".upload"):                        
                                                

        message= "\n\nuploading " + jpg_file + " to google. "     # File " + str(upload_counter) + " of " + str(len(files)) + " \n\n"
        logger.info(message)

        text = get_text(jpg_file)   

        filename = jpg_file.split(".")[0] + ".txt"

        file1=open(filename,"a")
        #file1.write(text,'\n')
        file1.write("{}\n".format(text))
        file1.close()
                                                            
        create_temp_file = "touch " + jpg_file.split('.')[0] + ".upload"
        logger.info("\n  Creating temp file " + create_temp_file + "\n")
        os.system(create_temp_file)
                        

#   	    move_file(pdf_file)
        logger.info( "\n\n========\n\n")
        upload_counter = upload_counter + 1



jpg_count = len(glob.glob('page_*.jpg'))
text_count = len(glob.glob('page_*.txt'))

missing_files = open('missing_files.txt','w')

if not jpg_count == text_count:

            logger.info("\n\n=========ERROR===========\n\n")
            
            for i in range(1,int(jpg_count)+1):
                        txt_file = "page_" + str(i).zfill(5) + ".txt"
                        if not os.path.isfile(txt_file):
                                    missing_files.write(txt_file +"\n")
                                    logger.info( "Missing " + txt_file)
                                    logger.info( "page_" + str(i).zfill(5) + ".jpg" + " should be reuploaded ")
                                                                         

            logger.info(" \n\nText files are not equal to JPG files. Some JPG files not OCRed. Run this script again to complete OCR all the JPG files \n\n")
            sys.exit()

            
missing_files.close()
            

files = []
for filename in glob.glob('page_*.txt'):
        files.append(filename)
        files.sort()


# Split the text files to sync with the original images

logger.info("Split the text files to sync with the original images")


if int(columns)==1:
        i = 1
        for textfile in files:
                with open(textfile,'r') as filetosplit:
                         content = filetosplit.read()
                        
                         if len(content)>50:
                                 with open('txt_'+str(i).zfill(5)+'.txt', 'w') as towrite:
                                         towrite.write(content)
                                 i = i+1
                         else:

                                with open('txt_'+str(i).zfill(5)+'.txt', 'w') as towrite:
                                	towrite.write(' ')
                                i = i+1

                                                                                                                              

                                        

elif int(columns)==2:
                                                                                                                                                
    i = 1
    for textfile in files:
        with open(textfile,'r') as filetosplit:
                content = filetosplit.read()
                if "________________" in content:
                        records = content.split('________________')
                        #print records
                        for record in records[1::2]:
                                with open('txt_'+str(i).zfill(5)+'.txt', 'w') as towrite:
                                        towrite.write(record)
                                i = i+1
                else:
                        for no in range(int(columns)):
                                with open('txt_'+str(i).zfill(5)+'.txt', 'w') as towrite:
                          	      towrite.write(' ')
                                i = i+1
                                
                    


logger.info("Joining text files based on Column No")
                                
files = []
for filename in glob.glob('txt*.txt'):
        files.append(filename)
        files.sort()

                                                

chunks=[files[x:x+int(columns)] for x in xrange(0, len(files), int(columns))]

counter = 1
                                               
for i in chunks:
        com =  ' '.join(i)
        command = "cat  " + com + " > " + "text_for_page_" + str(counter).zfill(5) + ".txt"
        counter = counter + 1
        logger.info("Running " + command)
        os.system(command)



message =  "\nMoving all temp files to " + temp_folder + "\n"
logger.info(message)
command = "mv folder*.log currentfile.pdf  doc_data.txt pg*.pdf page* txt* *.jpg  " + '"' +  temp_folder + '"'
logger.info("Running " + command.encode('utf-8'))
os.system(command.encode('utf-8'))





files = []
for textfile in glob.glob('text_for_page*.txt'):
            files.append(textfile)
            files.sort()

            
single_file = open("all_text_for_" + filename + ".txt" ,"w")

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
                                                                

logger.info("Merged all OCRed files to  all_text_for_" + filename + ".txt")


if not os.path.isdir("text-for-" + filename):
            os.mkdir("text-for-" + filename)

command = "cp *.txt text-for-" + filename
logger.info("Making a copy of all text files to text-for-" + filename)
logger.info("Running " + command.encode('utf-8'))
os.system(command.encode('utf-8'))




if keep_temp_folder_in_google_drive == "no":
        message =  "\nDeleting the Temp folder in Google Drive " + temp_folder + "\n"
        logger.info(message)
        command = "gdrm.py " + drive_folder_id
        logger.info("Running " + command)
        os.system(command)


message =  "\n\nDone. Check the text files start with text_for_page_ "
logger.info(message)




result_text_count = len(glob.glob('text_for_page_*.txt'))

if not jpg_count == result_text_count:
            logger.info("\n\n=========ERROR===========\n\n")
            logger.info(" \n\nText files are not equal to JPG files. Some JPG files not OCRed. Run this script again to complete OCR all the JPG     files \n\n")
            sys.exit()



                                        