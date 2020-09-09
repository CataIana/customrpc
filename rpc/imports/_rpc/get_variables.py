import sys
from time import time
from datetime import datetime
from os import environ, path, mkdir

from json import load as j_load

from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

from subprocess import Popen, PIPE

def getVariables(self):
    config = self.readConfig()
    if config["enable_media"] == True:
        try:
            with open(self.music_file) as f:
                music_read = f.read().splitlines() #Read music file
        except FileNotFoundError:
            config["enable_media"] = False
            self.state = config["default_state"]
        else:
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
                    if self.state == "Twitch - Twitch":
                        self.state = config["twitch_replacement"]
                    #Calculate the difference between the 2 times and set time left to how long that is plus the current time
                    if config["use_time_left"] == True:
                        self.time_left = time() + (duration - position)
                    else:
                        self.time_left = int(time() - position)
                else:
                    self.state = self.getDefaults("state") #If music is not playing let details be the default setting
                    self.time_left = None
            except IndexError: #Rainmeter rewrites to the music.txt file multiple times per second, and python may catch the text file with nothing in it.
                self.state = config["default_state"] #Prevents errors that may occur every few hours. Holy shit this took a long time to diagnose
    else:
        self.state = self.getDefaults("state") #If user disabled showing media, let state be default
        self.time_left = None #When setting state, always set time_left

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
        try:
            programlist = fetchProgramList(self.exclusions)
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
        except Exception as e:
            self.log.critical(e)
            sys.exit()
    else:
        self.details = self.getDefaults("details")
        self.small_image = None
        self.small_text = None

    if config["enable_media"] == True and config["vlc_pwd"] != "":
        programlist = fetchProgramList(self.exclusions)
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

def fetchProgramList(exclusions):
    programlist = {} #Program list is required for vlc detection, and it also required for game detection
    proc = Popen(["WMIC", "PROCESS", "get", "Caption", ",", "ProcessID"], shell=True, stdout=PIPE) #Get running processes and process ids associated with them
    for line in proc.stdout:
        program = line.decode().rstrip().split()#Clean up line
        if len(program) > 0: #If line isn't blank
            if program[0] not in exclusions: #If process isn't in exclusions list
                programlist[program[0]] = program[1] #Add process and process id to dictionary
    return programlist

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