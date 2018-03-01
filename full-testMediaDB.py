#
# test the MediaDB
#
import sys
import os
import MediaDB
from anytree import  Node,  RenderTree


# test the functionality with a rich set of input
def test(dirList):
    print("Running test-----------------------")
    MediaDB.InitDB(3)
    for theDir in dirList:
        for root, directories, files in os.walk(theDir):
            for filename in files:
                print("--> Adding: ",  filename,  "theDir: ",  theDir)
                print("root: ",  root)
                MediaDB.AddFileToDB(filename,  root)
    MediaDB.ReportStats()
    MediaDB.DumpDB()
    MediaDB.UpdateDB()
    MediaDB.CreateRecommendedTree()
    outputString = MediaDB.GetRecommendedTreeString()
    print(outputString)
    MediaDB.CleanupDB()    
    print("Finished test.....................")
    return 0
    
def main():
    errors = 0
    if (len(sys.argv) < 2):
        print("Please give a text file with a list of directories on the command line")
    else:
        textfilename = sys.argv[1]
        dirs = [line.rstrip('\n') for line in open(textfilename)]
        print (dirs)
        errors = test(dirs)
        print("All tested completed, Errors: " + str(errors))

main()
