#
# test the MediaDB
#
import sys
import os
import MediaDB
import datetime
from anytree import  Node,  RenderTree


# test the functionality with a rich set of input
def test(dirList, jsonName, update):
    if (update):
        MediaDB.InitDB(JsonInitFile=jsonName, Debug=1)
    else:
        MediaDB.InitDB(Debug=1)

    for theDir in dirList:
        print("--> Directory: ", theDir)
        for root, directories, files in os.walk(theDir):
            for filename in files:
                fullname = os.path.join(root, filename)
                #print("--> Adding: ",  fullname)
                MediaDB.AddFileToDB(fullname, root)
    #MediaDB.DumpDB()
    MediaDB.UpdateDB()
    MediaDB.ReportStats()
    MediaDB.CreateRecommendedTree()
    outputString = MediaDB.GetRecommendedTreeString()
    MediaDB.OutputJson(jsonName)
    #print(outputString)
    MediaDB.CleanupDB()    
    return 0

def test_json(jsonname, update):
    MediaDB.InitDB(JsonInitFile=jsonname, Debug=1)
    MediaDB.DumpDB()
    return 0
    
def main():
    jsonfilename = ""
    textfilename = ""
    update = False
    errors = 0
    print("Args: "+ str(len(sys.argv)) + ": " + str(sys.argv))
    print("Running test-------- " + str(datetime.datetime.now().time()))
    if (len(sys.argv) <= 1):
        print("If you want to add files to db, then add folderlist.txt")
        print("test.py db.json [folderlist.txt]")
    else:
        arguments = sys.argv
        del arguments[0]
        i = 0
        while (i < len(arguments)):
            #print("i: " + str(i) + " arguments[i] " + arguments[i])
            if (arguments[i] == "-u"):
                update = True
            elif (arguments[i] == "-j"):
                i = i + 1
                jsonfilename = arguments[i]
            elif (arguments[i] == "-d"):
                i = i + 1
                textfilename = arguments[i]
            else:
                print("Unknown command line: " + arguments[i])
            i = i + 1

        if (jsonfilename is ""):
            print("You must supply -j <jsonfile> to either create or read from")
            return
        if (textfilename is ""):
            test_json(jsonfilename, update)
        else:
            dirs = [line.rstrip('\n') for line in open(textfilename)]
            print (dirs)
            errors = test(dirs, jsonfilename, update)
        print("All tested completed, Errors: " + str(errors))
        print("Finished test........ " + str(datetime.datetime.now().time()))
main()
