from time import time
from json import loads as j_loadstr

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