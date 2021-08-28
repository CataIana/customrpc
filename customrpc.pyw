from time import time, sleep
from json.decoder import JSONDecodeError
from json import load as j_load
from random import choice
import spotipy.util as util
from os import getcwd
from psutil import process_iter, boot_time
from spotipy import Spotify, SpotifyException
from pypresence import Presence
from pypresence.exceptions import InvalidID, InvalidPipe
from time import localtime, strftime, sleep
from requests import get
from xml_to_dict import XMLtoDict
import logging
import sys
import signal
from traceback import format_tb


class CustomRPC():
    def __init__(self):
        with open(f"{getcwd()}/config.json") as f:
            self.config = j_load(f)

        if __name__ == "__main__":
            signal.signal(signal.SIGINT, self.close)
        self.format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        self.log_level = logging.DEBUG
        self.log = logging.getLogger("customrpc")
        self.log.setLevel(self.log_level)

        fhandler = logging.FileHandler(filename="rpc.log", encoding="utf-8", mode="w+")
        fhandler.setLevel(logging.WARNING)
        fhandler.setFormatter(self.format)
        self.log.addHandler(fhandler)

        chandler = logging.StreamHandler(sys.stdout)                             
        chandler.setLevel(self.log_level)
        chandler.setFormatter(self.format)                                        
        self.log.addHandler(chandler)

        self.prev_cid = None
        self.connected = False
        self.previous_payload = None
        self.force_update = True
        self.auth_spotify()
        self.xml_parser = XMLtoDict()

    def auth_spotify(self):
        self.log.debug("Authorising Spotify")
        token = util.prompt_for_user_token(
            scope="user-read-currently-playing user-read-playback-state", **self.config["spotify"])
        self.sp = Spotify(auth=token)

    def reconnect(self, client_id=None):
        if client_id is None:
            client_id = self.config["default_cid"]
        if self.connected:
            self.RPC.close()
            self.connected = False
        self.log.info(f"Connecting with Client ID {client_id}")
        self.RPC = Presence(client_id=client_id)
        while True:
            try:
                self.RPC.connect()
            except InvalidID as e:
                sleep(2)
                self.log.debug(f"Retrying... ({e})")
            except InvalidPipe as e:
                sleep(2)
                self.log.debug(f"Retrying... ({e})")
            else:
                break
        self.log.info("Connected")
        self.force_update = True
        self.connected = True

    def same_payload(self, payload):
        if self.previous_payload == None:
            self.previous_payload = payload
        if self.force_update:
            self.force_update = False
            return False
        for x, y in payload.items():
            if x in ["large_image", "small_image"]:  # Things to not bother comparing
                continue
            if x in ["start", "end"]:
                if not self.compare_times(self.previous_payload.get(x, None), y):
                    self.previous_payload = payload
                    return False
            else:
                if self.previous_payload.get(x, None) != y:
                    self.previous_payload = payload
                    return False
        return True

    def compare_times(self, a, b):
        try:
            if abs(a-b) < 3:
                return True
        except TypeError:
            return True

    def get_payload(self):
        extra_button = None
        media_button = None
        payload = {
            "details": self.config["fallback_details"],
            "state": self.config["fallback_state"],
            "large_image": choice(self.config["large_image_names"]),
            "large_text": self.config["fallback_largetext"]
        }
        if self.config["use_extra_button"]:
            extra_button = self.config["extra_button"]
        client_id = None
        if self.config["show_spotify"]:
            try:
                spotify = self.sp.current_user_playing_track()
            except SpotifyException:
                self.auth_spotify()
                spotify = self.sp.current_user_playing_track()
            if spotify is None:
                client_id = None
            else:
                if not spotify["is_playing"]:
                    client_id = None
                else:
                    try:
                        payload["state"] = f"{spotify['item']['name']} - {spotify['item']['artists'][0]['name']}"
                        media_button = {"label": "Play on Spotify", "url": spotify["item"]["external_urls"]["spotify"]}
                        client_id = self.config["spotify_cid"]
                        if self.config["use_time_left_media"] == True:
                            payload["end"] = time(
                            ) + (int(spotify["item"]["duration_ms"]/1000) - int(spotify["progress_ms"]/1000))
                        else:
                            payload["start"] = int(
                                time() - int(spotify["progress_ms"]/1000))
                        payload["small_image"] = self.config["spotify_icon"]
                    except KeyError as e:
                        formatted_exception = "Traceback (most recent call last):\n" + ''.join(format_tb(e.__traceback__)) + f"{type(e).__name__}: {e}"
                        self.log.error(formatted_exception)
        if self.config["show_other_media"] or self.config["show_games"]:
            games = list(self.config["games"].keys())+["vlc.exe"]
            processes = {p.name(): {"object": p, "info": self.config["games"].get(p.name().lower(), None)} for p in process_iter() if p.name().lower() in games}
        if self.config["show_other_media"]:
            process = processes.get("vlc.exe", None)
            if process is not None:
                process_info = process["info"]
                try:
                    r = get("http://localhost:8080/requests/status.xml", verify=False, auth=("", self.config["vlc_http_password"]), timeout=2)
                except ConnectionError as e:
                    pass
                    self.log.debug(f"Connection error processing VLC dict: {e}")
                else:
                    try:
                        p = self.xml_parser.parse(r.text)["root"]
                        if p["state"] == "playing":
                            vlctitle = None
                            vlcartist = None
                            for x in p["information"]["category"][0]["info"]:
                                if type(p["information"]["category"][0]["info"]) is not list:
                                    x = p["information"]["category"][0]["info"]
                                if x["@name"] == "title":
                                    vlctitle = x["#text"]
                                if x["@name"] == "filename":
                                    vlcfilename = x["#text"]
                                if x["@name"] == "artist":
                                    vlcartist = x["#text"]
                            if vlctitle is None:
                                vlctitle = vlcfilename
                            payload["state"] = f"{vlctitle} - {vlcartist}"[:112]
                            if self.config["use_time_left_media"] == True:
                                payload["end"] = int(time() + int(p["time"]))
                            else:
                                payload["start"] = int(time() - int(p["time"]))
                            payload["small_image"] = self.config["vlc_icon"]
                            client_id = self.config["vlc_cid"]
                    except KeyError as e:
                        self.log.debug(f"KeyError processing VLC dict: {e}")

            webnp = {}
            failed = 0
            while webnp == {}:
                try:
                    with open(".info.json") as f:
                        webnp = j_load(f)
                except JSONDecodeError:
                    failed += 1
                    if failed > 9:
                        break
                except FileNotFoundError:
                    break
            if time() - webnp.get("last_update", 0) < 10:
                if webnp.get("state", None) == "1":
                    if webnp["player"] in self.config["other_media"].keys():
                        client_id = self.config["other_media"][webnp["player"]]["client_id"]
                        if len(f"{webnp['title']} - {webnp['artist']}") > 128:
                            payload["state"] = f"{webnp['title'][:-(len(webnp['artist'])-(128-len(webnp['artist'])-3))]}... - {webnp['artist']}"
                        else:
                            payload["state"] = f"{webnp['title']} - {webnp['artist']}"
                        payload["small_image"] = self.config["other_media"][webnp["player"]]["icon"]
                        if webnp["player"] == "Twitch":
                            media_button = {"label": "Watch on Twitch", "url": f"https://twitch.tv/{webnp['artist'].lower()}"}
                        else:
                            media_button = None
                        duration_read = webnp["duration"].split(":")[::-1]
                        position_read = webnp["position"].split(":")[::-1]
                        duration = 0
                        position = 0
                        try:
                            for i in range(len(duration_read)-1, -1, -1): #Smart loop to convert times from hour/minutes to seconds. Fully expandable, so works with any lengths
                                duration += int(duration_read[i])*(60**i)
                            for i in range(len(position_read)-1, -1, -1):
                                position += int(position_read[i])*(60**i)
                        except ValueError:
                            formatted_exception = "Traceback (most recent call last):\n" + ''.join(format_tb(e.__traceback__)) + f"{type(e).__name__}: {e}"
                            self.log.warning(formatted_exception)
                        if self.config["use_time_left_media"] == True:
                            payload["end"] = int(time() + (duration - position))
                        else:
                            payload["start"] = int(time() - position)
        if self.config["show_games"]:
            if processes != {}:
                processes.pop("vlc.exe", None)
                process = list(processes.values())[0]
                process_info = process["info"]
                if self.prev_cid != process_info["client_id"]:
                    self.log.debug(
                        f"Matched process {process['object'].name()} to client ID {process_info['client_id']} with name {process_info['name']}")
                try:
                    create_time = process["object"].create_time()
                except OSError:
                    # system processes, using boot time instead
                    create_time = boot_time()
                epoch = time() - create_time
                conv = {
                    "days": str(epoch // 86400).split('.')[0],
                    "hours": str(epoch // 3600 % 24).split('.')[0],
                    "minutes": str(epoch // 60 % 60).split('.')[0],
                    "seconds": str(epoch % 60).split('.')[0],
                    "full": strftime('%Y-%m-%d %I:%M:%S %p %Z', localtime(create_time))
                }
                time_info = f"for {conv['days'] if conv['days'] != '0' else ''}{'' if conv['days'] == '0' else 'd, '}{conv['hours'] if conv['hours'] != '0' else ''}{'' if conv['hours'] == '0' else 'h, '}{conv['minutes'] if conv['minutes'] != '0' else ''}{'' if conv['minutes'] == '0' else 'm'}"
                if time_info == "for ":
                    time_info = "0m"

                client_id = process_info["client_id"]
                payload["details"] = f"{time_info}"
                payload["small_image"] = process_info["icon"]

        if [media_button, extra_button] != [None, None]:
            payload["buttons"] = []
        if media_button is not None:
            payload["buttons"].append(media_button)
        if extra_button is not None:
            payload["buttons"].append(extra_button)


        return client_id, payload

    def main(self):
        client_id, payload = self.get_payload()
        if self.prev_cid != client_id:
            self.log.info(f"Switching from {self.prev_cid} to {client_id}")
            self.prev_cid = client_id
            if client_id is not None:
                self.reconnect(client_id=client_id)
            else:
                self.RPC.clear()
        if not self.connected and client_id is not None:
            self.reconnect(client_id=client_id)
        if not self.same_payload(payload):
            self.log.debug(f"Setting presence with payload {payload}")
            if client_id is not None:
                while True:
                    try:
                        self.RPC.update(**payload)
                    except InvalidID:
                        self.log.warning("Invalid ID, restarting...")
                        self.reconnect(client_id=client_id)
                    except InvalidPipe:
                        self.log.warning("InvalidPipe, is discord running? Reconnecting...")
                        self.reconnect(client_id=client_id)
                    else:
                        break
            sleep(15)
        else:
            self.log.debug("Ignoring same payload")
            sleep(5)
        try:
            with open(f"{getcwd()}/config.json") as f:
                self.config = j_load(f)
        except JSONDecodeError:
            self.log.warning("Error reading config file")
        except FileNotFoundError:
            self.log.warning("Error reading config file")

    def close(self, signal, frame):
        self.log.info("Stopping...")
        try:
            self.RPC.close()
        except AttributeError:
            pass
        sys.exit()

    def get_traceback(self):
        return "Traceback (most recent call last):\n" + ''.join(format_tb(e.__traceback__)) + f"{type(e).__name__}: {e}"

if __name__ == "__main__":
    rpc = CustomRPC()
    while True:
        try:
            rpc.main()
        except Exception as e:
            rpc.log.error(rpc.get_traceback())
