#-------------------------------------------------
# Photo Cleanup Tool
#
# This python + QT tool has the user select where all their photos and videos are stored
#  then analyzing as best it can to determine the date of the photos/videos, and then creates
#  a new directory structure at the destination, which will be clean and cronological.
#  Over more than a dozen years of sync'ing digital cameras, smartphones, and family shared images,
#  some order is needed to this mess.  Online backups are organized, but the original archive is what we 
#  have locally.
#
# This uses MediaDB for most of the underlying analysis and management of the files
# This file is primarily the UI component to it
#
# author - patrick shehane
# date - July 9 2017
#-------------------
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QLabel, QPushButton
from PyQt5.QtWidgets import QHBoxLayout,QVBoxLayout, QScrollArea
from PyQt5.QtGui import QPainter, QColor
#from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QMainWindow, QAction
#from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMenuBar
#from PyQt5.QtGui import QIcon
#from PyQt5.QtCore import QRect
from PyQt5.QtCore import Qt,  QSize
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import *
import math
import os
import MediaDB

class PaintWidget(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.color = QColor(0, 0, 0)
        self.init_ui()
        self.theTree = {}
        self.myWidth = 500
        self.myHeight = 70
        
    def init_ui(self):
        print("paint init")
    def paintEvent(self, event):
        print("paint")
        qp = QPainter(self)
        qp.begin(self)
        qp.fillRect(event.rect(),  QBrush(self.color))
        self.drawTree(qp)
        qp.end()
        
    def mousePressEvent(self, event):
        self.setFocus(Qt.OtherFocusReason)
        event.accept()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.color = QColor(self.color.green(), self.color.blue(),
                                127 - self.color.red())
            self.update()
            self.clicked.emit()
            event.accept()
    def sizeHint(self):    
        return QSize(self.myWidth,  self.myHeight)
    def setTree(self,  treeDict):
        print("tree")
        self.theTree = treeDict
    def drawTree(self,  qp):
        x = 0
        y = 0
        count = len(self.theTree.keys()) + 1
        print("Count:" + str(count))
        maxArea = self.myWidth * self.myHeight
        boxArea = maxArea / count
        print("Area:" + str(maxArea) + " " + str(boxArea))
        boxSide = int(math.sqrt(boxArea))
        print("Box side: " + str(boxSide))
        
        for k in self.theTree.keys():
            #print("k:" + str(k) + " val:" + str(self.theTree[k]))
            if (self.theTree[k] == 0):
                c = Qt.white
            elif (self.theTree[k] == 1):
                c = Qt.blue
            else: # 2
                c = Qt.red
            qp.setPen(c)
            qp.fillRect(x,  y,  boxSide,  boxSide,  c)
            qp.setPen(Qt.black)
            qp.drawRect(x,  y,  boxSide,  boxSide)
            
            x = x+boxSide
            if (x > self.myWidth):
                y = y+boxSide
                x = 0
            if (y > self.myHeight):
                y = 0

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        os.chdir('C:\\')
        self.FileCounter = 0
        self.DictSearchDirectories = {}
        self.DictFiles = {}
        self.DictExtensions = {'.ini':'i', # meta data
                               '.jpg':'p' , # still image photo
                               '.tiff':'p',
                               '.bmp':'p',
                               '.arf':'r', # still image raw
                               '.dng':'r',
                               '.mov':'v', # video
                               '.mp4':'v'}
        self.DirButtons = []
        self.initUI()

    def initUI(self):
        print("launch")
        addButton = QPushButton("Add Directories...")
        self.directoriesFound = QLabel("0 directories")
        searchButton = QPushButton("Search Files...")
        self.filesFound = QLabel("0 files")
        self.outputText = QLabel("")
        self.outputScroll = QScrollArea()
        self.outputScroll.setFixedHeight(100)
        self.outputScroll.setWidgetResizable(True)
        self.outputScroll.setWidget(self.outputText)
        self.selectedDirectories = QLabel("Click to remove search directories")
        analyzeButton = QPushButton("Analyze")

        self.paintWidget = PaintWidget()
        
        h_box = QHBoxLayout()
        #h_box.addStretch()
        h_box.addWidget(addButton)
        h_box.addWidget(self.directoriesFound)
        h_box.addStretch()
        h_box.addWidget(searchButton)
        h_box.addWidget(self.filesFound)
        h_box.addWidget(analyzeButton)
        h_box.addStretch()
        v_box = QVBoxLayout()
        v_box.addLayout(h_box)
        v_box.addWidget(self.selectedDirectories)
        h2_box = QHBoxLayout()
        v_box.addLayout(h2_box)
        self.listDirButtonsBox = QVBoxLayout()
        h2_box.addLayout(self.listDirButtonsBox)
        h2_box.addStretch()
        h2_box.addStretch()
        v_box.addWidget(self.outputScroll)
        v_box.addWidget(self.paintWidget)
        v_box.addStretch()
        v_box.addStretch()
        self.setLayout(v_box)
        
        addButton.clicked.connect(self.addButtonClicked)
        searchButton.clicked.connect(self.searchButtonClicked)
        analyzeButton.clicked.connect(self.analyzeButtonClicked)

        self.paintWidget.update()

        self.show()

    def addButtonClicked(self):
        # get the directory
        file = str(QFileDialog.getExistingDirectory(self, "Add Directory..."))
        state = self.DictSearchDirectories.get(file, 0)
        if (state == 0):
            self.DictSearchDirectories[file] = 1
            self.directoriesFound.setText(str(len(self.DictSearchDirectories)) + " directories")
            # visually add the directory, button used so removal easy
            b = QPushButton(file)
            self.DirButtons.append(b);
            b.clicked.connect(self.removeDirButton)
            self.listDirButtonsBox.addWidget(b)
        else:
            print("Directory already in the list")

    def removeDirButton(self):
        # get the reference and remove. but is it still in my list?
        b = self.sender()
        del self.DictSearchDirectories[b.text()]
        self.listDirButtonsBox.removeWidget(b)
        b.deleteLater()
        b = None
        # update visual counter
        self.directoriesFound.setText(str(len(self.DictSearchDirectories)) + " directories")
        self.outputText.setText("")

    def searchButtonClicked(self):
        self.FileCounter = 0
        #print (self.DictSearchDirectories.keys())
        for theDir in self.DictSearchDirectories.keys():
            file_paths = get_filepaths(theDir, self.DictExtensions)
            #print (file_paths)
            self.DictFiles[theDir] = file_paths
            self.FileCounter += len(file_paths)
            self.filesFound.setText(str(self.FileCounter) + " files")
        self.filesFound.setText(str(self.FileCounter) + " files")

    def analyzeButtonClicked(self):
        self.analyzeFiles()

    def analyzeFiles(self):
        view = {}  # traverse and tag, so we can visualize
        sizes = {} # as we traverse hash by size
        names = {} # as we traverse hash by name

        countOfItems = 0
        candidates = {}
        doppleganger = {}
        for dirList in self.DictFiles.keys():
            #print(dirList)
            for file in self.DictFiles.get(dirList):
                MediaDB.AddFileToDB(file)
                #print(file)
                (path,name) = os.path.split(file)
                if (names.get(name, 0) == 0):
                     names[name] = [] # start the dictionary
                     view[file] = 0;
                else:
                     # duplicate name found!  remember it
                     candidates[file] = 'name'
                     doppleganger[file] = names[name]
                     view[file] = 1
                     countOfItems += 1
                names[name].append(file)

                fsize = os.path.getsize(file)
                if (sizes.get(fsize, 0) == 0):
                     #print("start " + str(fsize) + " " + file)
                     sizes[fsize] = [] # start the dictionary
                else:
                    # duplicate size found see if already
                    # in the candidate list
                    if (candidates.get(file, 0) == 0):
                        candidates[file] = 'size'
                        view[file] += 1
                    else:
                        # both duplicate size and name
                        candidates[file] = 'name|size'
                        mtime = os.path.getmtime(file)
                        fn = sizes[fsize][0]
                        mtime2 = os.path.getmtime(fn)
                        if (mtime == mtime2):
                            candidates[file] = 'name|size|date'
                            view[file] += 1
                    doppleganger[file] = sizes[fsize]
                    countOfItems += 1
                sizes[fsize].append(file)

        outstring = ""
        for dupesKey in candidates.keys():
            outstring += "File: "
            outstring += dupesKey
            outstring += " matched "
            outstring += candidates[dupesKey]
            outstring += "\n"
            for fname in doppleganger[dupesKey]:
                outstring += "\t" + fname + "\n"
            outstring += "\n"
        if (countOfItems == 0):
            outstring = "No files matching"
        print(outstring)
        self.outputText.setText(outstring)
        self.paintWidget.setTree(view)
        self.paintWidget.repaint()
            
        MediaDB.UpdateDB()
        MediaDB.CreateRecommendedTree()


    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        return fileName

    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        #options |= QFileDialog.ShowDirsOnly
        files, _ = QFileDialog.getSaveFileNames(self,"Directories", "","All Files (*)", options=options)
        return files

def get_filepaths(directory, theDict):
    file_paths = []  # List which will store all of the full filepaths.
    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
            the_name, the_extension = os.path.splitext(filename)
            lc_extension = the_extension.lower()
            filetype = theDict.get(lc_extension,"0")
            #print("found: " + the_name + " " + the_extension + " " + filetype)
            if filetype != "0":
                # Join the two strings in order to form the full filepath.
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)  # Add it to the list.
    return file_paths  # Self-explanatory.

class PhotoCleanupApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.form_widget = MainWidget()
        self.setCentralWidget(self.form_widget)
        self.init_ui()
        
    def init_ui(self):
        self.title = 'Photo Library Cleanup'
        self.left = 10
        self.top = 100
        self.width = 500
        self.height = 700
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        editMenu = mainMenu.addMenu('Options')
        helpMenu = mainMenu.addMenu('Help')
        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        # Set window background color
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MediaDB.InitDB(0) # -- initialize the MediaDB
    mainwindow = PhotoCleanupApp()
    #MediaDB.CleanupDB() # -- cleanup the MediaDB - in case we later support restarting the context
    sys.exit(app.exec_())
