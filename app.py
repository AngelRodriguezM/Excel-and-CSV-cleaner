import Input.readFolderFiles as readF
from Config import columnMapping #AI

filesFound = readF.readFolderFiles()
print(filesFound)

mappedFiles = columnMapping.mapFiles(filesFound, columnMapping.loadMapping()) #AI
print(mappedFiles) #AI
