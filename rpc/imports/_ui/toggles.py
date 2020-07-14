def toggleGames(self):
    config = self.readConfig() #Switch between true and false in config file, do the same for the UI text
    if config["enable_games"] == True:
        self.disableGames.setText("Enable Games")
        config["enable_games"] = False
    elif config["enable_games"] == False:
        self.disableGames.setText("Disable Games")
        config["enable_games"] = True
    self.log.info(f"Toggled games to {config['enable_games']}")
    self.updateConfig(config)

def toggleMedia(self):
    config = self.readConfig() #Switch between true and false in config file, do the same for the UI text
    if config["enable_media"] == True:
        self.disableMedia.setText("Enable Media")
        config["enable_media"] = False
    elif config["enable_media"] == False:
        self.disableMedia.setText("Disable Media")
        config["enable_media"] = True
    self.log.info(f"Toggled media to {config['enable_media']}")
    self.updateConfig(config)

def toggleTime(self): #Switch between true and false in config file, do the same for the UI text
    config = self.readConfig()
    if config["use_time_left"] == True:
        self.timeFormat.setText("Use End Time")
        config["use_time_left"] = False
    elif config["use_time_left"] == False:
        self.timeFormat.setText("Use Start Time")
        config["use_time_left"] = True
    self.log.info(f"Toggled time format to {config['use_time_left']}")
    self.updateConfig(config)