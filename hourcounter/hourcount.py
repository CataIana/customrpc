from subprocess import Popen, PIPE
from json import dumps as j_print
from json import load as j_load
from os import getcwd
from signal import signal, SIGINT, SIGTERM
from traceback import format_exc
from discord_webhook import DiscordEmbed
import logging
from time import sleep

class RPCHourCount():
    def __init__(self):
        self.root = "\\".join(getcwd().split('\\')[:-1])
        self.music_file = f"{self.root}\\rainmeter skin\\@Resources\\music.txt"
        self.open_processes = {}
        self.exclusions = ["svchost.exe"]

        with open("spam.log", "w"):
            pass
        self.log = logging.getLogger("Hourcounter")
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s",
                              "%Y-%m-%d %H:%M:%S")
        ch.setFormatter(formatter)
        self.log.addHandler(ch)
        self.log.setLevel(logging.DEBUG)
        fh = logging.FileHandler("spam.log")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.log.addHandler(fh)
    
        self.is_running = True
        signal(SIGINT, self.stop)
        signal(SIGTERM, self.stop)

    def add_to_database(self, **kwargs):
        realname, totalhrs = kwargs["realname"], kwargs["totalhrs"]
        with open(f"{getcwd()}\\..\\data\\hourcount.json") as g:
            hourcount = j_load(g)
        if realname in hourcount.keys():
            hourcount[realname] += float(totalhrs)
            with open(f"{getcwd()}\\..\\data\\hourcount.json", "w") as g:
                g.write(j_print(hourcount, indent=4))
        else:
            hourcount[realname] = float(totalhrs)
            with open(f"{getcwd()}\\..\\data\\hourcount.json", "w") as g:
                g.write(j_print(hourcount, indent=4))

    def active_dict(self, pid):
        proc = Popen(f"powershell New-TimeSpan -Start (get-process -id {pid}).StartTime", shell=True, stdout=PIPE)
        timeactive = []
        for line in proc.stdout:
            timeactive.append(line.decode().rstrip().replace(" ", ""))
        if timeactive[0] == f"get-process:Cannotfindaprocesswiththeprocessidentifier{pid}.":
            return "None"
        d = {}
        for line in list(filter(None, timeactive)):
            d[line.split(":")[0]] = line.split(":")[1]
        return d["TotalHours"]

    def close_loop(self):
        self.program_loop()
        self.music_loop()
        toremove = []
        for active_process in self.open_processes:
            if active_process not in self.programlist.keys():
                with open(f"{self.root}\\data\\gamelist.json") as e:
                    gamelist = j_load(e)
                for x, y in gamelist.items():
                    if x == active_process:
                        realname = y
                self.add_to_database(realname=realname, totalhrs=self.open_processes[active_process])
                toremove.append(active_process)
        if toremove.__len__() > 0:
            for remove in toremove:
                self.log.info(f"{remove} closed after running for {self.open_processes[remove]} hours.")
                del self.open_processes[remove]

    def program_loop(self):
        self.programlist = {}
        proc = Popen(["WMIC", "PROCESS", "get", "Caption", ",", "ProcessID"], shell=True, stdout=PIPE) #Get running processes and process ids associated with them
        for line in proc.stdout:
            program = line.decode().rstrip().split()#Clean up line
            if len(program) > 0: #If line isn't blank
                if program[0] not in self.exclusions: #If process isn't in exclusions list
                    self.programlist[program[0]] = program[1] #Add process and process id to dictionary

        with open(f"{self.root}\\data\\gamelist.json") as e:
            inclusions = j_load(e)

        for exe in inclusions.keys():
            if exe in self.programlist.keys():
                if exe not in self.open_processes:
                    self.log.info(f"{exe} opened.")
                    totalhrs = self.active_dict(self.programlist[exe])
                    self.open_processes[exe] = totalhrs

        for active_exe in self.open_processes:
            try:
                totalhrs = self.active_dict(self.programlist[active_exe])
                if totalhrs != "None":
                    self.open_processes[active_exe] = totalhrs
            except KeyError:
                pass
        #print(j_print(self.open_processes, indent=4))
        
    
    def music_loop(self):
        with open(self.music_file) as g:
            gr = g.read().splitlines()
            if gr.__len__() == 0:
                return
            self.music = {
                "song": gr[0],
                "state": gr[1],
                "current": gr[2],
                "duration": gr[3]
            }
            del gr
            #print(j_print(self.music, indent=4))
        
    def stop(self, recieved, frame):
        self.log.info("Stopping")
        self.is_running = False

hourcount = RPCHourCount()
while hourcount.is_running:
    sleep(5)
    hourcount.close_loop()