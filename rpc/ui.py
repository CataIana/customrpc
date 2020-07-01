from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QEvent
import qdarkstyle
import ctypes

from os import path, getcwd, getpid, environ, remove, mkdir
from subprocess import Popen, PIPE

from json import load as j_load
from json import dumps as j_print

import sys
from imports import CustomRPC, getLogger, VLCPasswordWindow, except_info
from traceback import format_exception

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        self.runRPC = kwargs["runRPC"]
        kwargs.pop("runRPC")
        super(MainWindow, self).__init__(*args, **kwargs)
        try:
            self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = getcwd()

        #Create logger
        self.log = getLogger("DEBUG")

        #Run checks before starting
        self.checks()

        #Set variables
        self.variables()
        
        #Setup the UI
        self.initUI()

        if self.runRPC:
            self.initRPC()
        self.log.debug("Finished init")

    def variables(self):
        self.windowTitle = "RPC Settings"
        self.iconDir = f"{self.root}\\..\\icon.ico"
        self.toolTip = "CustomRPC"
        self.font = QFont("Segoe UI", 12)
        self.updateText = "Update"

    def checks(self):
        if path.isfile(f"{environ['USERPROFILE']}\\rpc.pid"):
            with open(f"{environ['USERPROFILE']}\\rpc.pid") as f:
                pid = f.read()
            proc = Popen(["WMIC", "PROCESS", "get", "Caption", ",", "ProcessID"], shell=True, stdout=PIPE) #Get running processes and process ids associated with them
            for line in proc.stdout:
                program = line.decode().rstrip().split()
                if len(program) > 0:
                    if program[1] == pid:
                        if program[0] == "rpc.exe":
                            self.log.critical(f"Already running! ({pid})")
                            ctypes.windll.user32.MessageBoxW(None, "Already Running!", "RPC", 0x10)
                            sys.exit()
        
        with open(f"{environ['USERPROFILE']}\\rpc.pid", "w") as p:
            p.write(str(getpid()))
            self.log.debug(f"PID: {getpid()}")
    
    def initUI(self):
        self.setWindowTitle(self.windowTitle)
        self.setStyleSheet(qdarkstyle.load_stylesheet())

        #Set tray icon
        self.trayIcon = QSystemTrayIcon(QIcon(self.iconDir), self)
        self.trayIcon.activated.connect(self.trayClicked)
        self.trayIcon.setToolTip(self.toolTip)

        #Create menu for tray icon
        self.menu = QMenu()
        self.menu.addAction("Settings", self.settings)
        self.menu.addAction("Exit", self.exit)
        self.trayIcon.setContextMenu(self.menu)

        #Set window icon
        self.setWindowIcon(QIcon(self.iconDir))


        #Create all the layouts
        self.mainLayout = QVBoxLayout()
        self.titleLayout = QVBoxLayout()
        self.clientIDLayout = QHBoxLayout()
        self.stateLayout = QHBoxLayout()
        self.detailsLayout = QHBoxLayout()
        self.largeTextLayout = QHBoxLayout()
        self.optionsLayout = QHBoxLayout()
        self.options2Layout = QHBoxLayout()
        self.infoboxLayout = QHBoxLayout()

        config = self.readConfig()

        ##################################################################

        #Objects
        titleLabel = QLabel(self.windowTitle)

        #Add Widgets
        self.titleLayout.addWidget(titleLabel)

        #Set extra data
        titleLabel.setFont(self.font)
        titleLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        #Add layout
        self.mainLayout.addLayout(self.titleLayout)

        ##################################################################

        #Objects
        clientIDLabel = QLabel("Client ID:")
        self.clientIDInput = QLineEdit(str(config["client_id"]))
        self.clientIDButton = QPushButton(self.updateText)
        
        #Add Widgets
        self.clientIDLayout.addWidget(clientIDLabel)
        self.clientIDLayout.addWidget(self.clientIDInput)
        self.clientIDLayout.addWidget(self.clientIDButton)

        #Set extra data
        self.clientIDButton.clicked.connect(self.updateClientID)

        #Add layout
        self.mainLayout.addLayout(self.clientIDLayout)

        ##################################################################

        #Objects
        stateLabel = QLabel("Default State:")
        self.stateInput = QLineEdit(config["default_state"])
        self.stateButton = QPushButton(self.updateText)

        #Add Widgets
        self.stateLayout.addWidget(stateLabel)
        self.stateLayout.addWidget(self.stateInput)
        self.stateLayout.addWidget(self.stateButton)

        #Set extra data
        self.stateButton.clicked.connect(self.updateState)

        #Add layout
        self.mainLayout.addLayout(self.stateLayout)

        ##################################################################

        #Objects
        detailsLabel = QLabel("Default Details:")
        self.detailsInput = QLineEdit(config["default_details"])
        self.detailsButton = QPushButton(self.updateText)

        #Add widgets
        self.detailsLayout.addWidget(detailsLabel)
        self.detailsLayout.addWidget(self.detailsInput)
        self.detailsLayout.addWidget(self.detailsButton)

        #Set extra data
        self.detailsButton.clicked.connect(self.updateDetails)

        #Add layout
        self.mainLayout.addLayout(self.detailsLayout)

        ##################################################################

        #Objects
        largeTextLabel = QLabel("Large Text:")
        self.largeTextInput = QLineEdit(config["large_text"])
        self.largeTextButton = QPushButton(self.updateText)

        #Add widgets
        self.largeTextLayout.addWidget(largeTextLabel)
        self.largeTextLayout.addWidget(self.largeTextInput)
        self.largeTextLayout.addWidget(self.largeTextButton)

        #Set extra data
        self.largeTextButton.clicked.connect(self.updateLargeText)

        #Add layout
        self.mainLayout.addLayout(self.largeTextLayout)

        ##################################################################
        
        #Objects
        if config["enable_games"] == True:
            self.disableGames = QPushButton("Disable Games")
        else:
            self.disableGames = QPushButton("Enable Games")
        if config["enable_media"] == True:
            self.disableMedia = QPushButton("Disable Media")
        else:
            self.disableMedia = QPushButton("Enable Media")
        if config["use_time_left"] == True:
            self.timeFormat = QPushButton("Use Start Time")
        else:
            self.timeFormat = QPushButton("Use End Time")

        #Add widgets
        self.optionsLayout.addWidget(self.disableGames)
        self.optionsLayout.addWidget(self.disableMedia)
        self.optionsLayout.addWidget(self.timeFormat)

        #Set extra data
        self.disableGames.clicked.connect(self.toggleGames)
        self.disableMedia.clicked.connect(self.toggleMedia)
        self.timeFormat.clicked.connect(self.toggleTime)

        #Add layout
        self.mainLayout.addLayout(self.optionsLayout)

        ##################################################################

        #Objects
        self.chgVLCPwd = QPushButton("VLC Password")
        self.viewLog = QPushButton("View Log")
        self.restartButton = QPushButton("Restart RPC")

        #Add widgets
        self.options2Layout.addWidget(self.chgVLCPwd)
        self.options2Layout.addWidget(self.viewLog)
        self.options2Layout.addWidget(self.restartButton)

        #Set extra data
        self.chgVLCPwd.clicked.connect(self.showVLCPwdWindow)
        self.viewLog.clicked.connect(self.showLogFile)
        self.restartButton.clicked.connect(self.restartRPC)

        #Add layout
        self.mainLayout.addLayout(self.options2Layout)

        ##################################################################

        #Objects
        self.info = QLabel("")

        #Add widgets
        self.infoboxLayout.addWidget(self.info)

        #Add layout
        self.mainLayout.addLayout(self.infoboxLayout)

        #Create Qwidget and set layout into widget
        self.mainWidget = QWidget()
        self.mainWidget.setFont(self.font)
        self.mainWidget.setLayout(self.mainLayout)

        self.setCentralWidget(self.mainWidget)
        self.setFixedSize(400, 280) #Set window dimensions
        self.trayIcon.show()

    def updateClientID(self):
        new_clientID = self.clientIDInput.text()
        config = self.readConfig()
        if new_clientID == "":
            result = "Client ID cannot be empty!"
            b = False
        if new_clientID.__len__() != 18:
            result = "Client ID must be 18 digits!"
            b = False
        try:
            int(new_clientID)
        except ValueError:
            result = "Value must be an integer!"
            b = False
        else:
            config["client_id"] = int(new_clientID)
            result = f'Set client ID. Restart program to apply changes'
            b = True
        self.log.info(f'Set client ID to "{config["client_id"]}"')
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def updateState(self):
        new_state = self.stateInput.text()
        config = self.readConfig()
        if new_state.__len__() > 128:
            result = "String too long!"
            b = False
        elif new_state.__len__() < 2:
            result = "String too short!"
            b = False
        else:
            config["default_state"] = new_state
            self.log.info(f"Set details to {config['default_state']}")
            result = f'Set details to "{config["default_state"]}"'
            b = True
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def updateDetails(self):
        new_details = self.detailsInput.text()
        config = self.readConfig()
        if new_details.__len__() > 128:
            result = "String too long!"
            b = False
        elif new_details.__len__() < 2:
            result = "String too short!"
            b = False
        else:
            config["default_details"] = new_details
            self.log.info(f"Set details to {config['default_details']}")
            result = f'Set details to "{config["default_details"]}"'
            b = True
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def updateLargeText(self):
        new_large_text = self.largeTextInput.text()
        config = self.readConfig()
        if new_large_text.__len__() > 128:
            result = "String too long!"
            b = False
        elif new_large_text.__len__() < 2:
            result = "String too short!"
            b = False
        else:
            config["large_text"] = new_large_text
            self.log.info(f"Set details to {config['large_text']}")
            result = f'Set details to "{config["large_text"]}"'
            b = True
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def showLogFile(self):
        self.log.info("Opening log file")
        folder = f"{self.root}\\log.log"
        try:
            Popen(["C:\\Program Files\\Notepad++\\notepad++.exe", folder])
        except FileNotFoundError:
            Popen(["notepad", folder])

    def showVLCPwdWindow(self):
        self.log.info("Showing VLC password change dialog box")
        self.VlcPwdWin = VLCPasswordWindow(self)
        self.VlcPwdWin.show()
        
    def updateConfig(self, config):
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json", "w") as f:
            f.write(j_print(config, indent=4))

    def readConfig(self):
        try:
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
                return j_load(f)
        except FileNotFoundError:
            self.log.error("Config not found! Generating...")
            data = {
                "client_id": "",
                "default_state": "  ",
                "default_details": "  ",
                "large_text": "  ",
                "enable_games": True,
                "enable_media": True,
                "use_time_left": True,
                "vlc_pwd": ""
            }
            if not path.isdir(f"{environ['LOCALAPPDATA']}\\customrpc"):
                mkdir(f"{environ['LOCALAPPDATA']}\\customrpc")
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json", "w") as f:
                f.write(j_print(data, indent=4))
            self.log.info("Sucessfully created config file.")
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
                return j_load(f)

    def exit(self):
        self.trayIcon.hide()
        self.hide()
        remove(f"{environ['USERPROFILE']}\\rpc.pid")
        self.log.info("Exiting...")
        sys.exit()

    def settings(self):
        self.show()

    def closeEvent(self, event):
        self.log.info("Close event")
        event.ignore()
        self.hide()
    
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                event.ignore()
                self.log.info("Minimize event")
                self.hide()
    
    def trayClicked(self, event):
        self.log.debug(f"Tray icon clicked. Event {event}")
        if event == 3:
            self.show()
            self.activateWindow()

    def toggleGames(self):
        config = self.readConfig()
        if config["enable_games"] == True:
            self.disableGames.setText("Enable Games")
            config["enable_games"] = False
        elif config["enable_games"] == False:
            self.disableGames.setText("Disable Games")
            config["enable_games"] = True
        self.log.info(f"Toggled games to {config['enable_games']}")
        self.updateConfig(config)

    def toggleMedia(self):
        config = self.readConfig()
        if config["enable_media"] == True:
            self.disableMedia.setText("Enable Media")
            config["enable_media"] = False
        elif config["enable_media"] == False:
            self.disableMedia.setText("Disable Media")
            config["enable_media"] = True
        self.log.info(f"Toggled media to {config['enable_media']}")
        self.updateConfig(config)

    def toggleTime(self):
        config = self.readConfig()
        if config["use_time_left"] == True:
            self.timeFormat.setText("Use End Time")
            config["use_time_left"] = False
        elif config["use_time_left"] == False:
            self.timeFormat.setText("Use Start Time")
            config["use_time_left"] = True
        self.log.info(f"Toggled time format to {config['use_time_left']}")
        self.updateConfig(config)

    def restartRPC(self):
        self.log.info("Restarting RPC")
        self.rpc.stop()
        self.initRPC()

    def initRPC(self):
        config = self.readConfig()
        self.rpc = CustomRPC(config["client_id"], logger=self.log)
        self.rpc.mainLoop()

    def except_hook(self, exc_type, exc_value, exc_tb):
        enriched_tb = except_info(exc_tb) if exc_tb else exc_tb
        self.log.info(f"Uncaught exception: {format_exception(exc_type, exc_value, enriched_tb)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(runRPC=True)
    sys.excepthook = window.except_hook
    sys.exit(app.exec_())