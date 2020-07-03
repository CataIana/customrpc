from pypresence import Presence
from pypresence.exceptions import InvalidPipe, InvalidID, ServerError
from PyQt5.QtCore import QTimer, QEventLoop

from random import choice
from win10toast import ToastNotifier

import sys
from datetime import datetime
from time import time
from os import environ, path, getcwd, mkdir
from subprocess import Popen, PIPE
from json import load as j_load
from json import dumps as j_print
from json import loads as j_loadstr

from requests import Session
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

import logging

from imports.c_log import getLogger

class CustomRPC(Presence):
    def __init__(self, client_id, *args, **kwargs):
        if "logger" in kwargs:
            self.log = kwargs["logger"]
        else:
            self.log = getLogger("DEBUG")
        super(CustomRPC, self).__init__(client_id)
        self.supported_platforms = ["win32"] #It's for personal use, I don't use linux anymore or macos
        if sys.platform not in self.supported_platforms:
            self.log.critical(f"Unsupported Platform! ({sys.platform})") #Exit if not on windows
            sys.exit()

        try:
           self.root = path.dirname(path.realpath(__file__))
        except NameError:
            self.root = getcwd()

        self.time_left = None
        self.toaster = ToastNotifier()
        self.exclusions = ["svchost.exe"] #Clean up program list. Kinda uncessary but probably saves ram.
        self.image_list = [
            "kitty", "chicken", "chickies", "chub", "kitty2", 
            "kitty3", "kitty4", "sleepy", "kitty5", "kitty6", "kitty7"] #The images available to the script
        self.game_icons = {
            "Battlefield 1": "bf1",
            "Call of Duty: Black Ops": "bo1",
            "Call of Duty: Black Ops - Multiplayer": "bo1m",
            "Counter-Strike: Global Offensive": "csgo",
            "Fortnite": "fortnite",
            "Forza Horizon 4": "forza",
            "Golf With Your Friends": "golf",
            "GTA V": "gta",
            "Minecraft": "minecraft",
            "Mirror's Edge Catalyst": "mirrors_edge",
            "Mercy Time on Overwatch": "ow",
            "Rocket League": "rocket",
            "Rainbow Six Seige": "seige",
            "Valorant": "valorant",
            "VirtualBox VM": "vbox",
            "VSCode": "vscode",
            "Warframe": "warframe",
        }
        self.music_file = f"{self.root}\\..\\..\\rainmeter skin\\@Resources\\music.txt"
        self.isConnected = False
        self.lastUpdateTime = 0
        self.errored = False
        self.rollingIndexDetails = 0
        self.rollingIndexState = 0
        self.rollingOptions = [
            "Time",
            "Weather",
            "Use Text"
        ]

        self.rSession = Session()
        self.fetchWeather()

        self.isRunning = True

        self.reconnect() #Initalize connection. Own function created to avoid errors if discord isn't open
        try:
            self.updateRPC(False)
        except ServerError:
            self.log.critical("Client ID is invalid!")
            raise TypeError(f"Client ID {self.client_id} is invalid")
        except InvalidID:
            self.updateRPC(False)

    def reconnect(self):
        while not self.isConnected:
            try:
                self.connect()
            except InvalidPipe:
                self.log.error("Cannot connect to discord! Is discord open? (Invalid Pipe)")
            except ConnectionRefusedError:
                self.log.error("Cannot connect to discord! Is discord open? (Connection Refused)")
            except FileNotFoundError:
                self.log.error("Cannot connect to discord! Is discord open? (File Not Found)")
            except InvalidID:
                self.log.critical("Cannot connect to discord! Is discord open? (Invalid ID)")
            else:
                self.log.info("Connected.")
                self.isConnected = True
            loop = QEventLoop()
            QTimer.singleShot(5000, loop.quit)
            loop.exec_()

    def updateRPC(self, wait=True): #Not sure why this didn't happen sooner, but set the details straight away, rather than waiting for a change.
        self.getVariables()
        config = self.readConfig()
        if (self.lastUpdateTime + 14) > time() and self.lastUpdateTime != 0: #This is a workaround for at the start of the code execution. Because the __init__ of this needs to finish,
            initSleep = (self.lastUpdateTime + 14) - time() #before the UI part will start working we must skip the sleep, otherwise the program will not progress until that sleep completes. This is the use of the wait variable at the bottom of this function
            self.log.debug(f"Init sleeping for {initSleep}") #This loop is then put into action immediately after without waiting, which is an issue, as the RPC is set after about 2 seconds, which discord will accept, but it should only be set every 15 seconds
            loop = QEventLoop()
            QTimer.singleShot(initSleep*1000, loop.quit)
            loop.exec_() #This prevents that and should only run at the very start, or somehow the sleep(15) at the bottom of this function gets cut short. It will be logged for now to ensure this is the case
            self.getVariables() #Since it generally sleeps for about 14 seconds, get the variables again, just to be sure

        if config["use_time_left"]:
            output = self.update(
                state=self.state,
                details=self.details,
                end=self.time_left,
                large_image=choice(self.image_list),
                large_text=self.large_text,
                small_image=self.small_image,
                small_text=self.small_text
            ) #Set status and store for terminal output
        else:
            output = self.update(
                state=self.state,
                details=self.details,
                start=self.time_left,
                large_image=choice(self.image_list),
                large_text=self.large_text,
                small_image=self.small_image,
                small_text=self.small_text
            ) #Set status and store for terminal output
        self.lastUpdateTime = time()
        self.rollingIndexDetails += 1
        self.rollingIndexState += 1
        timestamps = ""
        for x, y in output["data"]["timestamps"].items():
            timestamps += f"{x}: {y}, ".strip(", ")
        self.log.info(f"{output['cmd']} State: {output['data']['state']} Details: {output['data']['details']}  Timestamps: {timestamps}")
        if wait == True:
            loop = QEventLoop()
            QTimer.singleShot(15000, loop.quit)
            loop.exec_()

    def mainLoop(self):
        while self.isRunning:
            if self.isConnected:
                prev_state, prev_details, prev_large_text, prev_time_left = self.state, self.details, self.large_text, self.time_left #Store previous state/details
                self.getVariables()
                f = True
                while self.state == prev_state and self.details == prev_details and self.large_text == prev_large_text and self.compareTimes(self.time_left, prev_time_left): #If variables haven't changed don't bother sending requests to discord.
                    if f:
                        self.log.info("Waiting for update")
                        f = False
                    self.getVariables() #Check if variables have changed
                    try:
                        if __name__ == "__main__":
                            sys.stdout.write('\x1b[2K')
                    except AttributeError:
                        pass
                    loop = QEventLoop()
                    QTimer.singleShot(2000, loop.quit)
                    loop.exec_() #Avoid wasting cpu time and wait 2 seconds before trying again
                try:
                    sys.stdout.write('\x1b[2K') #Clear terminal line if applicable
                except AttributeError: #Except required if not running via a terminal
                    pass
                try:
                    self.updateRPC()
                except InvalidID:  #If connection lost to Discord, attempt reconnection
                    self.log.info("Reconnecting...")
                    self.isConnected = False
                    self.close()
                    self.reconnect()
                except ServerError:
                    self.log.critical("Client ID is invalid!")
                    self.close()

    def getVariables(self):
        config = self.readConfig()
        if config["enable_media"] == True:
            try:
                with open(self.music_file) as f:
                    music_read = f.read().splitlines() #Read music file
            except FileNotFoundError:
                config["enable_media"] = False
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
                    self.state = self.getDefaults("state") #If music is not playing let details be the default setting
                    self.time_left = None
            except IndexError: #Rainmeter rewrites to the music.txt file multiple times per second, and python may catch the text file with nothing in it.
                pass #Prevents errors that may occur every few hours. Holy shit this took a long time to diagnose
        else:
            self.state = self.getDefaults("state") #If user disabled showing media, let state be default
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
            self.details = self.getDefaults("details") #Below code doesn't change anything if no process in gamelist is running. Wasn't an issue when not using OOP. Simplest fix, rather than making a boolean or similar
            self.small_image = None
            self.small_text = None
            try:
                with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json") as g:
                    gamelist = j_load(g) #Read the json gamelist into the json library
            except FileNotFoundError:
                if not path.isdir(f"{environ['LOCALAPPDATA']}\\customrpc"):
                    mkdir(f"{environ['LOCALAPPDATA']}\\customrpc")
                with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json", "w") as g:
                    g.write("{\n}")
                with open(f"{environ['LOCALAPPDATA']}\\customrpc\\gamelist.json") as g:
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
                        try:
                            self.small_image = self.game_icons[realname]
                        except KeyError:
                            self.small_image = None
                        self.small_text = realname
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
                                try:
                                    self.small_image = self.game_icons[realname]
                                except KeyError:
                                    self.small_image = None
                                self.small_text = realname
                                break
                            else: #Show just the minutes
                                self.details = f"Playing {realname} for {d['Minutes']}m"
                                try:
                                    self.small_image = self.game_icons[realname]
                                except KeyError:
                                    self.small_image = None
                                self.small_text = realname
                                break
                        else: #Otherwise display hours and minutes
                            self.details = f"Playing {realname} for {d['Hours']}h:{d['Minutes']}m"
                            try:
                                self.small_image = self.game_icons[realname]
                            except KeyError:
                                self.small_image = None
                            self.small_text = realname
                            break
        else:
            self.details = self.getDefaults("details")
            self.small_image = None
            self.small_text = None

        if config["enable_media"] == True:
            if "vlc.exe" in programlist.keys(): #Check if vlc is running
                self.rSession.auth = ("", config["vlc_pwd"]) #Login to vlc client. See https://www.howtogeek.com/117261/how-to-activate-vlcs-web-interface-control-vlc-from-a-browser-use-any-smartphone-as-a-remote/
                try:
                    r = self.rSession.get('http://localhost:8080/requests/status.xml', verify=False) #Authenticate the vlc web client
                except ConnectionError:
                    if self.errored == False:
                        self.toaster.show_toast("RPC",
                            "Unable to access VLC web interface!\nHave you activated the web interface?\nHave you allowed VLC through Windows Firewall?",
                            icon_path="custom.ico",
                            duration=10
                        )
                        self.errored = True
                else:
                    soup = BeautifulSoup(r.text, "lxml") #Do the BS4 magic
                    title_error = soup.find("title")
                    if title_error != None:
                        if self.errored == False:
                            self.toaster.show_toast("RPC",
                                "Unable to access VLC web interface!\nDid you set the correct password?",
                                icon_path="custom.ico",
                                duration=10
                            )
                            self.errored = True
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
    
    def readConfig(self=None):
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
            return j_load(f)

    def compareTimes(self, a, b):
        try:
            if abs(a - b) < 3:
                return True
        except TypeError:
            return True

    def stop(self):
        self.clear()
        self.close()
        self.isRunning = False

    def getDefaults(self, type_, config_override=None):
        if config_override == None:
            config = self.readConfig()
        else:
            config = config_override
        if type_ == "details":
            if config["default_option"] == "Time":
                return "Sydney, Australia 🇦🇺"
            if config["default_option"] == "Weather":
                return "Sydney, Australia 🇦🇺"
            if config["default_option"] == "Use Text":
                return config["default_details"]
            if config["default_option"] == "Rotating":
                if self.rollingIndexDetails > self.rollingOptions.__len__()-1:
                    self.rollingIndexDetails = 0
                config["default_option"] = self.rollingOptions[self.rollingIndexDetails]
                return self.getDefaults(type_, config)
        if type_ == "state":
            if config["default_option"] == "Time":
                return f"{datetime.now():%Y-%m-%d %I:%M %p}"
            if config["default_option"] == "Weather":
                return f"Currently {self.getWeather('temp')}°C degrees"
            if config["default_option"] == "Use Text":
                return config["default_state"]
            if config["default_option"] == "Rotating":
                if self.rollingIndexState > self.rollingOptions.__len__()-1:
                    self.rollingIndexState = 0
                config["default_option"] = self.rollingOptions[self.rollingIndexState]
                return self.getDefaults(type_, config)
        return "None"

    def getWeather(self, request):
        if self.weather_json["time"]+900 < int(time()):
            self.fetchWeather()
        
        if self.weather_json["cod"] == 200:
            if request == "temp":
                return f"{(self.weather_json['main']['temp'] - 273.15):.2f}"
            else:
                return None
        else:
            return None

    def fetchWeather(self):
        city_id = "2147714"
        api_key = "23acbaf2250474acbe34f76ffc375b0f"
        rw = self.rSession.get(f"https://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={api_key}")
        self.weather_json = j_loadstr(rw.text)
        self.weather_json["time"] = int(time())
        self.log.info("Requesting weather info")
        
