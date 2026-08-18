# MultiPrint (Watched Multi-Printer Router)

MultiPrint is a Windows GUI application that allows you to select multiple - Physical and Virtual - printers and print a document to all of them simultaneously. A hot-folder will watch for new files, print them automatically to the selected printers, and then delete the file. 

## General Instructions
1. Select the printers you want to print to
2. Set the print settings for the printers
    - Select duplex printing
    - Select number of copies
4. Select Docuware Import Folder (For Docuware only - leave as default if not using Docuware)
5. Set the folder you want to watch for print jobs (leave as default folder will be created/used)
6. Select Continuous Monitoring or One Time Listen
7. Click Start Listening
8. Prompt Print to PDF and save to the watch folder

## EXE Build Instructions
```
pip install pyinstaller
```
```
pyinstaller printmulti2.spec
```
This will create a dist folder with the EXE