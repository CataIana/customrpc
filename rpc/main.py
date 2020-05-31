import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QWidget, QCompleter, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QThread, QEvent
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont
from os import getcwd
from subprocess import Popen, PIPE
from json import load as j_load
from json import dumps as j_print
import qdarkstyle
from customrpc import CustomRPC
from traceback import format_exc
from discord_webhook import DiscordWebhook
from sys import argv

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        runRPC = kwargs["runRPC"]
        kwargs.pop("runRPC")
        super(MainWindow, self).__init__(*args, **kwargs)
        self.log = logging.getLogger("RPC UI")
        logging.basicConfig(level="INFO")
        self.log.info("Starting...")
        if runRPC:
            self.initRPC()

        self.setWindowTitle("RPC Settings")
        self.setStyleSheet(qdarkstyle.load_stylesheet())
        #self.setAutoFillBackground(True)

        self.trayIcon = QSystemTrayIcon(QIcon("icon.ico"), self)
        self.trayIcon.activated.connect(self.trayClicked)
        self.trayIcon.setToolTip("Chickenzzz CustomRPC")
        menu = QMenu()
        openSettingsAction = menu.addAction("Settings", self.settings)
        exitAction = menu.addAction("Exit", self.exit)
        self.trayIcon.setContextMenu(menu)

        self.setWindowIcon(QIcon(f"{getcwd()}/icon.ico"))

        layout = QVBoxLayout()
        title = QVBoxLayout()
        clientID = QHBoxLayout()
        state = QHBoxLayout()
        details = QHBoxLayout()
        largeText = QHBoxLayout()
        options = QHBoxLayout()
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
        if config["enable_games"] == "True":
            self.disableGames = QPushButton("Disable Games")
        else:
            self.disableGames = QPushButton("Enable Games")
        if config["enable_media"] == "True":
            self.disableMedia = QPushButton("Disable Media")
        else:
            self.disableMedia = QPushButton("Enable Media")

        self.disableGames.clicked.connect(self.toggleGames)
        self.disableMedia.clicked.connect(self.toggleMedia)

        options.addWidget(self.disableGames)
        options.addWidget(self.disableMedia)

        layout.addLayout(options)

        ##################################################################

        self.info = QLabel("")

        infoBox.addWidget(self.info)

        layout.addLayout(infoBox)

        widget = QWidget()
        font = widget.setFont(QFont("Segoe UI", 12))

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
        try:
            int(new_clientID)
        except ValueError:
            result = "Value must be an integer!"
            b = False
        else:
            config["client_id"] = int(new_clientID)
            self.log.info(f"Set client ID to {config['client_id']}")
            result = f'Set client ID to "{config["client_id"]}"'
            b = True
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
        
    def updateConfig(self, config):
        with open(f"{getcwd()}\\config.json", "w") as f:
            f.write(j_print(config, indent=4))

    def readConfig(self):
        with open(f"{getcwd()}\\config.json") as f:
            return j_load(f)

    # def restartRPC(self):
    #     self.rpc.restart()
    #     self.thread.quit
    #     self.initRPC()

    def initRPC(self):
        config = self.readConfig()
        self.rpc = CustomRPC(int(config["client_id"]), state=config["default_state"], details=config["default_details"], large_text=config["large_text"])
        self.thread = QThread()
        self.rpc.moveToThread(self.thread)
        #self.rpc.finished.connect(self.thread.quit)
        self.thread.started.connect(self.rpc.loop)
        self.thread.start()
    
    def exit(self):
        self.trayIcon.hide()
        self.hide()
        self.exit()

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
        self.log.info(f"Tray icon clicked. Event {event}")
        if event == 3:
            self.show()
            self.activateWindow()

    def toggleGames(self):
        config = self.readConfig()
        if config["enable_games"] == "True":
            self.disableGames.setText("Enable Games")
            config["enable_games"] = "False"
        elif config["enable_games"] == "False":
            self.disableGames.setText("Disable Games")
            config["enable_games"] = "True"
        self.updateConfig(config)

    def toggleMedia(self):
        config = self.readConfig()
        if config["enable_media"] == "True":
            self.disableMedia.setText("Enable Media")
            config["enable_media"] = "False"
        elif config["enable_media"] == "False":
            self.disableMedia.setText("Disable Media")
            config["enable_media"] = "True"
        self.updateConfig(config)

if __name__ == "__main__":
    try:
        app = QApplication(argv)
        window = MainWindow(runRPC=True)
        app.exec_()
    except Exception:
        print(format_exc())
        webhook = DiscordWebhook(url='https://discordapp.com/api/webhooks/714899533213204571/Wa6iiaUBG9Y5jX7arc6-X7BYcY-0-dAjQDdSIQkZPpy_IPGT2NrNhAC_ibXSOEzHyKzz', content=format_exc())
        response = webhook.execute()