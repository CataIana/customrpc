from PyQt5.QtWidgets import (
    QApplication, QMainWindow) #Main imports
from PyQt5.QtGui import QFont #Other main imports and stuff
import ctypes #Used for a simple dialog box if script is already running

from os import path, getpid, environ # For various file interactions
from subprocess import Popen, PIPE  #Terminal commands and stuff

import sys

class MainWindow(QMainWindow):
    from imports.rpc import CustomRPC
    from imports._ui import VLCPasswordWindow
    from imports._ui import toggleGames, toggleMedia, toggleTime
    from imports._ui import initUI
    from imports._ui import updateClientID, updateDefaultOptions, updateState, updateDetails, updateLargeText
    from imports._ui import updateConfig, readConfig 
    from imports._ui import closeEvent, changeEvent, trayClicked, showLogFile, settings, exit
    from imports._shared_imports import getLogger, customExceptHook

    def __init__(self, *args, **kwargs):
        self.runRPC = kwargs.get("runRPC", True)
        kwargs.pop("runRPC")
        self.stderr_webhook = kwargs.get("errorsToWebhook", True)
        kwargs.pop("errorsToWebhook")
        super(MainWindow, self).__init__(*args, **kwargs) #Inherit MainWindow properties from PyQt5 beacuse inheritance cool and useful and neat
        try:
            self.root = path.dirname(path.realpath(__file__)) #If running from py file get its folder
        except NameError: #Isn't available when running from exe, so just used getcwd. Bad, but idk what else I can do.
            self.root = path.dirname(sys.argv[0]) #UPDATE we can use sys.argv[0] when running as exe

        self.log = self.getLogger("DEBUG") #Use library to create logger with all formatting with files and stuff

        if __name__ == "__main__":
            sys.excepthook = self.customExceptHook #Create own excepthook that replaces the existing one, but ONLY if running this code directly

        if self.runRPC:
            self.checks() #Don't bother duplicate checking if RPC isn't running

        self.variables() #Define all the variables and stuff that are used

        #Setup the UI
        self.initUI()

        if self.runRPC:
            self.initRPC()
        self.log.debug("Finished init")
        if self.runRPC:
            self.rpc.mainLoop() #Run the mainloop.

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

    def showVLCPwdWindow(self):
        self.log.info("Showing VLC password change dialog box")
        self.VlcPwdWin = self.VLCPasswordWindow(self) #Init vlc password change window
        self.VlcPwdWin.show() #Show it

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
        self.rpc = self.CustomRPC(config["client_id"], logger=self.log) #Initialize rpc script

if __name__ == "__main__":
    app = QApplication(sys.argv) #Create application
    runRPC = True
    if sys.argv.__len__() > 1:
        options = {"False": False, "True": True}
        if sys.argv[1].capitalize() in ["False", "True"]:
            runRPC = options[sys.argv[1].capitalize()]
    window = MainWindow(runRPC=runRPC, errorsToWebhook=False) #Init window
    sys.exit(app.exec_()) #Run process