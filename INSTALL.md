INSTALL
=======

Just run the below command

```
bash ./setup.sh
```

This will install all the required packages.




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
 

That' all.

You can see this demo video in Tamil with English Subtitles to setup the gdcmdtools.
https://www.youtube.com/watch?v=PH9TnD67oj4&feature=youtu.be


