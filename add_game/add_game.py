import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QWidget, QCompleter
from PyQt5.QtCore import Qt, QFile, QTextStream
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont
from os import path, getcwd, environ
from subprocess import Popen, PIPE
from json import load as j_load
from json import dumps as j_print
import qdarkstyle

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger("RPC Add Game")
        logging.basicConfig(level="INFO")
        self.log.info("Starting...")
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("RPC Add Game")
        self.setStyleSheet(qdarkstyle.load_stylesheet())
        #self.setAutoFillBackground(True)
        try:
            self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = getcwd()

        self.setWindowIcon(QIcon(f"{self.root}\\..\\icon.ico"))
        # palette = self.palette()
        # palette.setColor(QPalette.Window, QColor("white"))
        # self.setPalette(palette)

        layout = QVBoxLayout()
        title = QVBoxLayout()
        selection = QHBoxLayout()
        name = QHBoxLayout()
        buttons = QHBoxLayout()

        addLabel = QLabel("Add Game")

        title.addWidget(addLabel)

        addLabel.setFont(QFont("Segoe UI", 18))
        addLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        layout.addLayout(title)
        ##################################################################


        selectLabel = QLabel("Select Program :")
        self.programList = QComboBox()

        selection.addWidget(selectLabel)
        selection.addWidget(self.programList)

        self.programList.activated.connect(self.checkExists)
        #self.programList.setCompleter(MyCompleter())
        
        layout.addLayout(selection)
        ##################################################################


        realNameLabel = QLabel("Realname: ")
        self.realNameInput = QLineEdit()

        name.addWidget(realNameLabel)       
        name.addWidget(self.realNameInput)

        layout.addLayout(name)
        ##################################################################

        self.addProgramButton = QPushButton("Add Game")
        showGamelist = QPushButton("Open Game List")

        self.addProgramButton.clicked.connect(self.addGame)
        showGamelist.clicked.connect(self.showGameList)

        buttons.addWidget(self.addProgramButton)
        buttons.addWidget(showGamelist)

        layout.addLayout(buttons)
        ##################################################################

        self.infoLabel = QLabel("")
        layout.addWidget(self.infoLabel)

        widget = QWidget()
        widget.setFont(QFont("Segoe UI", 12))
        
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        self.refreshList()
        self.addProgramButton.setEnabled(False)
        self.setFixedSize(350, 175)

    def mousePressEvent(self, event):
        self.refreshList()

    def refreshList(self):
        self.log.info("Refreshing program list")
        exclusions = ["svchost.exe"]
        programlist = [""]

        proc = Popen('WMIC PROCESS get Caption', shell=True, stdout=PIPE)
        for line in proc.stdout:
            a = line.decode().rstrip()
            if len(a) > 0:
                if a not in exclusions:
                    programlist.append(a)
        programlist = list(dict.fromkeys(programlist))
        self.programList.addItems(sorted(programlist, key=str.casefold))

    def checkExists(self, index):
        self.log.info("Checking exists")
        if index == 0:
            self.addProgramButton.setEnabled(False)
            self.infoLabel.setText("")
            self.log.info("Blank selected. Disabling button")
        else:
            self.chosen = self.programList.itemText(index)
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json") as ga:
                gamelist = j_load(ga)
            if self.chosen in list(gamelist.keys()):
                self.infoLabel.setText("Executable already defined!")
                self.addProgramButton.setEnabled(False)
                self.log.info("Already defined game selected. Disabling button")
            else:
                self.addProgramButton.setEnabled(True)
                self.infoLabel.setText("")
                self.log.info("Undefined game selected. Enabling button")

    def addGame(self):
        self.log.info("Adding game")
        realname = self.realNameInput.text()
        if self.chosen != "" and realname != "":
            self.infoLabel.setText(f"Adding {self.chosen}...")
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json") as ga:
                gamelist = j_load(ga)
            gamelist[self.chosen] = realname
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json", "w") as gw:
                gw.write(j_print(gamelist, indent=4))
            self.infoLabel.setText("Done!")
            self.log.info(f"Successfully added {self.chosen} to game list under {realname}")
        else:
            self.infoLabel.setText("Fill out all boxes!")
            self.log.info("Realname box empty")
    
    def showGameList(self):
        self.log.info("Showing game list")
        folder = f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json"
        Popen(f"start {folder}", shell=True)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()
window.log.info("Exiting")