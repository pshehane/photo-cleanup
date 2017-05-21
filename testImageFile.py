import os
import exifread
import re
import sys

# Testing EXIF read,  and parsing directory names to look for a proposed new name for the directory structure

def main():
    if (len(sys.argv) < 3):
        print("Please give a path on the command line")
    else:
        filePath = sys.argv[2]
        print("Analyzing: " + filePath)
        walk_filepaths(filePath)

def walk_filepaths(directory):
    file_paths = []  # List which will store all of the full filepaths.
    new_paths = {} # construct a dictionary of the new directories that can be made, keyed by the new directory name to use
    file_change = {} # construct a 'from' (original path) and 'to' (new path) dictionary under this dictionary which is keyed by filename.
    
    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)  # Add it to the list.
            year = 0
            month = 0
            day = 0

            # -----------
            # Look for directory naming to have hints
            # -----------
            m = re.search('([0-9]?)-([0-9]?)-([12][09][0-9][0-9])',  filepath)
            try:
                year = m.group(3)
                month = str(int(m.group(1)))
                day = str(int(m.group(2)))
            except Exception as e:
                print("No name in the directory")

            # -----------
            # Look next at the EXIF
            # -----------

            f = open(filepath,  'rb')
            tags = exifread.process_file(f)
            
            # EXIF has two datetime fields, need to research...
            #tag = 'Image DateTime'
            tag = 'EXIF DateTimeOriginal'
            value = tags.get(tag,  "unfound datetime")
            m = re.search('([0-9][0-9][0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([0-9][0-9]):([0-9][0-9]):([0-9][0-9])',  str(value))
            try:
                year = m.group(1)
                month = str(int(m.group(2)))
                day = str(int(m.group(3)))
            except Exception as e:
                print("No EXIF")

            # construct the new directory name 'dirname' if we found anything
            dirname = ""
            if (day != 0):
                a = year
                b = month.zfill(2)
                c = day.zfill(2)
                dirname = a + "-" + b + "-" + c
                
                if (new_paths.get(dirname,  0) == 0):
                    new_paths[dirname] = [] # start an array
                new_paths[dirname].append(filename)
                
                if (file_change.get(filename,  0) == 0):
                    file_change[filename] = {} # start a dictionary
                tmpDict = {}
                tmpDict['from'] = root
                tmpDict['to'] = dirname
                file_change[filename] = tmpDict
    
    # now for seeing if we were successful
    for d in new_paths.keys():
        for f in new_paths[d]:
            print("Directory: " + str(d) + " - " + f)
    for f in file_change.keys():
        tmp = file_change[f]
        print("Change file:"  + f +" from "+ tmp['from'] + " to " + tmp['to'])
    return file_paths

# Run main 
if __name__ == "__main__":
    main()

