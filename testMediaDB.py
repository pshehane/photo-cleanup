#
# test the MediaDB
#
import sys
import MediaDB

# create and destroy
def test1():
    print("Running test1-----------------------")
    MediaDB.InitDB()
    MediaDB.CleanupDB()
    print("Finished test1......................")
    return 0

# create, add, and destroy
def test2(file):
    print("Running test2-----------------------")
    MediaDB.InitDB()
    MediaDB.AddFileToDB(file)
    MediaDB.ReportStats()
    MediaDB.DumpDB()
    MediaDB.CleanupDB()    
    print("Finished test2.....................")
    return 0

# create, add, remove, and destroy
def test3(file):
    print("Running test3----------------------")
    MediaDB.InitDB()
    MediaDB.AddFileToDB(file)
    MediaDB.ReportStats()
    MediaDB.DumpDB()
    MediaDB.RemoveFileFromDB(file)
    MediaDB.DumpDB()
    MediaDB.ReportStats()
    MediaDB.CleanupDB()    
    print("Finished test3....................")
    return 0

# create, add, add duplicate, remove, and destroy
def test4(file):
    print("Running test4----------------------")
    MediaDB.InitDB()
    print("-Adding 1 " + file)
    MediaDB.AddFileToDB(file)
    print("-Adding 2 " + file)
    MediaDB.AddFileToDB(file)
    print("-Adding 3 " + file)
    MediaDB.AddFileToDB(file)
    MediaDB.ReportStats()
    MediaDB.DumpDB()
    MediaDB.RemoveFileFromDB(file)
    MediaDB.DumpDB()
    MediaDB.ReportStats()
    MediaDB.CleanupDB()    
    print("Finished test4....................")
    return 0

# test the UpdateDB function
def test5(file):
    print("Running test5-----------------------")
    MediaDB.InitDB()
    MediaDB.AddFileToDB(file)
    MediaDB.ReportStats()
    MediaDB.DumpDB()
    print("-Update 1")
    MediaDB.UpdateDB()
    print("-Update 2")
    MediaDB.UpdateDB()
    MediaDB.CreateRecommendedTree()
    MediaDB.CleanupDB()    
    print("Finished test5.....................")
    return 0

# test the UpdateDB function
def test6(fileList):
    print("Running test5-----------------------")
    MediaDB.InitDB()
    for file in fileList:
        MediaDB.AddFileToDB(file)
    MediaDB.ReportStats()
    MediaDB.DumpDB()
    MediaDB.UpdateDB()
    MediaDB.CreateRecommendedTree()
    MediaDB.CleanupDB()    
    print("Finished test5.....................")
    return 0
    
def main():
    errors = 0
    if (len(sys.argv) < 3):
        print("Please give a path on the command line")
    else:
        file = sys.argv[2]
        errors = errors + test1()
        errors = errors + test2(file)
        errors = errors + test3(file)
        errors = errors + test4(file)
        errors = errors + test5(file)
        if (len(sys.argv) > 3):
           # fileList = sys.argv
            errors = errors + test6(sys.argv[2:])
        print("All tested completed, Errors: " + str(errors))

main()
