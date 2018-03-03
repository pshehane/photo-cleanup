#
# Media Database (MediaDB)
#
# 

import os
import json
import hashlib
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
NewDirDB = {}

# Statistics
# as we encounter interesting statistics, we initialize in InitDB (please see below for each item)
StatsDB = {}

# data structure to hold global variables
Globals = {}

# Picasa Data
# store the info from picasa both global and image specific
# we will have to reconstruct the file if files move
PicasaDB = {}


#---------------------
# InitDB
# call to initialize the library and the internal DB's
#--------------------
def InitDB(requestedVerboseLevel):
    print("Initializing DB")
    Globals["VerboseLevel"] = requestedVerboseLevel
    StatsDB["Ini count"] = 0   # .ini files, etc
    StatsDB["Meta count"] = 0   # .moff,.thm files, etc
    StatsDB["Picture count"] = 0     # any still or multi-still image
    StatsDB["Video count"] = 0        # any video sequence
    StatsDB["Raw count"] = 0           # any RAW image files
    StatsDB["Reject count"] = 0      # when the Add fails, due to file not being image-type
    StatsDB["Collision count"] = 0 # when files are duplicate
    StatsDB["Total files"] = 0        # incremented for all files put into the DB
    StatsDB["Error"] = 0                  # for easy lookup from stats DB
    StatsDB["DateFromEXIF"] = 0 # debug - how many came from EXIF
    StatsDB["DateFromStat"] = 0 # debug - how many came from Stat
    StatsDB["DateFromDir"] = 0  # debug - how many came from Dir
    StatsDB["DateFromFile"] = 0 # debug - how many came from File
    SortDB["RootNode"] = Node("top")
    PicasaDB["Contacts2"] = {} # list
    PicasaDB["Picasa"] = {} # list

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
# no need to worry about sanitizing the input. it will refcount
# duplicates for instance only "imaging" files are actually added.
# Return count of items    
#--------------------
def AddFileToDB(file,  dir):
    count = -1
    
    DebugPrint("Adding <" + file + "> to DB",  3)

    # is this a file we care about? otherwise ignore
    ftype = IsImagingFile(file)
    if (ftype != '0'):
        if (ftype == 'i'):
            parseIni(file, dir)
            UpdateStatsAdd(ftype)
            return 1

        hashname = hashlib.md5(file.encode('utf-8')).hexdigest()
        entry = DictDB.get(hashname, 0)
        if (entry == 0):
            DictDB[hashname] = {}
            DictDB[hashname]['RefCount'] = 1
            DictDB[hashname]['Name'] = file
            DictDB[hashname]['Directory']= dir
            DictDB[hashname]['FileType'] = ftype
            # if this is the first time we see this file then treat as unique, otherwise, collision occurred
            StatsDB["Total files"] = StatsDB["Total files"] + 1
            UpdateStatsAdd(ftype)
        else:
            count = DictDB[hashname].get('RefCount',  0)
            if (count == 0):
                frameinfo = getframeinfo(currentframe())
                errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
                ErrorPrint (errorInfo + "Error! zero refcount is unexpected")
            DictDB[hashname]['RefCount'] = count + 1
            StatsDB["Collision count"] = StatsDB["Collision count"] + 1
    else:
        ErrorPrint("AddFileToDB: Skipping: " + file)
    return count

#---------------------
# CheckFileInDB
# Return count of items with supplied name
#--------------------
def CheckFileInDB(file):
    hashname = hashlib.md5(file.encode('utf-8')).hexdigest()
    DebugPrint("Checking <" + file + "> is in DB",  3)
    count = DictDB.get(hashname,  0) 
    if (count != 0):
        count = DictDB[hashname]['RefCount']
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
    hashname = hashlib.md5(file.encode('utf-8')).hexdigest()
    entry = DictDB.get(hashname, 0)
    if (entry == 0): 
        # error
        frameinfo = getframeinfo(currentframe())
        errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
        ErrorPrint(errorInfo + "Unknown file: "+ file)
    else:
        count = DictDB[hashname]['RefCount']
        if (count > 1):
            # decrement reference count
            DictDB[hashname]['RefCount'] = count - 1
            StatsDB["Collision count"] = StatsDB["Collision count"] - 1
        else:
            ftype = IsImagingFile(file)
            UpdateStatsDel(ftype)
            del DictDB[hashname]
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
# todo: go back over the DB and look for dependencies
# -----  .moff, .modd, .thm files need to go with parent of similar name
# -----  .picasa.ini files
# -----   ??

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
            fullname = entry.get('Name', "(null)")
            if (isAnalyzed == 1):
                tSuccess,  tYear,  tMonth,  tDay = DetermineLikelyDate(entry, fullname)
                sYear = "%(y)04d" % {"y" : tYear}
                sMonth = "%(m)02d" % {"m" : tMonth,  "d"  : tDay}
                sDay = "%(d)02d" % {"m" : tMonth,  "d"  : tDay}

                newpath = os.path.join(sYear, sMonth, sDay)
                entry.setdefault('NewDirectory', newpath)
                NewDirDB['newpath'] = k  # cross reference with 'hashname'
                
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
                rootpath,  filename = os.path.split(fullname)
                fileNode = Node(filename,  parent=dayNode)
                DebugPrint(str(fileNode),  3)
    DebugPrint("Print Tree:",  4)
    DebugPrint(RenderTree(rootNode),  4)
    DebugPrint("End Tree Print",  4)
    for pre,  fill,  nodule in RenderTree(rootNode):
        DebugPrint("%s%s" % (pre,  nodule.name),  3)

def GetRecommendedTreeString():
    string = ""
    for pre,  fill,  nodule in RenderTree(SortDB["RootNode"]):
        string = string + "%s%s\n" % (pre,  nodule.name)
    return string
    
# -----
# DumpDB - useful for debug
# ------
def DumpDB():
    DebugPrint("DB contents:",  0)
    for k in DictDB.keys():
        stringOut = " " + k + " : " + str(DictDB[k])
        #stringOut = stringOut + " : " + DictDB[k]
        DebugPrint(stringOut,  0)

# -----
# OutputJson
# -----
def OutputJson(outputName):
    SuperStructure = {}
    SuperStructure['DictDB'] = DictDB
    SuperStructure['StatsDB'] = StatsDB
    SuperStructure['PicasaDB'] = PicasaDB
    SuperStructure['NewDirDB'] = NewDirDB

    jsonFile = open(outputName, "w")
    jstr = json.dumps(SuperStructure, sort_keys=True,
                      indent=4, separators=(',', ': '))
    jsonFile.write(jstr)
    jsonFile.close()

# -----
# ReportStats - useful for debug
# ------
def ReportStats():
    DebugPrint("Statistics:",  0)
    for k in StatsDB.keys():
        DebugPrint(" " + k + " : " + str(StatsDB[k]),  0)


# --- private -------------------------------------------------

DictExtensions = {   '.ini':'i', # ini data
                               '.jpg':'p' , # still image photo
                               '.tiff':'p',
                               '.bmp':'p',
                               '.arf':'r', # still image raw
                               '.arw':'r',
                               '.dng':'r',
                               '.thm':'m', # meta data
                               '.moff':'m',
                               '.modd':'m',
                               '.mov':'v', # video
                               '.mp4':'v',
                               '.mts':'v',
                               '.mpg':'v',
                               '.m2ts':'v',
                               '.avi':'v'}
Map_TypeToStat = {  'p': "Picture count", 
                                'i': "Ini count",
                                'r': "Raw count", 
                                'm': "Meta count",
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
def Analyze(hashname,  fileEntry):
    theFile = fileEntry.get('Name', "(null)")
    justFileName = os.path.basename(theFile)
    DebugPrint("Analyzing " + theFile,  1)
    fileEntry['Analyzed'] = 1
    theDir = fileEntry.get('Directory',  "(nulldir)")
    dateStat = FindDateFromStat(theFile) # need full path, accessing file
    dateDir = FindDateFromDirectory(theDir) # need just dir path
    dateFile = FindDateFromFilename(justFileName) # need just the name
    dateEXIF = FindDateFromEXIF(theFile) # need full path, accessing file
    DebugPrint("Analyzing: Stat:" + str(dateStat) + " DirName:" + str(dateDir) + " FileName:" + str(dateFile) + " EXIF:" + str(dateEXIF),  2)
    fileEntry['DateStat'] = dateStat
    fileEntry['DateDir'] = dateDir
    fileEntry['DateFile'] = dateFile
    fileEntry['DateEXIF'] = dateEXIF
    if (dateStat[0]):
        StatsDB['DateFromStat'] = StatsDB['DateFromStat'] + 1
    if (dateEXIF[0]):
        StatsDB['DateFromEXIF'] = StatsDB['DateFromEXIF'] + 1
    if (dateDir[0]):
        StatsDB['DateFromDir'] = StatsDB['DateFromDir'] + 1
    if (dateFile[0]):
        StatsDB['DateFromFile'] = StatsDB['DateFromFile'] + 1
    theParentDir = os.path.basename(theDir)
    print("Analyze: tag = " + theParentDir)
    if ('Tag' not in fileEntry):
        fileEntry['Tag'] = theParentDir

#-- 
# Find Date functions - each will return a standard  (success, YYYY,MM,DD)  array
#--
def FindDateFromEXIF(file):
    success = 0
    year,  month,  day = 0,  0,  0
    # EXIF has two datetime fields, need to research...
    #tag = 'Image DateTime'
    tag = 'EXIF DateTimeOriginal'

    f = open(file,  'rb')
    #print("FindDateFromEXIF:" + file)
    try:
        tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal', debug=True)
    except MemoryError:
        tags = {}
    except TypeError:
        tags = {}
    except IndexError:
        tags = {}
    f.close()
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
        ErrorPrint(errorInfo+"No EXIF tag in file:" + file)
    return [success,  year,  month,  day]
    
def FindDateFromDirectory(file):
    #print("FindDateFromDir:" + file)
    root,  filename = os.path.split(file)
    return regexFileDate1(root) # check the root path
    
def FindDateFromFilename(file):
    #print("FindDateFromFile:" + file)
    root,  filename = os.path.split(file)
    return regexFileDate1(filename) # check the filename itself

def FindDateFromStat(file):
    #print("FindDateFromStat:" + file)
    mtime = os.path.getmtime(file)
    mod_timestamp = datetime.datetime.fromtimestamp(mtime)
    year = mod_timestamp.year
    month = mod_timestamp.month
    day = mod_timestamp.day
    return [1,  year,  month,  day]

# Refactored from parent functions that are searching the name or path for anything
# that looks like a date string

RegExPatterns = {
        ## Use 3 parens to select (1st) (2nd) (3rd) and then label:
        ##  YY , MM, DD with where to find it. 
        ##     Example: 2013-4-17  (xxxx)-(x)-(xx) and 1, 2, 3
        ##     Example: 4-17-2013  (x)-(xx)-(xxxx) and 3, 1, 2
        '([0-9][0-9]?)-([0-9][0-9]?)-([12][09][0-9][0-9])' : [ 3,  1,  2],  # MM-DD-YYYY
        '([0-9][0-9]?)_([0-9][0-9]?)_([12][09][0-9][0-9])' : [ 3,  1,  2],  # MM_DD_YYYY
        '^([0-9][0-9]?)([0-9][0-9]?)([12][09][0-9][0-9])' : [ 3,  1,  2],  # MM_DD_YYYY
        '([12][09][0-9][0-9])-([0-9][0-9]?)-([0-9][0-9]?)' : [ 1,  2,  3],  # YYYY-MM-DD
        '^([12][09][0-9][0-9])([0-9][0-9]?)([0-9][0-9]?)' : [ 1,  2,  3],  # YYYY-MM-DD
    }


# original, simple method.  not used
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
        success = 0
        #frameinfo = getframeinfo(currentframe())
        #errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
        #ErrorPrint(errorInfo + "No dateinfo in the string: " + string)
    return [success,  year,  month,  day]

def regexFileDate1(string):
    success = 0
    year,  month,  day = 0,  0,  0
    for key in RegExPatterns.keys():
        regPattern = key
        m = re.search(".*" + regPattern + ".*",  string)
        try:
            indexYear,  indexMonth,  indexDay = RegExPatterns[key]
            year = int(m.group(indexYear))
            month = int(m.group(indexMonth))
            day = int(m.group(indexDay))
            success = 1
            break
        except AttributeError as e:
            success = 0
            #frameinfo = getframeinfo(currentframe())
            #errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
            #ErrorPrint(errorInfo + "No dateinfo in the string: " + string + " using " + regPattern)
    return [success,  year,  month,  day]


# Simple approach to determine best date; Priority assignment
#  Let us assume:  if EXIF info - then it wins.
#  If not, then Filename has the info, next Directory name, and finally Stat.
#  Stat = file creation
def DetermineLikelyDate(fileEntry,  filename):
    success,  year,  month,  day = 0,  0,  0,  0
    if ('DateEXIF' in fileEntry):
       [success, year, month, day] = fileEntry['DateEXIF']
    if (success == 0 and 'DateFile' in fileEntry):
       [success, year, month, day] = fileEntry['DateFile']
    if (success == 0 and 'DateDir' in fileEntry):
       [success, year, month, day] = fileEntry['DateDir']
    if (success == 0 and 'DateStat' in fileEntry):
       [success, year, month, day] = fileEntry['DateStat']
    if (success == 0):
        ErrorPrint("ERROR no date for: " + filename)
    return [success, year, month, day]

# First approach, which looks at now many dates are the same, and use that
# concern is, if EXIF is actually more believable, the others could be
# human error.  EXIF is only wrong if intentionally changed or the device
# was set to the wrong time/date.
def VotingBased_DetermineLikelyDate(fileEntry,  filename):
    success,  year,  month,  day = 0,  0,  0,  0
    #scoring method
    # first histogram the 4 possible dates
    hist = {}
    max = ""
    maxCount = 0
    for key in fileEntry.keys():
        # weed out the keys that are not "Date"
        if (re.search("Date", key) is None):
            continue
        # skip unsuccessful dates
        if (fileEntry[key][0] == 0):
            continue
        current = str(fileEntry[key])
        print ("current: " + current)
        if (hist.get(current,  0) == 0):
            hist[current] = 1
        else:
            hist[current] = hist[current] + 1
        if (hist[current] > maxCount):
            max = current
            maxCount = hist[current]
            success,  year,  month,  day = fileEntry[key]
    
    if (len(hist) > 1):
        # see if top two are a match
        listKeys = list(hist.keys())
        DebugPrint(str(listKeys),  3)
        if (hist[listKeys[1]] == maxCount):
            frameinfo = getframeinfo(currentframe())
            errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
            ErrorPrint(errorInfo + "We have a tie! " + filename)
            DebugPrint (str(hist),  0)
            DebugPrint ("max is " + str(maxCount) + " " + max,  0)
    # second priority order
    return [success,  year,  month,  day]

def parseIni(filename, directory):
    # we will only process the properly named picasa ini file

    if (os.path.basename(filename) != ".picasa.ini" and
        os.path.basename(filename) != "Picasa.ini" and
        os.path.basename(filename) != ".Picasa.ini"):
        ErrorPrint("Skipping processing: " + filename + " : " + directory)
        return
    lines = [line.rstrip('\n') for line in open(filename, encoding="utf8")]
    mode = 0  # 0=idle, 1=contacts, 2=image, 3=Picasa
    hashname = "" # remember the image name's hash
    for l in lines:
        nameInLine = re.search("^\[([^\]]+)\]$", l)
        if (l == "[Contacts2]"):
            mode = 1 # contacts
        elif (l == "[Picasa]"):
            mode = 3 # Picasa
        elif (nameInLine != None):
            mode = 2 # image info
            imageName = nameInLine.group(1)
            fullImageName = os.path.join(directory, imageName)
            hashname = hashlib.md5(fullImageName.encode('utf-8')).hexdigest()
            entry = PicasaDB.get(hashname, 0)
            if (entry == 0):
                PicasaDB[hashname] = {}
                PicasaDB[hashname]["Name"] = fullImageName
                PicasaDB[hashname]["Directory"] = directory
                PicasaDB[hashname]["RefCount"] = 1
            else:
                count = PicasaDB[hashname].get('RefCount',  0)
                if (count == 0):
                    frameinfo = getframeinfo(currentframe())
                    errorInfo = str(frameinfo.filename) + ":" + str(frameinfo.lineno) + "> "
                    ErrorPrint (errorInfo + "Error! zero refcount is unexpected")
                PicasaDB[hashname]['RefCount'] = count + 1
        else: # normal line, so pull according to state
            m = re.search("^([a-z0-9]+)=(.+)$", l)
            try:
                phash = m.group(1)
                pcontent = m.group(2)
                if (mode == 1):
                    PicasaDB['Contacts2'][phash] = pcontent
                elif (mode == 3):
                    PicasaDB['Picasa'][phash] = pcontent
                elif (mode == 2):
                    entry = PicasaDB[hashname].get(phash, 0)
                    if (entry == 0):
                        PicasaDB[hashname][phash] = pcontent
                    else:
                        if (entry != pcontent):
                            ErrorPrint("Overwriting picasa data! Mismatch!")
                            ErrorPrint("Overwriting:" + entry + "::" + pcontent)
            except AttributeError as e:
                pass

# a quick little function that cleans up the debug prints throughout the code
# example: if verbose is at 3, it prints everything
# if at v=1, then only general function flow is printed
def DebugPrint(printString, printLevel):
    if (printLevel < Globals["VerboseLevel"]):
        print(printString)
# later if we want to do something due to errors
def ErrorPrint(printString):
    print(printString)
