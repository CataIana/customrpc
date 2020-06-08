from pypresence import Presence, InvalidPipe, InvalidID
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from time import sleep, time
from random import choice

from sys import platform, stdout
from os import environ, path, getcwd
from subprocess import Popen, PIPE
from json import load as j_load
from json import dumps as j_print

from requests import Session
from bs4 import BeautifulSoup

from logging import getLogger, basicConfig, FileHandler

from traceback import format_exc
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
        self.log = getLogger("CustomRPC")
        basicConfig(level="DEBUG")
        super(CustomRPC, self).__init__()
        self.supported_platforms = ["win32"] #It's for personal use, I don't use linux anymore or macos
        if platform not in self.supported_platforms:
            self.log.critical(f"{bcolors.FAIL}{bcolors.BOLD}Unrecognized Platform! ({platform}){bcolors.ENDC}") #Exit if not on windows
            exit()
        
        self.log = getLogger(__name__)
        self.client_id = client_id
        self.RPC = Presence(self.client_id) #Init PyPresence, the magician behind the scenes
        self.time_left = None
        self.exclusions = ["svchost.exe"] #Clean up program list. Kinda uncessary but probably saves ram.
        self.image_list = ["kitty", "chicken", "chickies", "chub",  "kitty2", "kitty3", "kitty4", "sleepy", "kitty5", "kitty6", "kitty7"] #The images available to the script
        self.music_file = f"{environ['USERPROFILE']}/Documents/Rainmeter/Skins/Chickenzzz Music Status/@Resources/music.txt" #Where to find the music.txt that rainmeter outputs

        #try:
        #    self.root = icon = path.dirname(path.realpath(__file__))
        #except NameError:
        #
        self.root = getcwd()

        self.log.info(f"{bcolors.WARNING}Connecting...{bcolors.ENDC}")
        #print(f"{bcolors.WARNING}Connecting...{bcolors.ENDC}", end="\r")
        self.reconnect() #Initalize connection. Own function created to avoid errors if discord isn't open
        self.updateRPC(False)
        #self.intReady.emit(1)

    def reconnect(self):
        while True:
            try:
                self.RPC.connect()
            except InvalidPipe:
                pass
            except ConnectionRefusedError:
                self.log.error(f"{bcolors.FAIL}{bcolors.BOLD}Cannot connect to discord! Is discord open?{bcolors.ENDC}")
                #print(f"{bcolors.FAIL}{bcolors.BOLD}Cannot connect to discord! Is discord open?{bcolors.ENDC}", end="\r")
            except FileNotFoundError:
                self.log.error(f"{bcolors.FAIL}{bcolors.BOLD}Cannot connect to discord! Is discord open?{bcolors.ENDC}")
                #print(f"{bcolors.FAIL}{bcolors.BOLD}Cannot connect to discord! Is discord open?{bcolors.ENDC}", end="\r")
            else:
                break
            sleep(5)

    def updateRPC(self, wait=True): #Not sure why this didn't happen sooner, but set the details straight away, rather than waiting for a change.
        self.getVariables()
        output = self.RPC.update(
            state=self.state,
            details=self.details,
            end=self.time_left,
            large_image=choice(self.image_list),
            large_text=self.large_text
        ) #Set status and store for terminal output
        timestamps = ""
        for x, y in output["data"]["timestamps"].items():
            timestamps += f"{x}: {y}, ".strip(", ")
        self.log.info(f"{output['cmd']} State: {bcolors.OKGREEN}{output['data']['state']}{bcolors.ENDC} Details: {bcolors.OKGREEN}{output['data']['details']}{bcolors.ENDC}  Timestamps: {bcolors.OKGREEN}{timestamps}{bcolors.ENDC}")
        #print(f"{output['cmd']} State: {bcolors.OKGREEN}{output['data']['state']}{bcolors.ENDC} Details: {bcolors.OKGREEN}{output['data']['details']}{bcolors.ENDC}  Timestamps: {bcolors.OKGREEN}{timestamps}{bcolors.ENDC}", end="\r")
        if wait == True:
            sleep(15)

    @pyqtSlot()
    def loop(self):
        while __name__ != "__main__":
            try:
                prev_state, prev_details, prev_large_text = self.state, self.details, self.large_text #Store previous state/details
                self.getVariables() #Get variables
                f = True
                while self.state == prev_state and self.details == prev_details and self.large_text == prev_large_text: #If variables haven't changed don't bother sending requests to discord.
                    if f:
                        self.log.info("Waiting for update")
                        f = False
                    self.getVariables() #Check if variables have changed
                    try:
                        if __name__ == "__main__":
                            stdout.write('\x1b[2K')
                    except AttributeError:
                        pass
                    #self.log.info(f"{bcolors.OKGREEN}Waiting for update...{bcolors.ENDC}")
                    #print(f"{bcolors.OKGREEN}Waiting for update...{bcolors.ENDC}", end="\r")
                    sleep(2) #Avoid wasting cpu time and wait 2 seconds before trying again
                try:
                    stdout.write('\x1b[2K') #Clear terminal line if applicable
                except AttributeError: #Except required if not running via a terminal
                    pass
                self.updateRPC()
            except InvalidID: #If connection lost to Discord, attempt reconnection
                self.log.info(f"{bcolors.WARNING}Reconnecting...{bcolors.ENDC}")
                #print(f"{bcolors.WARNING}Reconnecting...{bcolors.ENDC}", end="\r")
                self.reconnect()

    def getVariables(self):
        with open(f"{self.root}\\config.json") as f:
            config = j_load(f)
        if config["enable_media"] == "True":
            with open(self.music_file) as f:
                music_read = f.read().splitlines() #Read music file
            try:
                if music_read[1] == "1": #The second line has a 1 in it if music is playing, 0 if paused, and 3 if stopped. Rainmeter/Luas/Webnowplayings choice I dont pick
                    self.state = music_read[0] #Set details to currently playing song
                    duration = int(music_read[3].split(":")[0]) * 60 + int(music_read[3].split(":")[1])
                    position = int(music_read[2].split(":")[0]) * 60 + int(music_read[2].split(":")[1])
                    self.time_left = time() + (duration - position)
                else:
                    self.state = config["default_state"] #If music is not playing let details be the default setting
                    self.time_left = None
            except IndexError: #Rainmeter rewrites to the music.txt file multiple times per second, and python may catch the text file with nothing in it.
                pass #Prevents errors that may occur every few hours
        else:
            self.state = config["default_state"]
            self.time_left = None

        programlist = {}
        proc = Popen(["WMIC", "PROCESS", "get", "Caption", ",", "ProcessID"], shell=True, stdout=PIPE) #Get running processes and process ids associated with them
        for line in proc.stdout:
            program = line.decode().rstrip().split()#Clean up line
            if len(program) > 0: #If line isn't blank
                if program[0] not in self.exclusions: #If process isn't in exclusions list
                    programlist[program[0]] = program[1] #Add process and process id to dictionary

        if config["enable_games"] == "True":
            self.details = config["default_details"] #Below code doesn't change anything if no process in gamelist is running. Wasn't an issue when not using OOP. Simplest fix, rather than making a boolean or similar
            with open(f"{self.root}\\..\\data\\gamelist.json") as g:
                gamelist = j_load(g) #Read the json gamelist into the json library
            for exe, realname in gamelist.items(): #Iterate through the gamelist and find a matching process that is running
                if exe in list(programlist.keys()): #Checks through programlist's keys
                    proc = Popen(["powershell", f"New-TimeSpan -Start (get-process -id {programlist[exe]}).StartTime"], shell=True, stdout=PIPE) #If found, find how long that process has been running for
                    timeactive = []
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

        if config["enable_media"] == "True":
            if "vlc.exe" in programlist.keys(): #Check if vlc is running
                s = Session() #Create a requests session.
                s.auth = ('', '6254') #Login to vlc client. See https://www.howtogeek.com/117261/how-to-activate-vlcs-web-interface-control-vlc-from-a-browser-use-any-smartphone-as-a-remote/
                r = s.get('http://localhost:8080/requests/status.xml', verify=False) #Authenticate the vlc web client
                soup = BeautifulSoup(r.text, "lxml") #Do the BS4 magic
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
                    self.details = f"Watching {vlctitle} on VLC"
        else:
            self.state = config["default_state"]
        
        self.details = self.details[:128] #Make sure both variables aren't more than 128 characters long.
        self.state = self.state[:128] #Discord limits to 128 characters. Not my choice
        self.large_text = config["large_text"]

    #@pyqtSlot()
    def restart(self):
        self.log.info("Restarting RPC")
        self.RPC.clear()
        self.RPC.close()
        #self.finished.emit()

    def readConfig(self=None):
        with open(f"{self.root}\\config.json") as f:
            return j_load(f)

if __name__ == "__main__":
    config = CustomRPC.readConfig()

    rpc = CustomRPC(
        int(config["client_id"]),
        state=config["default_state"],
        details=config["default_details"],
        large_text=config["large_text"]
    )
    while True:
        rpc.loop()
