import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QThread, QEvent
from PyQt5.QtGui import QIcon, QFont
from os import path, getcwd, getpid, environ, remove, mkdir
from json import load as j_load
from json import dumps as j_print
import qdarkstyle
from subprocess import Popen, PIPE
from customrpc import CustomRPC
from traceback import format_exc
from discord_webhook import DiscordWebhook
from sys import argv
import sys

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        runRPC = kwargs["runRPC"]
        kwargs.pop("runRPC")
        if "clear_log" in kwargs:
            clearLog = kwargs["clear_log"]
            kwargs.pop("clear_log")
        else:
            clearLog = False
        super(MainWindow, self).__init__(*args, **kwargs)
        try:
            self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = getcwd()

        if clearLog:
            with open(f"{self.root}\\log.log", "w"):
                pass
        self.log = logging.getLogger("RPC UI")
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s", "%Y-%m-%d %I:%M:%S %p")
        ch.setFormatter(formatter)
        self.log.addHandler(ch)
        self.log.setLevel(logging.DEBUG)
        fh = logging.FileHandler(f"{self.root}\\log.log")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.log.addHandler(fh)

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
                            import ctypes
                            ctypes.windll.user32.MessageBoxW(None, "Already Running!", "RPC", 0x10)
                            sys.exit()

        with open(f"{environ['USERPROFILE']}\\rpc.pid", "w") as p:
            p.write(str(getpid()))
            self.log.debug(f"PID: {getpid()}")
    
        if runRPC:
            self.initRPC()

        self.setWindowTitle("RPC Settings")
        self.setStyleSheet(qdarkstyle.load_stylesheet())

        self.icondir = f"{self.root}\\..\\icon.ico"

        self.trayIcon = QSystemTrayIcon(QIcon(self.icondir), self)
        self.trayIcon.activated.connect(self.trayClicked)
        self.trayIcon.setToolTip("CustomRPC")
        menu = QMenu()
        menu.addAction("Settings", self.settings)
        menu.addAction("Exit", self.exit)
        self.trayIcon.setContextMenu(menu)

        self.setWindowIcon(QIcon(self.icondir))

        layout = QVBoxLayout()
        title = QVBoxLayout()
        clientID = QHBoxLayout()
        state = QHBoxLayout()
        details = QHBoxLayout()
        largeText = QHBoxLayout()
        options = QHBoxLayout()
        options2 = QHBoxLayout()
        infoBox = QHBoxLayout()

        config = self.readConfig()

        ##################################################################

        titleLabel = QLabel("RPC Settings")

        title.addWidget(titleLabel)

        titleLabel.setFont(QFont("Segoe UI", 14))
        titleLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        layout.addLayout(title)
        ##################################################################3

        clientIDLabel = QLabel("Client ID:")
        self.clientIDInput = QLineEdit(str(config["client_id"]))
        self.clientIDButton = QPushButton("Update")

        self.clientIDButton.clicked.connect(self.updateClientID)

        clientID.addWidget(clientIDLabel)
        clientID.addWidget(self.clientIDInput)
        clientID.addWidget(self.clientIDButton)

        layout.addLayout(clientID)

        ##################################################################

        stateLabel = QLabel("Default State:")
        self.stateInput = QLineEdit(config["default_state"])

        self.stateButton = QPushButton("Update")

        self.stateButton.clicked.connect(self.updateState)

        state.addWidget(stateLabel)
        state.addWidget(self.stateInput)
        state.addWidget(self.stateButton)

        layout.addLayout(state)

        ##################################################################

        detailsLabel = QLabel("Default Details:")
        self.detailsInput = QLineEdit(config["default_details"])
        self.detailsButton = QPushButton("Update")

        self.detailsButton.clicked.connect(self.updateDetails)

        details.addWidget(detailsLabel)
        details.addWidget(self.detailsInput)
        details.addWidget(self.detailsButton)

        layout.addLayout(details)

        ##################################################################

        largeTextLabel = QLabel("Large Text:")
        self.largeTextInput = QLineEdit(config["large_text"])
        self.largeTextButton = QPushButton("Update")

        self.largeTextButton.clicked.connect(self.updateLargeText)

        largeText.addWidget(largeTextLabel)
        largeText.addWidget(self.largeTextInput)
        largeText.addWidget(self.largeTextButton)

        layout.addLayout(largeText)

        ##################################################################
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

        self.disableGames.clicked.connect(self.toggleGames)
        self.disableMedia.clicked.connect(self.toggleMedia)
        self.timeFormat.clicked.connect(self.toggleTime)

        options.addWidget(self.disableGames)
        options.addWidget(self.disableMedia)
        options.addWidget(self.timeFormat)

        layout.addLayout(options)

        ##################################################################

        self.chgVLCPwd = QPushButton("VLC Password")
        ph1 = QPushButton()
        ph2 = QPushButton()

        self.chgVLCPwd.clicked.connect(self.showVLCPwdWindow)

        options2.addWidget(self.chgVLCPwd)
        options2.addWidget(ph1)
        options2.addWidget(ph2)

        layout.addLayout(options2)

        ##################################################################

        self.info = QLabel("")

        infoBox.addWidget(self.info)

        layout.addLayout(infoBox)

        widget = QWidget()
        widget.setFont(QFont("Segoe UI", 12))

        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setFixedSize(400, 280)
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

    def initRPC(self):
        config = self.readConfig()
        try:
            int(config["client_id"])
        except ValueError:
            self.log.critical("Client ID is not a valid integer!")
            return
        try:
            self.rpc = CustomRPC(int(config["client_id"]), state=config["default_state"], details=config["default_details"], large_text=config["large_text"], log=self.log)
        except TypeError:
            pass
        else:
            self.thread = QThread()
            self.rpc.moveToThread(self.thread)
            #self.rpc.finished.connect(self.thread.quit)
            self.thread.started.connect(self.rpc.loop)
            self.thread.start()

    def exit(self):
        self.trayIcon.hide()
        self.hide()
        remove(f"{environ['USERPROFILE']}\\rpc.pid")
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

class VLCPasswordWindow(QMainWindow):
    def __init__(self, parent):
        super(VLCPasswordWindow, self).__init__()
        self.parent = parent

        self.setWindowTitle("Change VLC Password")
        self.setStyleSheet(qdarkstyle.load_stylesheet())

        self.setWindowIcon(QIcon(parent.icondir))

        layout = QVBoxLayout()

        config = self.parent.readConfig()

        ##################################################################

        titleLabel = QLabel("Change VLC Password")
        titleLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.pwdInput = QLineEdit(config["vlc_pwd"])
        self.pwdInput.setEchoMode(QLineEdit.Password)
        self.pwdButton = QPushButton("Change Password")

        self.pwdInput.returnPressed.connect(self.pwdButton.click)
        self.pwdButton.clicked.connect(self.setPassword)

        layout.addWidget(titleLabel)
        layout.addWidget(self.pwdInput)
        layout.addWidget(self.pwdButton)

        widget = QWidget()
        widget.setFont(QFont("Segoe UI", 12))
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setFixedSize(300, 150)

    def setPassword(self):
        new_pwd = self.pwdInput.text()
        config = self.parent.readConfig()
        config["vlc_pwd"] = new_pwd
        self.parent.updateConfig(config)
        self.parent.log.info(f"Set VLC password to {config['vlc_pwd']}")
        self.log.info("Closing VLC password change dialog box")
        self.hide()


if __name__ == "__main__":
    # try:
    #     app = QApplication(argv)
    #     window = MainWindow(runRPC=True)
    #     app.exec_()
    # except Exception:
    #     print(format_exc())
    #     webhook = DiscordWebhook(url='https://discordapp.com/api/webhooks/714899533213204571/Wa6iiaUBG9Y5jX7arc6-X7BYcY-0-dAjQDdSIQkZPpy_IPGT2NrNhAC_ibXSOEzHyKzz', content=format_exc())
    #     response = webhook.execute()
    app = QApplication(argv)
    window = MainWindow(runRPC=True, clear_log=False)
    app.exec_()
