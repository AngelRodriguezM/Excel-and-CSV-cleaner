import pandas as pd 
import os

df = pd.DataFrame

#AI removed the module-level Tk() root: the UI owns the single root, and nothing here uses tkinter

#AI
def findHeaderRow(raw, maxScan=10):
    for i in range(min(maxScan, len(raw) - 1)):
        row = raw.iloc[i]
        # a header row is fully filled and all text; a title row has blanks
        if row.notna().all() and all(isinstance(v, str) for v in row):
            return i
    return 0

#AI
def applyHeader(raw):
    i = findHeaderRow(raw)
    df = raw.iloc[i + 1:].reset_index(drop=True)
    df.columns = raw.iloc[i]
    return df

def readCsv(CsvPath):
    if os.path.exists(CsvPath):
        try:
            read = pd.read_csv(CsvPath, header=None, dtype=str) #AI
            read = applyHeader(read) #AI
            print("file read!")

            return read
        except Exception as e:
            print({e})


def readExcel(ExcelPath):
    if os.path.exists(ExcelPath):
        try:
            read = pd.read_excel(ExcelPath, header=None) #AI
            read = applyHeader(read) #AI
            print("file read!")
            return read
        except Exception as e:
            print({e})

