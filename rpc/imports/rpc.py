from pypresence import Presence
from pypresence.exceptions import InvalidID, ServerError
from PyQt5.QtCore import QTimer, QEventLoop

import sys
from os import environ, path
from json import load as j_load


class CustomRPC(Presence):
    from ._shared_imports import getLogger
    from ._shared_imports import customExceptHook
    from ._rpc import variables, getVariables, getDefaults, getWeather, fetchWeather
    from ._rpc import reconnect, updateRPC

    def __init__(self, client_id, **kwargs):
        try:
            self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = path.dirname(sys.argv[0]) 
        if "logger" in kwargs.keys():
            self.log = kwargs["logger"]
            kwargs.pop("logger")
        else:
            self.log = self.getLogger("DEBUG")
        if "fallback" in kwargs.keys():
            self.fallback = kwargs["fallback"]
            kwargs.pop("fallback")
        else:
            self.fallback = False

        super(CustomRPC, self).__init__(client_id)
        self.supported_platforms = ["win32"] #It's for personal use, I don't use linux anymore or macos
        if sys.platform not in self.supported_platforms:
            self.log.critical(f"Unsupported Platform! ({sys.platform})") #Exit if not on windows
            sys.exit()

        if __name__ == "__main__":
            sys.excepthook = self.customExceptHook

        self.variables()
        self.reconnect() #Initalize connection. Own function created to avoid errors if discord isn't open
        try:
            self.updateRPC(self.fallback, False)
        except ServerError:
            self.log.critical("Client ID is invalid!")
            raise TypeError(f"Client ID {self.client_id} is invalid")
        except InvalidID:
            self.updateRPC(self.fallback, False)

    def mainLoop(self):
        while self.isRunning:
            if self.isConnected:
                prev_state, prev_details, prev_large_text, prev_time_left = self.state, self.details, self.large_text, self.time_left #Store previous state/details
                self.getVariables(self.fallback)
                f = True
                while self.state == prev_state and self.details == prev_details and self.large_text == prev_large_text and self.compareTimes(self.time_left, prev_time_left): #If variables haven't changed don't bother sending requests to discord.
                    if f:
                        self.log.info("Waiting for update")
                        f = False
                    self.getVariables(self.fallback) #Check if variables have changed
                    loop = QEventLoop()
                    QTimer.singleShot(2000, loop.quit)
                    loop.exec_() #Avoid wasting cpu time and wait 2 seconds before trying again
                try:
                    self.updateRPC(self.fallback)
                except InvalidID:  #If connection lost to Discord, attempt reconnection
                    self.log.info("Reconnecting...")
                    self.isConnected = False
                    self.close()
                    self.reconnect()
                except ServerError:
                    self.log.critical("Client ID is invalid!")
                    self.close()

    def compareTimes(self, a, b):
        try:
            if abs(a - b) < 3:
                return True
        except TypeError:
            return True
    
    @staticmethod
    def readConfig():
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
            return j_load(f)

    def stop(self):
        self.isRunning = False
        self.clear()
        self.close()
