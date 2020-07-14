from PyQt5.QtCore import Qt, QEvent
from os import remove, environ
import sys
from subprocess import Popen

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

def exit(self):
    self.trayIcon.hide() #Remove tray icon
    self.hide() #Hide window if shown
    if self.runRPC:
        remove(f"{environ['USERPROFILE']}\\rpc.pid") #Remove pid file if it was created
    self.log.info("Exiting...")
    sys.exit() #Finally exit

def settings(self):
    self.show() #Function that activates when settings option in tray menu is clicked, just shows the main window

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