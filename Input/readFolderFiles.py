import os
import pandas as pd
from tkinter import Tk, filedialog
from Input import readFiles

#AI folderPath is now an argument (the UI passes it). With no argument it falls back to the old
#AI folder dialog, using a temporary root so no Tk() exists at import time.

def readFolderFiles(folderPath=None):
    if folderPath is None:
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folderPath = filedialog.askdirectory()
        root.destroy()
    if not folderPath:  #AI dialog cancelled
        return {}
    found = False
    foundFiles = {}
    for files in os.listdir(folderPath):
        fullPath = os.path.join(folderPath, files)
        ext = files.lower()
        if ext.endswith(".csv"):
            fileData = readFiles.readCsv(fullPath)
            #TODO identify header row and skip title
            
            #TODO skip blanks and total rows
            

            foundFiles[files] = fileData

            found = True
        elif ext.endswith((".xlsx" , ".xls", ".xlsm")):
            fileData = readFiles.readExcel(fullPath)


            foundFiles[files] = fileData
            found = True
    if not found:
        print("no existing excel or csv file")
    return foundFiles