# pdf2text (with Google Vision API)

This script will convert your multi pages PDF file to text file using Google VISION API


# Install


# run below command in ubuntu
```

sudo apt-get install poppler-utils mupdf-tools git python3-pip

sudo pip3 install requests

sudo pip3 install configparser
```

# Setup

1. setup VISOION API in Google Cloud Console

See here for the links on setting up 
https://cloud.google.com/vision/docs/before-you-begin

Note: You need a valid credit card to create a Billing Account in Google Cloud.

2. you will get a VISION API as a big string.

3. Enter the required details in config.ini

```
[settings]

file_name = 
columns = 
google_vision_api_key =

[application_path]

mutool = /usr/bin/mutool
pdfseparate = /usr/bin/pdfseparate
pdfunite = /usr/bin/pdfunite
gs = /usr/bin/gs
```

In the [settings] section,

give the PDF file name in file_name

give the column number

give the google_vision_api_key

in the [application_path] section, 

give the full path for mutool, pdfseparate, pdfunite and gs.


# Execute

python3 pdf2text.py



# How it works?

* Python gets the PDF file
* splits using pdfseparate
* cuts the pdf vertically based on column number using mutool
* stitches the pdf using pdfunite
* converts the PDF to JPG using gs (Ghostscript)
* Python sends the image to google and gets as text
* Python combines all text to one single text file.




