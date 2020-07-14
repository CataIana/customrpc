from PyQt5.QtWidgets import (
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QWidget, QSystemTrayIcon, QMenu, QComboBox) #Main imports
from PyQt5.QtGui import QIcon #Other main imports and stuff
from PyQt5.QtCore import Qt
import qdarkstyle #Dark theme that looks pretty nice

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