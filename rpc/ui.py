from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QSystemTrayIcon, QMenu, QComboBox #Main imports
from PyQt5.QtGui import QIcon, QFont #Other main imports and stuff
from PyQt5.QtCore import Qt, QEvent
import qdarkstyle #Dark theme that looks pretty nice
import ctypes #Used for a simple dialog box if script is already running

from os import path, getcwd, getpid, environ, remove, mkdir #For various file interactions
from subprocess import Popen, PIPE #Terminal commands and stuff

from json import load as j_load #Reading config files
from json import dumps as j_print

import sys
from imports import CustomRPC, getLogger, VLCPasswordWindow, except_info
from traceback import format_exception #My imports hell yeah

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        self.runRPC = kwargs["runRPC"]
        kwargs.pop("runRPC")
        super(MainWindow, self).__init__(*args, **kwargs) #Inherit MainWindow properties from PyQt5 beacuse inheritance cool and useful and neat
        try:
            self.root = path.dirname(path.realpath(__file__)) #If running from py file get its folder
        except NameError: #Isn't available when running from exe, so just used getcwd. Bad, but idk what else I can do
            self.root = getcwd()

        self.log = getLogger("DEBUG") #Use library to create logger with all formatting with files and stuff

        if self.runRPC:
            self.checks() #Don't bother duplicate checking if RPC isn't running

        self.variables() #Define all the variables and stuff that are used
        
        #Setup the UI
        self.initUI()

        if self.runRPC:
            self.initRPC()
        self.log.debug("Finished init")

    def variables(self):
        self.windowTitle = "RPC Settings"
        self.iconDir = f"{self.root}\\..\\icon.ico" #Where to find the icon
        self.toolTip = "CustomRPC" #Tray icon tooltip
        self.font = QFont("Segoe UI", 12) #Set font that everything uses
        self.updateText = "Update"

    def checks(self): #Reads the pid from %USERPROFILE% and if rpc.exe is running with that pid, exit this instance, otherwise overwrite with this instances PID
        if path.isfile(f"{environ['USERPROFILE']}\\rpc.pid"): #Check if pid file exists
            with open(f"{environ['USERPROFILE']}\\rpc.pid") as f:
                pid = f.read() #If so get the pid from it
            proc = Popen(["WMIC", "PROCESS", "get", "Caption", ",", "ProcessID"], shell=True, stdout=PIPE) #Get running processes and process ids associated with them
            for line in proc.stdout: #Iterate through the process list fetched from subprocess
                program = line.decode().rstrip().split() #Clean up the line and split exe name and pid into a list of 2 items
                if len(program) > 0: #If its not a blank line. Prevents index errors
                    if program[1] == pid: #Check if pid matches
                        if program[0] == "rpc.exe": #If pid matches check if exe name matches. If so, exit
                            self.log.critical(f"Already running! ({pid})")
                            ctypes.windll.user32.MessageBoxW(None, "Already Running!", "RPC", 0x10)
                            sys.exit()
        
        with open(f"{environ['USERPROFILE']}\\rpc.pid", "w") as p: #Otherwise overwrite the pid file with this processes pid
            p.write(str(getpid()))
            self.log.debug(f"PID: {getpid()}") #And log the pid because yeet
    
    def initUI(self):
        self.setWindowTitle(self.windowTitle)
        self.setStyleSheet(qdarkstyle.load_stylesheet()) #Load dark theme

        self.trayIcon = QSystemTrayIcon(QIcon(self.iconDir), self) #Setup tray icon
        self.trayIcon.activated.connect(self.trayClicked) #Conenect clicks to function
        self.trayIcon.setToolTip(self.toolTip) #Set the tooltip that shows up when hovering over tray icon

        self.menu = QMenu() #Create a menu
        self.menu.addAction("Settings", self.settings) #Add settings
        self.menu.addAction("Exit", self.exit) #And exit
        self.trayIcon.setContextMenu(self.menu) #Set the tray menu to the defined menu

        self.setWindowIcon(QIcon(self.iconDir)) #Set the window icon to the same as the tray icon.


        #Create all the layouts
        self.mainLayout = QVBoxLayout()
        self.titleLayout = QVBoxLayout()
        self.clientIDLayout = QHBoxLayout()
        self.stateLayout = QHBoxLayout()
        self.detailsLayout = QHBoxLayout()
        self.defaultOptionsLayout = QHBoxLayout()
        self.largeTextLayout = QHBoxLayout()
        self.optionsLayout = QHBoxLayout()
        self.options2Layout = QHBoxLayout()
        self.infoboxLayout = QHBoxLayout()

        config = self.readConfig() #Read config for reading existing settings

        ##################################################################
        #Create the title, matching the window title, and aligning it to centre

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
        self.clientIDInput.returnPressed.connect(self.clientIDButton.click) #Make enter button trigger the update button
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
        self.stateInput.returnPressed.connect(self.stateButton.click) #Make enter button trigger the update button
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
        self.detailsInput.returnPressed.connect(self.detailsButton.click) #Make enter button trigger the update button
        self.detailsButton.clicked.connect(self.updateDetails)

        #Add layout
        self.mainLayout.addLayout(self.detailsLayout)

        ##################################################################

        #Objects
        defaultOptionsLabel = QLabel("Default Options:")
        self.defaultOptionsList = QComboBox()
        self.defaultOptionsButton = QPushButton(self.updateText)

        #Add widgets
        self.defaultOptionsLayout.addWidget(defaultOptionsLabel)
        self.defaultOptionsLayout.addWidget(self.defaultOptionsList)
        self.defaultOptionsLayout.addWidget(self.defaultOptionsButton)

        #Set extra data
        self.defaultOptionsList.addItems(
            [
                "Time",
                "Weather",
                "Use Text",
                "Rotating"
            ]
        )
        index = self.defaultOptionsList.findText(config["default_option"], Qt.MatchFixedString) #Find the index that the config is set to in the combobox list
        self.defaultOptionsList.setCurrentIndex(index) #Then set the combobox to that item in the config file
        self.defaultOptionsButton.clicked.connect(self.updateDefaultOptions)
        self.defaultOptionsButton.adjustSize() #Rescale to fit better

        #Add layout
        self.mainLayout.addLayout(self.defaultOptionsLayout)

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
        self.largeTextInput.returnPressed.connect(self.largeTextButton.click) #Make enter button trigger the update button
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
        self.setFixedSize(400, 320) #Set window dimensions
        self.trayIcon.show() #Show tray icon so we can open the settings/exit

    def updateClientID(self):
        new_clientID = self.clientIDInput.text() #Fetch input text
        config = self.readConfig()
        if new_clientID == "": #Run checks to make sure client id is somewhat valid, I don't know the actual requirements for a valid client id, but these are close enough
            result = "Client ID cannot be empty!" #Set text for info box
            b = False #Don't bother updating config if client id is invalid
        if new_clientID.__len__() != 18:
            result = "Client ID must be 18 digits!" #Set text for info box
            b = False #Don't bother updating config if client id is invalid
        try:
            int(new_clientID)
        except ValueError:
            result = "Value must be an integer!" #Set text for info box
            b = False #Don't bother updating config if client id is invalid
        else:
            config["client_id"] = int(new_clientID) #Update config client id
            result = f'Set client ID. Restart program to apply changes' #Set text for info box
            b = True #Make sure to update config with new client id
        self.log.info(f'Set client ID to "{config["client_id"]}"')
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def updateState(self):
        new_state = self.stateInput.text() #Fetch input text
        config = self.readConfig()
        if new_state.__len__() > 128: #Run checks to make sure state isn't too long or too short
            result = "String too long!"
            b = False #Don't bother updating config if state is invalid
        elif new_state.__len__() < 2:
            result = "String too short!"
            b = False #Don't bother updating config if state is invalid
        else:
            config["default_state"] = new_state #Update config state
            self.log.info(f"Set details to {config['default_state']}") #Set text for info box
            result = f'Set details to "{config["default_state"]}"'
            b = True #Make sure to update config with new state
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def updateDetails(self):
        new_details = self.detailsInput.text() #Fetch input text
        config = self.readConfig()
        if new_details.__len__() > 128: #Run checks to make sure details isn't too long or too short
            result = "String too long!"
            b = False #Don't bother updating config if details is invalid
        elif new_details.__len__() < 2:
            result = "String too short!"
            b = False #Don't bother updating config if details is invalid
        else:
            config["default_details"] = new_details #Update config details
            self.log.info(f"Set details to {config['default_details']}") #Set text for info box
            result = f'Set details to "{config["default_details"]}"'
            b = True #Make sure to update config with new details
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def updateDefaultOptions(self):
        config = self.readConfig()
        config["default_option"] = self.defaultOptionsList.currentText() #Static options, no checks need to be done here. Overwrite and write to file
        self.log.info(f"Set default option to {config['default_option']}")
        self.info.setText(f"Set default option to {config['default_option']}")
        self.updateConfig(config)

    def updateLargeText(self):
        new_large_text = self.largeTextInput.text() #Fetch input text
        config = self.readConfig()
        if new_large_text.__len__() > 128: #Run checks to make sure text isn't too long or too short
            result = "String too long!"
            b = False #Don't bother updating config if text is invalid
        elif new_large_text.__len__() < 2:
            result = "String too short!"
            b = False #Don't bother updating config if text is invalid
        else:
            config["large_text"] = new_large_text #Update config text
            self.log.info(f"Set details to {config['large_text']}") #Set text for info box
            result = f'Set details to "{config["large_text"]}"'
            b = True #Make sure to update config with new text
        self.info.setText(result)
        if b:
            self.updateConfig(config)

    def showLogFile(self):
        self.log.info("Opening log file")
        folder = f"{self.root}\\log.log"
        try:
            Popen(["C:\\Program Files\\Notepad++\\notepad++.exe", folder]) #If notepad++ in path, open with it
        except FileNotFoundError:
            try:
                Popen(["C:\\Program Files (x86)\\Notepad++\\notepad++.exe", folder]) #If notepad++ in path 32bit, open with it
            except FileNotFoundError:
                Popen(["notepad", folder]) #Otherwise open with normal notepad

    def showVLCPwdWindow(self):
        self.log.info("Showing VLC password change dialog box")
        self.VlcPwdWin = VLCPasswordWindow(self) #Init vlc password change window
        self.VlcPwdWin.show() #Show it
        
    def updateConfig(self, config):
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json", "w") as f:
            f.write(j_print(config, indent=4)) #Overwrite config file with config passed

    def readConfig(self):
        try:
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f: #Read  config and return in json format
                return j_load(f)
        except FileNotFoundError:
            self.log.error("Config not found! Generating...") #Generate config with default options if not found
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
                mkdir(f"{environ['LOCALAPPDATA']}\\customrpc") #Create customrpc folder if it doesn't exist
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json", "w") as f:
                f.write(j_print(data, indent=4)) #Write new config file
            self.log.info("Sucessfully created config file.")
            with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
                return j_load(f) #And return it as normal

    def exit(self):
        self.trayIcon.hide() #Remove tray icon
        self.hide() #Hide window if shown
        if self.runRPC:
            remove(f"{environ['USERPROFILE']}\\rpc.pid") #Remove pid file if it was created
        self.log.info("Exiting...")
        sys.exit() #Finally exit

    def settings(self):
        self.show() #Function that activates when settings option in tray menu is clicked, just shows the main window

    def closeEvent(self, event): #Function is triggered when window is closed
        self.log.info("Close event")
        event.ignore() #Ignore close so program may minimize to tray
        self.info.setText("")
        self.hide()
    
    def changeEvent(self, event): #Function is triggered when window is minimized
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized: #Check if window is minimized
                event.ignore() #Ignore beacuse idk?
                self.log.info("Minimize event")
                self.info.setText("") #Clear info box
                self.hide() #Minimize to tray
    
    def trayClicked(self, event): #Function that is triggered when
        self.log.debug(f"Tray icon clicked. Event {event}")
        if event == 3: #Event 3 is a single left click, open when this even occurs
            self.show()
            self.activateWindow() #Not sure what this does, probably a side effect of the program starting minimized or something

    def toggleGames(self):
        config = self.readConfig() #Switch between true and false in config file, do the same for the UI text
        if config["enable_games"] == True:
            self.disableGames.setText("Enable Games")
            config["enable_games"] = False
        elif config["enable_games"] == False:
            self.disableGames.setText("Disable Games")
            config["enable_games"] = True
        self.log.info(f"Toggled games to {config['enable_games']}")
        self.updateConfig(config)

    def toggleMedia(self):
        config = self.readConfig() #Switch between true and false in config file, do the same for the UI text
        if config["enable_media"] == True:
            self.disableMedia.setText("Enable Media")
            config["enable_media"] = False
        elif config["enable_media"] == False:
            self.disableMedia.setText("Disable Media")
            config["enable_media"] = True
        self.log.info(f"Toggled media to {config['enable_media']}")
        self.updateConfig(config)

    def toggleTime(self): #Switch between true and false in config file, do the same for the UI text
        config = self.readConfig()
        if config["use_time_left"] == True:
            self.timeFormat.setText("Use End Time")
            config["use_time_left"] = False
        elif config["use_time_left"] == False:
            self.timeFormat.setText("Use Start Time")
            config["use_time_left"] = True
        self.log.info(f"Toggled time format to {config['use_time_left']}")
        self.updateConfig(config)

    def restartRPC(self): #Trigger the rpc function to stop and reinitialize it
        if self.runRPC:
            self.log.info("Restarting RPC")
            self.rpc.stop()
            self.initRPC()
        else:
            self.log.info("RPC is not enabled! Cannot restart.")
            self.info.setText("RPC is not enabled! Cannot restart.")

    def initRPC(self):
        config = self.readConfig()
        self.rpc = CustomRPC(config["client_id"], logger=self.log) #Initialize rpc script
        self.rpc.mainLoop() #Run the mainloop. Side effect is that the __init__ of this program actually never finishes

    def except_hook(self, exc_type, exc_value, exc_tb):
        enriched_tb = except_info(exc_tb) if exc_tb else exc_tb #Some copy paste magic that catches errors, generates a better traceback and logs it for later debugging
        self.log.info(f"Uncaught exception: {format_exception(exc_type, exc_value, enriched_tb)}")
        from discord_webhook import DiscordWebhook

        webhook = DiscordWebhook(
            url="https://discordapp.com/api/webhooks/714899533213204571/Wa6iiaUBG9Y5jX7arc6-X7BYcY-0-dAjQDdSIQkZPpy_IPGT2NrNhAC_ibXSOEzHyKzz",
            content=format_exception(exc_type, exc_value, enriched_tb))
        webhook.execute()

if __name__ == "__main__":
    app = QApplication(sys.argv) #Create application
    window = MainWindow(runRPC=True) #Init window
    sys.excepthook = window.except_hook #Create own excepthook that replaces the existing one
    sys.exit(app.exec_()) #Run process