# pdf2text (with Google Vision API)

This script will convert your multi pages PDF file to text file using Google VISION API


# Install


# run below command in ubuntu
```

sudo apt-get install poppler-utils mupdf-tools git python3-pip

sudo pip3 install requests --ignore-installed

sudo pip3 install configparser --ignore-installed

sudo pip3 install google-api-python-client --ignore-installed

```

# API Setup

# API Setup
 * Create a new project for this tool to access your Google drive
    * Visit https://console.developers.google.com/ , create project, name it anything you like, ex: pdf2text.

 * Enable the following Google APIs in "APIs & auth/APIs"
    * Drive API
    * Fusion Tables API

 * Make sure your application has an application name in "APIs & auth/Consent screen"
    * Find "PRODUCT NAME" field. Make sure it's not blank.

 * Grant access to Google Drive for pdf2text in "APIs & auth/Credentials"
    * Click "Create new Client ID", APPLICATION TYPE: Installed application, INSTALLED APPLICATION TYPE: Other
    * Check the section "Client ID for native application", click at the "Download JSON".
    * save the json file as "client_secret.json" in the same folder where pdf2text.py script is.
 
 When running pdf2text.py, it will open a browser and ask to login to gmail and give permission to the project.
 Do as mentioned on the screen.


# First run

* Copy the PDf file you want to convert to text in the same folder, where pdf2text.py file is.
* Make sure there is no space in the pdf file name. Rename to replace all the spaces with "_"


* run the below command

```

python3 pdf2text.py --noauth_local_webserver -p [pdf_file_name]

```

Give the PDF file name in the [pdf_file_name] 


It will show a link.
Open the link in browser.
Login to your gmail account, which you used to generate client_secret.json
It will show a Key.
Copy the Key and paste in the console.
Press Enter.

It will proceed further with converting the PDF files to text.

Once, all the execution is done, check the same folder for a file, with a name "all_text_for_YOUR_PDF_FILE.PDF.txt"



# second run


For second runs, you can run as below


```

python3 pdf2text.py  -p [pdf_file_name]

```


# Columns

this script can process single column PDF files and double column PDF files.

Single column is default.

For double column files, run as below

```

python3 pdf2text.py  -p [pdf_file_name] -c 2

```


# How it works?

* Python gets the PDF file
* splits using pdfseparate
* cuts the pdf vertically based on column number using mutool
* stitches the pdf using pdfunite
* converts the PDF to JPG using gs (Ghostscript)
* Python sends the image to google and gets as text
* Python combines all text to one single text file.




