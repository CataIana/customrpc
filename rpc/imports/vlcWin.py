from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
import qdarkstyle

class VLCPasswordWindow(QMainWindow):
    def __init__(self, parent):
        super(VLCPasswordWindow, self).__init__()
        self.parent = parent

        self.setWindowTitle("Change VLC Password")
        self.setStyleSheet(qdarkstyle.load_stylesheet())

        self.setWindowIcon(QIcon(self.parent.iconDir))

        self.mainLayout = QVBoxLayout()

        config = self.parent.readConfig()

        ##################################################################

        titleLabel = QLabel("Change VLC Password")
        titleLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.pwdInput = QLineEdit(config["vlc_pwd"])
        self.pwdInput.setEchoMode(QLineEdit.Password)
        self.pwdButton = QPushButton("Change Password")

        self.pwdInput.returnPressed.connect(self.pwdButton.click)
        self.pwdButton.clicked.connect(self.setPassword)

        self.mainLayout.addWidget(titleLabel)
        self.mainLayout.addWidget(self.pwdInput)
        self.mainLayout.addWidget(self.pwdButton)

        self.mainWidget = QWidget()
        self.mainWidget.setFont(self.parent.font)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        self.setFixedSize(300, 150)

    def setPassword(self):
        new_pwd = self.pwdInput.text()
        config = self.parent.readConfig()
        config["vlc_pwd"] = new_pwd
        self.parent.updateConfig(config)
        self.parent.log.info(f"Set VLC password to {config['vlc_pwd']}")
        self.parent.log.info("Closing VLC password change dialog box")
        self.hide()