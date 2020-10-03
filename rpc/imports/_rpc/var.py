from win10toast import ToastNotifier
from requests import Session

def variables(self):
    self.time_left = None
    self.toaster = ToastNotifier()
    self.exclusions = ["svchost.exe"] #Clean up program list. Kinda uncessary but probably saves ram.
    self.image_list = [
        "kitty", "chicken", "chickies", "chub", "kitty2", "kitty3",
        "kitty4", "sleepy", "kitty5", "kitty6", "kitty7", "kitty8",
        "kitty9"] #The images available to the script
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