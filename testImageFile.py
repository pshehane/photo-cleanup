import sys
import os
import exifread
import re


filePath = "C:\\Users\\hulk\\OneDrive\\MassiveStorage\\PictureArchive\\[D]\\Our Pictures\\Eigth Import\\2-4-2014"
newFilePath = "C:\\"

def get_filepaths(directory):
    """
    This function will generate the file names in a directory 
    tree by walking the tree either top-down or bottom-up. For each 
    directory in the tree rooted at directory top (including top itself), 
    it yields a 3-tuple (dirpath, dirnames, filenames).
    """
    file_paths = []  # List which will store all of the full filepaths.
    new_paths = {}
    file_change = {}
    
    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)  # Add it to the list.

            #Look for directory naming to have hints
            m = re.search('([0-9]?)-([0-9]?)-([12][09][0-9][0-9])',  filepath)
            try:
                year = m.group(3)
                month = str(int(m.group(1)))
                day = str(int(m.group(2)))
                #print("1: " + filename + " Directory would be:  " + year + " " + month + " " + day)
            except Exception as e:
                print("No name in the directory")
                #if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                #   print ("Key: " + str(tag) + ", value " + str(tags[tag]))


            f = open(filepath,  'rb')
            tags = exifread.process_file(f)
            #for tag in tags.keys():
                #if tag in ('ImageUniqueID',  'DateTime'):
            #tag = 'Image DateTime'
            year = 0
            month = 0
            day = 0
            tag = 'EXIF DateTimeOriginal'
            value = tags.get(tag,  "unfound datetime")
            m = re.search('([0-9][0-9][0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([0-9][0-9]):([0-9][0-9]):([0-9][0-9])',  str(value))
            try:
                year = m.group(1)
                month = str(int(m.group(2)))
                day = str(int(m.group(3)))
                #print("2: " + filename + " Directory would be:  " + year + " " + month + " " + day)
            except Exception as e:
                print("No EXIF")
            
            dirname = ""
            if (day != 0):
                a = year
                b = month.zfill(2)
                c = day.zfill(2)
                #a = '{0:2d}-{1:2d}-{2:2d}'.format(int(year), int(month), int(day))
                dirname = a + "-" + b + "-" + c
                if (new_paths.get(dirname,  0) == 0):
                    new_paths[dirname] = []
                new_paths[dirname].append(filename)
                if (file_change.get(filename,  0) == 0):
                    file_change[filename] = {}
                tmpDict = {}
                tmpDict['from'] = root
                tmpDict['to'] = dirname
                file_change[filename] = tmpDict
                #print (dirname + "/" + filename)
    
    for d in new_paths.keys():
        for f in new_paths[d]:
            print("Directory: " + str(d) + " - " + f)
    for f in file_change.keys():
        tmp = file_change[f]
        print("Change file:"  + f +" from "+ tmp['from'] + " to " + tmp['to'])
    return file_paths  # Self-explanatory.

# Run the above function and store its results in a variable.   
full_file_paths = get_filepaths(filePath)
print (full_file_paths)
