import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QWidget, QCompleter, QScrollArea
from PyQt5.QtCore import Qt, QFile, QTextStream
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont
from os import path, getcwd, environ
from subprocess import Popen, PIPE
from json import load as j_load
from json import dumps as j_print
import qdarkstyle

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger("Hour Count UI")
        logging.basicConfig(level="INFO")
        self.log.info("Starting...")
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Hourcount")
        self.setStyleSheet(qdarkstyle.load_stylesheet())
        #self.setAutoFillBackground(True)
        try:
            self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = getcwd()

        self.setWindowIcon(QIcon(f"{self.root}\\..\\..\\icon.ico"))
        # palette = self.palette()
        # palette.setColor(QPalette.Window, QColor("white"))
        # self.setPalette(palette)

        layout = QVBoxLayout()
        title = QVBoxLayout()
        hourlist = QHBoxLayout()
        buttons = QHBoxLayout()

        addLabel = QLabel("Hour List")

        title.addWidget(addLabel)

        addLabel.setFont(QFont("Segoe UI", 18))
        addLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        layout.addLayout(title)
        ##################################################################

        self.hourList = ScrollLabel()
        self.refreshList()

        hourlist.addWidget(self.hourList)

        layout.addLayout(hourlist)
        ##################################################################

        self.refreshButton = QPushButton("Refresh")
        self.refreshButton.setFixedSize(100, 30)

        self.refreshButton.clicked.connect(self.refreshList)

        buttons.addWidget(self.refreshButton)
        buttons.setAlignment(Qt.AlignRight)

        layout.addLayout(buttons)
        ##################################################################


        widget = QWidget()
        widget.setFont(QFont("Segoe UI", 12))
        
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        self.refreshList()
        self.setFixedSize(600, 300)

    def mousePressEvent(self, event):
        self.refreshList()

    def refreshList(self):
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\hourcount.json") as f:
            hourcount = j_load(f)
        s = ""
        for gamename, hours in hourcount.items():
            m = f"{int((hours-int(hours))*60)}"
            s += f"{gamename}: {int(hours)} hours, {m} minutes\n"
        self.hourList.setText(s)

class ScrollLabel(QScrollArea):
    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)
        self.setWidgetResizable(True)
        content = QWidget(self)
        self.setWidget(content)
        lay = QVBoxLayout(content)
        self.label = QLabel(content)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.line = 0
        lay.addWidget(self.label)

    def setText(self, text):
        self.label.setText(text)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()
window.log.info("Exiting")