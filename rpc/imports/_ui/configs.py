from json import load as j_load  #Reading config files
from json import dumps as j_print
from os import environ, path, mkdir

def updateConfig(self, config):
    with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json", "w") as f:
        f.write(j_print(config, indent=4)) #Overwrite config file with config passed

def readConfig(self):
    try:
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f: #Read  config and return in json format
            return j_load(f)
    except FileNotFoundError:
        self.log.error("Config not found! Generating...") #Generate config with default options if not found
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
            mkdir(f"{environ['LOCALAPPDATA']}\\customrpc") #Create customrpc folder if it doesn't exist
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json", "w") as f:
            f.write(j_print(data, indent=4)) #Write new config file
        self.log.info("Sucessfully created config file.")
        with open(f"{environ['LOCALAPPDATA']}\\customrpc\\config.json") as f:
            return j_load(f) #And return it as normal