#
# Media Database (MediaDB)
#
# 

import os
import datetime
import re
import exifread
from inspect import currentframe, getframeinfo
from anytree import  Node,  RenderTree

# DictDB structure
# Purpose - master record of all files found
#  key = full path + file name
#  value = { count, meta data }
# ref count is for debugging and if user provided overlapping directory searches
DictDB = {}
# Meta Data for DictDB
#   { FileType, 'Date' from directory, 'Date' from EXIF, 'Date' from stat }

# SortDB structure
# Purpose - conceptual view of files, sorted by date
# key = "YYYY-MM-DD"
# value = original full path + file name (identical to DictDB, so cross reference possible)
SortDB = {}

# Statistics
# as we encounter interesting statistics, we initialize in InitDB (please see below for each item)
StatsDB = {}

# data structure to hold global variables
Globals = {}



#---------------------
# InitDB
# call to initialize the library and the internal DB's
#--------------------
def InitDB(requestedVerboseLevel):
    print("Initializing DB")
    Globals["VerboseLevel"] = requestedVerboseLevel
    StatsDB["Metafile count"] = 0   # .ini files, etc
    StatsDB["Picture count"] = 0     # any still or multi-still image
    StatsDB["Video count"] = 0        # any video sequence
    StatsDB["Raw count"] = 0           # any RAW image files
    StatsDB["Reject count"] = 0      # when the Add fails, due to file not being image-type
    StatsDB["Collision count"] = 0 # when files are duplicate
    StatsDB["Total files"] = 0        # incremented for all files put into the DB
    StatsDB["Error"] = 0                  # for easy lookup from stats DB
    SortDB["RootNode"] = Node("top")


#---------------------
# CleanupDB
# call to clean up, for instance if the UI needs to
#--------------------    
def CleanupDB():
    DebugPrint("Destroying DB",  1)
    DictDB.clear()
    SortDB.clear()
    StatsDB.clear()
#---------------------
# AddFileToDB
# call to add a file to the DB.
# no need to worry about sanitizing the input. it will refcount duplicates for instance
# only "imaging" files are actually added.
# Return count of items    
#--------------------
def AddFileToDB(file):
    count = -1
    DebugPrint("Adding <" + file + "> to DB",  3)
    ftype = IsImagingFile(file)
    if (ftype != '0'):
        entry = DictDB.get(file, 0)
        if (entry == 0):
            #DictDB[file] = count+1
            DictDB[file] = {}
            DictDB[file]['RefCount'] = 1
            # if this is the first time we see this file then treat as unique, otherwise, collision occurred
            StatsDB["Total files"] = StatsDB["Total files"] + 1
            UpdateStatsAdd(ftype)
        else:
            count = DictDB[file].get('RefCount',  0)
            if (count == 0):
                frameinfo = getframeinfo(currentframe())
                errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
                ErrorPrint (errorInfo + "Error! we should not have gotten a zero")
            DictDB[file]['RefCount'] = count + 1
            DictDB[file]['FileType'] = ftype
            StatsDB["Collision count"] = StatsDB["Collision count"] + 1
    return count

#---------------------
# CheckFileInDB
# Return count of items with supplied name
#--------------------
def CheckFileInDB(file):
    DebugPrint("Checking <" + file + "> is in DB",  3)
    count = DictDB.get(file,  0) 
    if (count != 0):
        count = DictDB[file]['RefCount']
    return count

#---------------------
# RemoveFileFromDB
# call to remove a file from the DB.
# no need to worry about sanitizing the input. it will decrement refcount of duplicates for instance
# only "imaging" files are actually added and removed.
# no return
#--------------------    
def RemoveFileFromDB(file):
    DebugPrint("Removing <" + file + "> from DB",  3)
    entry = DictDB.get(file, 0)
    if (entry == 0): 
        # error
        frameinfo = getframeinfo(currentframe())
        errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
        ErrorPrint(errorInfo + "Unknown file: "+ file)
    else:
        count = DictDB[file]['RefCount']
        if (count > 1):
            # decrement reference count
            #DictDB[file] = count - 1
            DictDB[file]['RefCount'] = count - 1
            StatsDB["Collision count"] = StatsDB["Collision count"] - 1
        else:
            ftype = IsImagingFile(file)
            UpdateStatsDel(ftype)
            del DictDB[file]
            StatsDB["Total files"] = StatsDB["Total files"] - 1

#----------------------
# UpdateDB - go thru and update the metadata for each file
#  if new files were added, since last UpdateDB, they will be analyzed
#  old files will only be updated if their file was removed and re-added
#----------------------
def UpdateDB():
    for k in DictDB.keys():
            entry = DictDB.get(k, 0)
            isAnalyzed = entry.get('Analyzed',  0)
            if (isAnalyzed == 0):
                Analyze(k,  entry)

#---------------------
# CreateRecommendedTree
#
# Use the analysis to create a date-based tree
# 
def CreateRecommendedTree():
    DebugPrint("Create Recommended Tree",  1)
    rootNode = SortDB["RootNode"]
    NodeDict = {}
    for k in DictDB.keys():
            entry = DictDB.get(k, 0)
            isAnalyzed = entry.get('Analyzed',  0)
            if (isAnalyzed == 1):
                tSuccess,  tYear,  tMonth,  tDay = DetermineLikelyDate(entry)
                sYear = "%(y)04d" % {"y" : tYear}
                #sMonth = "%(m)02d_%(d)02d" % {"m" : tMonth,  "d"  : tDay}
                sMonth = "%(m)02d" % {"m" : tMonth,  "d"  : tDay}
                sDay = "%(d)02d" % {"m" : tMonth,  "d"  : tDay}
                
                if(1):
                    # the longer way, but apparently get the right output
                    hashForNode = sYear
                    if (NodeDict.get(hashForNode,  0) == 0):
                        yearNode = Node(sYear,  parent=rootNode)
                        NodeDict[hashForNode] = yearNode
                    else:
                        yearNode = NodeDict[hashForNode]
                    hashForNode = sYear+sMonth
                    if (NodeDict.get(hashForNode,  0) == 0):
                        monthNode = Node(sMonth,  parent=yearNode)
                        NodeDict[hashForNode] = monthNode
                    else:
                        monthNode = NodeDict[hashForNode]
                    hashForNode = sYear+sMonth+sDay
                    if (NodeDict.get(hashForNode,  0) == 0):
                        dayNode = Node(sDay,  parent=monthNode)
                        NodeDict[hashForNode] = dayNode
                    else:
                        dayNode = NodeDict[hashForNode]
                    rootpath,  filename = os.path.split(k)
                    fileNode = Node(filename,  parent=dayNode)
                else:
                    # this first attempt, though cleaner, appears to make duplicate nodes side by side under the same parent.
                    # so the above was done to hash in a dictionary the already made nodes, and use them as needed
                    yearNode = Node(sYear,  parent=rootNode)
                    monthNode = Node(sMonth,  parent=yearNode)
                    dayNode = Node(sDay,  parent=monthNode)
                    rootpath,  filename = os.path.split(k)
                    fileNode = Node(filename,  parent=dayNode)
                DebugPrint(str(fileNode),  3)
    DebugPrint("Print Tree:",  4)
    DebugPrint(RenderTree(rootNode),  4)
    DebugPrint("End Tree Print",  4)
    for pre,  fill,  nodule in RenderTree(rootNode):
        DebugPrint("%s%s" % (pre,  nodule.name),  3)
    
# -----
# DumpDB - useful for debug
# ------
def DumpDB():
    DebugPrint("DB contents:",  0)
    for k in DictDB.keys():
        DebugPrint(" " + k + " : " + str(DictDB[k]),  0)

# -----
# ReportStats - useful for debug
# ------
def ReportStats():
    DebugPrint("Statistics:",  0)
    for k in StatsDB.keys():
        DebugPrint(" " + k + " : " + str(StatsDB[k]),  0)


# --- private -------------------------------------------------

DictExtensions = {   '.ini':'i', # meta data
                               '.jpg':'p' , # still image photo
                               '.tiff':'p',
                               '.bmp':'p',
                               '.arf':'r', # still image raw
                               '.dng':'r',
                               '.mov':'v', # video
                               '.mp4':'v', 
                               '.avi':'v'}
Map_TypeToStat = {  'p': "Picture count", 
                                'i': "Metafile count", 
                                'r': "Raw count", 
                                'v': "Video count", 
                                '0': "Reject count"}
 
def IsImagingFile(file):
    the_name, the_extension = os.path.splitext(file)
    lc_extension = the_extension.lower()
    filetype = DictExtensions.get(lc_extension,"0")
    return filetype
    
def UpdateStatsAdd(ftype):
    hash = Map_TypeToStat.get(ftype,  "Error")
    StatsDB[hash]  = StatsDB[hash] + 1

def UpdateStatsDel(ftype):
    hash = Map_TypeToStat.get(ftype,  "Error")
    StatsDB[hash]  = StatsDB[hash] - 1

#-----
# Analyze - where all the work will be!
# look at the file name, file directory path, EXIF info, etc
#-----
def Analyze(file,  fileEntry):
    DebugPrint("Analyzing " + file,  1)
    fileEntry['Analyzed'] = 1
    
    dateStat = FindDateFromStat(file)
    dateDir = FindDateFromDirectory(file)
    dateFile = FindDateFromFilename(file)
    dateEXIF = FindDateFromEXIF(file)
    DebugPrint("Analyzing: " + str(dateStat) + " : " + str(dateDir) + " : " + str(dateFile) + " : " + str(dateEXIF),  2)
    fileEntry['DateStat'] = dateStat
    fileEntry['DateDir'] = dateDir
    fileEntry['DateFile'] = dateFile
    fileEntry['DateEXIF'] = dateEXIF


#-- 
# Find Date functions - each will return a standard  (success, YYYY,MM,DD)  array
#--
def FindDateFromEXIF(file):
    success = 0
    year,  month,  day = 0,  0,  0
    
    f = open(file,  'rb')
    tags = exifread.process_file(f)
    # EXIF has two datetime fields, need to research...
    #tag = 'Image DateTime'
    tag = 'EXIF DateTimeOriginal'
    value = tags.get(tag,  "unfound datetime")
    m = re.search('([0-9][0-9][0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([0-9][0-9]):([0-9][0-9]):([0-9][0-9])',  str(value))
    try:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        success = 1
    except Exception as e:
        frameinfo = getframeinfo(currentframe())
        errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
        ErrorPrint(errorInfo+"No EXIF")
    return [success,  year,  month,  day]
    
def FindDateFromDirectory(file):
    root,  filename = os.path.split(file)
    return regexFileDate(root) # check the root path
    
def FindDateFromFilename(file):
    root,  filename = os.path.split(file)
    return regexFileDate(filename) # check the filename itself

def FindDateFromStat(file):
    mtime = os.path.getmtime(file)
    mod_timestamp = datetime.datetime.fromtimestamp(mtime)
    year = mod_timestamp.year
    month = mod_timestamp.month
    day = mod_timestamp.day
    return [1,  year,  month,  day]

# Refactored from parent functions that are searching the name or path for anything
# that looks like a date string
def regexFileDate(string):
    success = 0
    year,  month,  day = 0,  0,  0
    m = re.search('([0-9][0-9]?)-([0-9][0-9]?)-([12][09][0-9][0-9])',  string)
    try:
        year = int(m.group(3))
        month = int(m.group(1))
        day = int(m.group(2))
        success = 1
    except Exception as e:
        frameinfo = getframeinfo(currentframe())
        errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
        ErrorPrint(errorInfo + "No name in the directory")
    return [success,  year,  month,  day]


def DetermineLikelyDate(fileEntry):
    success,  year,  month,  day = 0,  0,  0,  0
    #scoring method
    # first histogram the 4 possible dates
    hist = {}
    max = ""
    maxCount = 0
    for key in fileEntry.keys():
        if (key == "RefCount"):
            continue
        elif (key == "Analyzed"):
            continue
        # skip unsuccessful dates
        if (fileEntry[key][0] == 0):
            continue
        current = str(fileEntry[key])
        if (hist.get(current,  0) == 0):
            hist[current] = 1
        else:
            hist[current] = hist[current] + 1
        if (hist[current] > maxCount):
            max = current
            maxCount = hist[current]
            success,  year,  month,  day = fileEntry[key]
    DebugPrint (str(hist),  3)
    DebugPrint ("max is " + str(maxCount) + " " + max,  3)
    
    if (len(hist) > 1):
        # see if top two are a match
        listKeys = list(hist.keys())
        DebugPrint(str(listKeys),  3)
        if (hist[listKeys[1]] == maxCount):
            frameinfo = getframeinfo(currentframe())
            errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
            ErrorPrint(errorInfo + "We have a tie!")
    # second priority order
    
    
    return [success,  year,  month,  day]
    
# a quick little function that cleans up the debug prints throughout the code
# example: if verbose is at 3, it prints everything
# if at v=1, then only general function flow is printed
def DebugPrint(printString, printLevel):
    if (printLevel < Globals["VerboseLevel"]):
        print(printString)
# later if we want to do something due to errors
def ErrorPrint(printString):
    print(printString)
