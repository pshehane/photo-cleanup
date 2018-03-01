#
# test the MediaDB
#
import sys
import os
import MediaDB
from anytree import  Node,  RenderTree


# test the functionality with a rich set of input
def test(dirList, outputJsonName):
    print("Running test-----------------------")
    MediaDB.InitDB(3)
    for theDir in dirList:
        for root, directories, files in os.walk(theDir):
            for filename in files:
                fullname = os.path.join(root, filename)
                print("--> Adding: ",  fullname)
                MediaDB.AddFileToDB(fullname, root)
    MediaDB.ReportStats()
    MediaDB.DumpDB()
    MediaDB.OutputJson(outputJsonName)
    MediaDB.UpdateDB()
    MediaDB.CreateRecommendedTree()
    outputString = MediaDB.GetRecommendedTreeString()
    print(outputString)
    MediaDB.CleanupDB()    
    print("Finished test.....................")
    return 0
    
def main():
    errors = 0
    if (len(sys.argv) < 3):
        print("Missing arguments, need directory list and json output.")
        print("test.py folderlist.txt json-output.txt")
    else:
        textfilename = sys.argv[1]
        jsonfilename = sys.argv[2]
        dirs = [line.rstrip('\n') for line in open(textfilename)]
        print (dirs)
        errors = test(dirs, jsonfilename)
        print("All tested completed, Errors: " + str(errors))

main()
