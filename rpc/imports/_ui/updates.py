def updateClientID(self):
    new_clientID = self.clientIDInput.text() #Fetch input text
    config = self.readConfig()
    if new_clientID == "": #Run checks to make sure client id is somewhat valid, I don't know the actual requirements for a valid client id, but these are close enough
        result = "Client ID cannot be empty!" #Set text for info box
        b = False #Don't bother updating config if client id is invalid
    if new_clientID.__len__() != 18:
        result = "Client ID must be 18 digits!" #Set text for info box
        b = False #Don't bother updating config if client id is invalid
    try:
        int(new_clientID)
    except ValueError:
        result = "Value must be an integer!" #Set text for info box
        b = False #Don't bother updating config if client id is invalid
    else:
        config["client_id"] = int(new_clientID) #Update config client id
        result = f'Set client ID. Restart program to apply changes' #Set text for info box
        b = True #Make sure to update config with new client id
    self.log.info(f'Set client ID to "{config["client_id"]}"')
    self.info.setText(result)
    if b:
        self.updateConfig(config)

def updateState(self):
    new_state = self.stateInput.text() #Fetch input text
    config = self.readConfig()
    if new_state.__len__() > 128: #Run checks to make sure state isn't too long or too short
        result = "String too long!"
        b = False #Don't bother updating config if state is invalid
    elif new_state.__len__() < 2:
        result = "String too short!"
        b = False #Don't bother updating config if state is invalid
    else:
        config["default_state"] = new_state #Update config state
        self.log.info(f"Set details to {config['default_state']}") #Set text for info box
        result = f'Set details to "{config["default_state"]}"'
        b = True #Make sure to update config with new state
    self.info.setText(result)
    if b:
        self.updateConfig(config)

def updateDetails(self):
    new_details = self.detailsInput.text() #Fetch input text
    config = self.readConfig()
    if new_details.__len__() > 128: #Run checks to make sure details isn't too long or too short
        result = "String too long!"
        b = False #Don't bother updating config if details is invalid
    elif new_details.__len__() < 2:
        result = "String too short!"
        b = False #Don't bother updating config if details is invalid
    else:
        config["default_details"] = new_details #Update config details
        self.log.info(f"Set details to {config['default_details']}") #Set text for info box
        result = f'Set details to "{config["default_details"]}"'
        b = True #Make sure to update config with new details
    self.info.setText(result)
    if b:
        self.updateConfig(config)

def updateDefaultOptions(self):
    config = self.readConfig()
    config["default_option"] = self.defaultOptionsList.currentText() #Static options, no checks need to be done here. Overwrite and write to file
    self.log.info(f"Set default option to {config['default_option']}")
    self.info.setText(f"Set default option to {config['default_option']}")
    self.updateConfig(config)

def updateLargeText(self):
    new_large_text = self.largeTextInput.text() #Fetch input text
    config = self.readConfig()
    if new_large_text.__len__() > 128: #Run checks to make sure text isn't too long or too short
        result = "String too long!"
        b = False #Don't bother updating config if text is invalid
    elif new_large_text.__len__() < 2:
        result = "String too short!"
        b = False #Don't bother updating config if text is invalid
    else:
        config["large_text"] = new_large_text #Update config text
        self.log.info(f"Set details to {config['large_text']}") #Set text for info box
        result = f'Set details to "{config["large_text"]}"'
        b = True #Make sure to update config with new text
    self.info.setText(result)
    if b:
        self.updateConfig(config)