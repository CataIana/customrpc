from time import time
from json import loads as j_loadstr
from requests.exceptions import ConnectionError


def getWeather(self, request):
    if self.weather_json["time"]+900 < int(time()):
        self.fetchWeather()

    try:
        if request == "temp":
            return round(self.weather_json["current"]["temp"], 1)
        elif request == "description":
            return self.weather_json["current"]["weather"][0]["description"].title()
        else:
            return None
    except KeyError:
        return None


def fetchWeather(self):
    lat = "-33.8426359"
    lon = "150.8306575"
    config = self.readConfig()
    self.weather_api_key = config["weather_api_key"]
    if self.weather_api_key != "":
        self.log.info("Requesting weather info")
        try:
            rw = self.rSession.get(
                f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units=metric&exclude=minutely,hourly,daily&appid={self.weather_api_key}")
        except ConnectionError:
            self.log.error("Failed to request weather info!")
            self.weather_json = {}
            self.weather_json["cod"] = 0
            self.weather_json["time"] = int(time()-860)
            return
        else:
            self.weather_json = j_loadstr(rw.text)
            self.weather_json["time"] = int(time())
            return
    else:
        self.log.error("API Key not provided for weather.")
        self.weather_json = {}
        self.weather_json["cod"] = 0
        self.weather_json["time"] = int(time()-860)
        return
