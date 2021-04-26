from pypresence.exceptions import InvalidPipe, InvalidID
from time import time, sleep
from random import choice

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
        sleep(5)

def updateRPC(self, fallback, wait=True): #Not sure why this didn't happen sooner, but set the details straight away, rather than waiting for a change.
    self.getVariables(fallback)
    config = self.readConfig()
    if (self.lastUpdateTime + 14) > time() and self.lastUpdateTime != 0: #This is a workaround for at the start of the code execution. Because the __init__ of this needs to finish,
        initSleep = (self.lastUpdateTime + 14) - time() #before the UI part will start working we must skip the sleep, otherwise the program will not progress until that sleep completes. This is the use of the wait variable at the bottom of this function
        self.log.debug(f"Init sleeping for {initSleep}") #This loop is then put into action immediately after without waiting, which is an issue, as the RPC is set after about 2 seconds, which discord will accept, but it should only be set every 15 seconds
        sleep(initSleep) #This prevents that and should only run at the very start, or somehow the sleep(15) at the bottom of this function gets cut short. It will be logged for now to ensure this is the case
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
    try:
        for x, y in output["data"]["timestamps"].items():
            timestamps += f"{x}: {y}, ".strip(", ")
    except KeyError:
        pass
    self.log.info(f"{output['cmd']} State: {output['data']['state']} Details: {output['data']['details']}  Timestamps: {timestamps}")
    if wait == True:
        sleep(15)