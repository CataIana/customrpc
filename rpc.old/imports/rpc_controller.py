from imports._rpc import rpc_management
from imports.rpc import CustomRPC
from imports._rpc.get_variables import fetchProgramList
from os import path, environ, mkdir
from json import load as j_load
from subprocess import Popen, PIPE
from PyQt5.QtCore import QTimer, QEventLoop
from ._rpc.get_variables import fetchProgramList
import sys
from time import sleep


class RPCController():
    from ._shared_imports import getLogger
    from .rpc import CustomRPC

    def __init__(self, **kwargs):
        try:
            self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = path.dirname(sys.argv[0])
        if "logger" in kwargs.keys():
            self.log = kwargs["logger"]
            kwargs.pop("logger")
        else:
            self.log = self.getLogger("DEBUG")
        self.isRunning = True
        self.current_program_name = False
        with open(f"{self.root}\\..\\client_ids.json") as f:
            self.client_ids = j_load(f)

    def controller(self):
        while self.isRunning:
            config = self.readConfig()
            try:
                with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json") as g:
                    # Read the json gamelist into the json library
                    gamelist = j_load(g)
            except FileNotFoundError:
                if not path.isdir(f"{environ['LOCALAPPDATA']}\\customrpc"):
                    mkdir(f"{environ['LOCALAPPDATA']}\\customrpc")
                with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json", "w") as g:
                    g.write("{\n}")
                with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json") as g:
                    # Read the json gamelist into the json library
                    gamelist = j_load(g)
            programlist = fetchProgramList()
            program_matched = False
            for exe, realname in gamelist.items():  # Iterate through the gamelist and find a matching process that is running
                if exe in list(programlist.keys()):  # Checks through programlist's keys
                    if realname in self.client_ids.keys():
                        program_matched = True
                        if self.current_program_name == False:
                            self.current_program_name = realname
                            self.log.info(
                                f"Switched Client ID to {self.current_program_name}")
                            self.rpc = CustomRPC(
                                self.client_ids[realname], logger=self.log)
                        else:
                            if realname != self.current_program_name:
                                self.rpc.stop()
                                self.current_program_name = False
                                # Not sure if important. Not sure if may cause issues.
                                del self.rpc
                                self.current_program_name = realname
                                self.log.info(
                                    f"Switched Client ID to {self.current_program_name}")
                                self.rpc = CustomRPC(
                                    self.client_ids[realname], logger=self.log)

            if not program_matched:
                if not self.current_program_name:
                    self.current_program_name = "Fallback"
                    self.log.info(
                        f"Switched Client ID to {self.current_program_name}")
                    self.rpc = CustomRPC(
                        config["client_id"], logger=self.log, fallback=True)
                else:
                    if "Fallback" != self.current_program_name:
                        self.rpc.stop()
                        self.current_program_name = False
                        # Not sure if important. Not sure if may cause issues.
                        del self.rpc
                        self.current_program_name = "Fallback"
                        self.log.info(
                            f"Switched Client ID to {self.current_program_name}")
                        self.rpc = CustomRPC(
                            config["client_id"], logger=self.log, fallback=True)

            loop = QEventLoop()
            QTimer.singleShot(15000, loop.quit)
            loop.exec_()  # Fancy version of time.sleep(15), for use with PyQt5

    @staticmethod
    def readConfig():
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
            return j_load(f)
