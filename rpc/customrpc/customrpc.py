from pypresence import Presence
from pypresence.exceptions import InvalidPipe, InvalidID, ServerError
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from time import sleep, time
from random import choice

from sys import platform, stdout
import sys
from os import environ, path, getcwd
from subprocess import Popen, PIPE
from json import load as j_load
from json import dumps as j_print

from requests import Session
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

import logging

from traceback import format_exception
from collections import namedtuple
from discord_webhook import DiscordWebhook

class bcolors: #Copy paste garbage to colour text in terminal
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
#After doing various OOP programming with friends I decided to move this program to oop. Don't expect it to be great
class CustomRPC(QObject):
    finished = pyqtSignal()
    intReady = pyqtSignal(int)
    def __init__(self, client_id, **kwargs):
        if "log" in kwargs:
            self.log = kwargs["log"]
        else:
            self.log = logging.getLogger("CustomRPC")
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s %(levelname)s [%(module)s %(funcName)s %(lineno)d]: %(message)s", "%Y-%m-%d %I:%M:%S %p")
            ch.setFormatter(formatter)
            self.log.addHandler(ch)
            self.log.setLevel(logging.DEBUG)

        super(CustomRPC, self).__init__()
        self.supported_platforms = ["win32"] #It's for personal use, I don't use linux anymore or macos
        if platform not in self.supported_platforms:
            #self.log.critical(f"{bcolors.FAIL}{bcolors.BOLD}Unrecognized Platform! ({platform}){bcolors.ENDC}") #Exit if not on windows
            self.log.critical(f"Unrecognized Platform! ({platform})") #Exit if not on windows
            exit()
        
        self.client_id = client_id
        self.RPC = Presence(self.client_id) #Init PyPresence, the magician behind the scenes
        self.time_left = None
        self.exclusions = ["svchost.exe"] #Clean up program list. Kinda uncessary but probably saves ram.
        self.image_list = ["kitty", "chicken", "chickies", "chub",  "kitty2", "kitty3", "kitty4", "sleepy", "kitty5", "kitty6", "kitty7"] #The images available to the script
        self.music_file = f"{environ['USERPROFILE']}/Documents/Rainmeter/Skins/Chickenzzz Music Status/@Resources/music.txt" #Where to find the music.txt that rainmeter outputs

        try:
           self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = getcwd()

        self.rSession = Session()

        self.lastUpdateTime = 0

        #self.log.info(f"{bcolors.WARNING}Connecting...{bcolors.ENDC}")
        self.log.info("Connecting...")
        self.reconnect() #Initalize connection. Own function created to avoid errors if discord isn't open
        try:
            self.updateRPC(False)
        except ServerError:
            self.log.critical("Client ID is invalid!")
            raise TypeError(f"Client ID {self.client_id} is invalid")
        except InvalidID:
            self.updateRPC(False)
        #self.intReady.emit(1)

    def reconnect(self):
        while True:
            try:
                self.RPC.connect()
            except InvalidPipe:
                #self.log.error(f"{bcolors.FAIL}Cannot connect to discord! Is discord open? (Invalid Pipe){bcolors.ENDC}")
                self.log.error("Cannot connect to discord! Is discord open? (Invalid Pipe)")
            except ConnectionRefusedError:
                #self.log.error(f"{bcolors.FAIL}Cannot connect to discord! Is discord open? (Connection Refused){bcolors.ENDC}")
                self.log.error("Cannot connect to discord! Is discord open? (Connection Refused)")
            except FileNotFoundError:
                #self.log.error(f"{bcolors.FAIL}Cannot connect to discord! Is discord open? (File Not Found){bcolors.ENDC}")
                self.log.error("Cannot connect to discord! Is discord open? (File Not Found)")
            except InvalidID:
                self.log.critical("This fixes the error, but this is never logged. I'm totally lost")
            else:
                #self.log.info(f"{bcolors.OKGREEN}Connected.{bcolors.ENDC}")
                self.log.info("Connected.")
                break
            sleep(5)

    def updateRPC(self, wait=True): #Not sure why this didn't happen sooner, but set the details straight away, rather than waiting for a change.
        self.getVariables()
        config = self.readConfig()
        if (self.lastUpdateTime + 15) > time() and self.lastUpdateTime != 0: #This is a workaround for at the start of the code execution. Because the __init__ of this needs to finish,
            initSleep = (self.lastUpdateTime + 15) - time() #before the UI part will start working we must skip the sleep, otherwise the program will not progress until that sleep completes. This is the use of the wait variable at the bottom of this function
            self.log.debug(f"Init sleeping for {initSleep}") #This loop is then put into action immediately after without waiting, which is an issue, as the RPC is set after about 2 seconds, which discord will accept, but it should only be set every 15 seconds
            sleep(initSleep) #This prevents that and should only run at the very start, or somehow the sleep(15) at the bottom of this function gets cut short. It will be logged for now to ensure this is the case
            self.getVariables() #Since it generally sleeps for about 14 seconds, get the variables again, just to be sure

        if config["use_time_left"]:
            output = self.RPC.update(
                state=self.state,
                details=self.details,
                end=self.time_left,
                large_image=choice(self.image_list),
                large_text=self.large_text
            ) #Set status and store for terminal output
        else:
            output = self.RPC.update(
                state=self.state,
                details=self.details,
                start=self.time_left,
                large_image=choice(self.image_list),
                large_text=self.large_text
            ) #Set status and store for terminal output
        self.lastUpdateTime = time()
        timestamps = ""
        for x, y in output["data"]["timestamps"].items():
            timestamps += f"{x}: {y}, ".strip(", ")
        #self.log.info(f"{output['cmd']} State: {bcolors.OKGREEN}{output['data']['state']}{bcolors.ENDC} Details: {bcolors.OKGREEN}{output['data']['details']}{bcolors.ENDC}  Timestamps: {bcolors.OKGREEN}{timestamps}{bcolors.ENDC}")
        self.log.info(f"{output['cmd']} State: {output['data']['state']} Details: {output['data']['details']}  Timestamps: {timestamps}")
        if wait == True:
            sleep(15)

    @pyqtSlot()
    def loop(self):
        while True:
            prev_state, prev_details, prev_large_text, prev_time_left = self.state, self.details, self.large_text, self.time_left #Store previous state/details
            self.getVariables() #Get variables
            f = True
            while self.state == prev_state and self.details == prev_details and self.large_text == prev_large_text and self.compareTimes(self.time_left, prev_time_left): #If variables haven't changed don't bother sending requests to discord.
                if f:
                    self.log.info("Waiting for update")
                    f = False
                self.getVariables() #Check if variables have changed
                try:
                    if __name__ == "__main__":
                        stdout.write('\x1b[2K')
                except AttributeError:
                    pass
                sleep(2) #Avoid wasting cpu time and wait 2 seconds before trying again
            try:
                stdout.write('\x1b[2K') #Clear terminal line if applicable
            except AttributeError: #Except required if not running via a terminal
                pass
            try:
                self.updateRPC()
            except InvalidID:  #If connection lost to Discord, attempt reconnection
                #self.log.info(f"{bcolors.WARNING}Reconnecting...{bcolors.ENDC}")
                self.log.info("Reconnecting...")
                self.RPC.close()
                sleep(2)
                self.reconnect()
            except ServerError:
                self.log.critical("Client ID is invalid!")
                self.RPC.close()

    def getVariables(self):
        config = self.readConfig()
        if config["enable_media"] == True:
            with open(self.music_file) as f:
                music_read = f.read().splitlines() #Read music file
            try:
                if music_read[1] == "1": #The second line has a 1 in it if music is playing, 0 if paused, and 3 if stopped. Rainmeter/Luas/Webnowplayings choice I dont pick
                    self.state = music_read[0] #Set details to currently playing song
                    duration_read = music_read[3].split(":")[::-1] #Read time into list with each item being hour/minute/second
                    position_read = music_read[2].split(":")[::-1]
                    duration = 0
                    position = 0
                    for i in range(len(duration_read)-1, -1, -1): #Smart loop to convert times from hour/minutes to seconds. Fully expandable, so works with any lengths
                        duration += int(duration_read[i])*(60**i)
                    for i in range(len(position_read)-1, -1, -1):
                        position += int(position_read[i])*(60**i)
                    #Calculate the difference between the 2 times and set time left to how long that is plus the current time
                    if config["use_time_left"] == True:
                        self.time_left = time() + (duration - position)
                    else:
                        self.time_left = int(time() - position)
                else:
                    self.state = config["default_state"] #If music is not playing let details be the default setting
                    self.time_left = None
            except IndexError: #Rainmeter rewrites to the music.txt file multiple times per second, and python may catch the text file with nothing in it.
                pass #Prevents errors that may occur every few hours. Holy shit this took a long time to diagnose
        else:
            self.state = config["default_state"] #If user disabled showing media, let state be default
            self.time_left = None #When setting state, always set time_left

        if config["enable_games"] == True or config["enable_media"] == True:
            programlist = {} #Program list is required for vlc detection, and it also required for game detection
            proc = Popen(["WMIC", "PROCESS", "get", "Caption", ",", "ProcessID"], shell=True, stdout=PIPE) #Get running processes and process ids associated with them
            for line in proc.stdout:
                program = line.decode().rstrip().split()#Clean up line
                if len(program) > 0: #If line isn't blank
                    if program[0] not in self.exclusions: #If process isn't in exclusions list
                        programlist[program[0]] = program[1] #Add process and process id to dictionary

        if config["enable_games"] == True:
            self.details = config["default_details"] #Below code doesn't change anything if no process in gamelist is running. Wasn't an issue when not using OOP. Simplest fix, rather than making a boolean or similar
            with open(f"{self.root}\\..\\..\\data\\gamelist.json") as g:
                gamelist = j_load(g) #Read the json gamelist into the json library
            for exe, realname in gamelist.items(): #Iterate through the gamelist and find a matching process that is running
                if exe in list(programlist.keys()): #Checks through programlist's keys
                    timeactive = []
                    while timeactive.__len__() < 1:
                        proc = Popen(["powershell", f"New-TimeSpan -Start (get-process -id {programlist[exe]}).StartTime"], shell=True, stdout=PIPE) #If found, find how long that process has been running for
                        for line in proc.stdout:
                            timeactive.append(line.decode().rstrip().replace(" ", ""))
                    timeactive_listed = list(filter(None, timeactive)) #Forget what this does, looks important
                    if timeactive_listed[0] != "Days:0": #Some programs do not record how long they have been running for. Catch this and just say the game name
                        self.details = f"Playing {realname}"
                    else: #Otherwise...
                        d = {}
                        for line in timeactive_listed:
                            try:
                                d[line.split(":")[0]] = line.split(":")[1] #Convert the powershell output into a dictionary, due to its dict-like output
                            except IndexError:
                                self.large_text = config["large_text"]
                                return
                        if d["Hours"] == "0": #Don't bother displaying hours if its 0
                            if d["Minutes"] == "0": #For better looks, hide time for the first minute the process has been running for
                                self.details = f"Playing {realname}" 
                                break
                            else: #Show just the minutes
                                self.details = f"Playing {realname} for {d['Minutes']}m"
                                break
                        else: #Otherwise display hours and minutes
                            self.details = f"Playing {realname} for {d['Hours']}h:{d['Minutes']}m"
                            break
        else:
            self.details = config["default_details"]

        if config["enable_media"] == True:
            if "vlc.exe" in programlist.keys(): #Check if vlc is running
                self.rSession.auth = ("", config["vlc_pwd"]) #Login to vlc client. See https://www.howtogeek.com/117261/how-to-activate-vlcs-web-interface-control-vlc-from-a-browser-use-any-smartphone-as-a-remote/
                try:
                    r = self.rSession.get('http://localhost:8080/requests/status.xml', verify=False) #Authenticate the vlc web client
                except ConnectionError:
                    if "ctypes" not in globals():
                        import ctypes
                        ctypes.windll.user32.MessageBoxW(None, "Unable to access VLC web interface!\nHave you activated the web interface?\nHave you allowed VLC through Windows Firewall?", "RPC", 0x10)
                else:
                    soup = BeautifulSoup(r.text, "lxml") #Do the BS4 magic
                    title_error = soup.find("title")
                    if title_error != None:
                        if "ctypes" not in globals():
                            import ctypes
                            ctypes.windll.user32.MessageBoxW(None, "Unable to access VLC web interface!\nDid you set the correct password?", "RPC", 0x10)
                    else:
                        vlcstate = soup.find("state").contents[0] #Locate the state object to get if vlc is playing or not
                        if vlcstate == "playing": #Just like music, don't display if not playing
                            vlctitle = None #Set to none so if statement after for loop doesn't error
                            info = soup.findAll("info") #Finda ll info tags
                            for x in info:
                                if x["name"] == "title": #Find the title tag
                                    vlctitle = x.contents[0] #And set it to the vlc title.
                                    break
                            if vlctitle == None: #For many files, there will be no titles, revert to filename instead, which will always exist
                                for x in info:
                                    if x["name"] == "filename":
                                        vlctitle = x.contents[0]
                                        break
                            self.state = f"Watching {vlctitle[:112]} on VLC"
                            if config["use_time_left"] == True:
                                self.time_left = int(time() + int(soup.find("time").text))
                            else:
                                self.time_left = int(time() - int(soup.find("time").text))
        
        self.details = self.details[:128] #Make sure both variables aren't more than 128 characters long.
        self.state = self.state[:128] #Discord limits to 128 characters. Not my choice
        self.large_text = config["large_text"] #and set the large_text, the only one that is static

    #@pyqtSlot()
    def restart(self):
        self.log.info("Restarting RPC")
        self.RPC.clear()
        self.RPC.close()
        #self.finished.emit()

    def readConfig(self=None):
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
            return j_load(f)

    def compareTimes(self, a, b):
        try:
            if abs(a - b) < 3:
                return True
        except TypeError:
            return True

def generateConfig():
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

def except_hook(exc_type, exc_value, exc_tb):
    enriched_tb = _add_missing_frames(exc_tb) if exc_tb else exc_tb
	# Note: sys.__excepthook__(...) would not work here.
	# We need to use print_exception(...):
    print(''.join(format_exception(exc_type, exc_value, enriched_tb)))
    #window.log.error("Uncaught exception", exc_info=(exc_type, exc_value, enriched_tb))
    webhook = DiscordWebhook(
        url='https://discordapp.com/api/webhooks/714899533213204571/Wa6iiaUBG9Y5jX7arc6-X7BYcY-0-dAjQDdSIQkZPpy_IPGT2NrNhAC_ibXSOEzHyKzz',
        content=f"```python\n{''.join(format_exception(exc_type, exc_value, enriched_tb))}```"
    )
    response = webhook.execute()

def _add_missing_frames(tb):
    result = fake_tb(tb.tb_frame, tb.tb_lasti, tb.tb_lineno, tb.tb_next)
    frame = tb.tb_frame.f_back
    while frame:
        result = fake_tb(frame, frame.f_lasti, frame.f_lineno, result)
        frame = frame.f_back
    return result

fake_tb = namedtuple(
    'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
)
sys.excepthook = except_hook

if __name__ == "__main__":
    with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
        config = j_load(f)

    rpc = CustomRPC(
        int(config["client_id"]),
        state=config["default_state"],
        details=config["default_details"],
        large_text=config["large_text"]
    )
    rpc.loop()
