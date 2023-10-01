import json
import logging
import signal
import sys
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from random import choice
from time import localtime, sleep, strftime, time
from traceback import format_tb
from typing import Optional, Union

from psutil import Process, boot_time, process_iter
from pypresence import Presence
from pypresence.exceptions import (DiscordError, DiscordNotFound, InvalidID,
                                   InvalidPipe)
from pywnp import WNPRedux
from requests import ConnectionError, ConnectTimeout, get
from spotipy import Spotify, SpotifyException, SpotifyOAuth
import xmltodict

# This class is just intended to be something that more or less mimics None without it actually being a nonetype
# It's used as a fill in for when a Client ID is not provided for an application
class Empty:
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return "No RPC"


NoRPC = Empty()


@dataclass
class Button:
    label: str
    url: str


@dataclass
class Payload:
    state: str
    details: str
    small_image: str = None
    small_text: str = None
    large_image: str = None
    large_text: str = None
    start: int = None
    end: int = None
    buttons: list = None

    def to_dict(self):
        return self.__dict__

    def add_button(self, button: Button):
        if self.buttons is None:
            self.buttons = []
        if len(self.buttons) < 2:
            self.buttons.append(button)
        else:
            raise TypeError("Cannot add more than 2 buttons!")

    def __str__(self):
        return str({k: v for k, v in self.__dict__.items() if v})

    def __repr__(self):
        return repr(str(self.__dict__))

    # Check if before and after times are within a certain range.
    def compare_times(self, a: int, b: int) -> bool:
        try:
            if abs(a-b) < 10: # Plex has very high variance. 3 seconds is good otherwise
                return True
        except TypeError:
            return True

    def __eq__(self, other):
        for x, y in self.__dict__.items():
            if x in ["large_image", "small_image"]:  # Things to not bother comparing
                continue
            if x in ["start", "end"]:
                if not self.compare_times(getattr(other, x, None), y):
                    return False
            else:
                if getattr(other, x, None) != y:
                    return False
        return True


class CustomRPC():
    def __init__(self):
        with open("config.json") as f:
            self.config: dict = json.load(f)

        if __name__ == "__main__":
            signal.signal(signal.SIGINT, self.close)

        # Setup logging
        self.format = logging.Formatter(
            '%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        self.log_level = logging.DEBUG
        self.log = logging.getLogger("customrpc")
        self.log.setLevel(self.log_level)

        fhandler_rotating = RotatingFileHandler("rpc.log", mode="a+", maxBytes=5*1024*1024, backupCount=0, encoding="utf-8", delay=0)
        fhandler_rotating.setLevel(logging.WARNING)
        fhandler_rotating.setFormatter(self.format)
        self.log.addHandler(fhandler_rotating)

        # fhandler = logging.FileHandler(
        #     filename="rpc.log", encoding="utf-8", mode="a+")
        # fhandler.setLevel(logging.WARNING)
        # fhandler.setFormatter(self.format)
        # self.log.addHandler(fhandler)

        # Ensure logging is also done to console
        chandler = logging.StreamHandler(sys.stdout)
        chandler.setLevel(self.log_level)
        chandler.setFormatter(self.format)
        self.log.addHandler(chandler)

        # WebNowPlaying Init
        WNPRedux.Initialize(1824, "1.1.1", self.log)

        self.prev_cid = None  # The last client ID used for connecting. Used for comparasions
        # If the RPC is currently connected. This can only really be assumed
        self.connected = False
        # Temporary var for comparing between payloads to decide if we need to send an update to discord
        self.previous_payload: Optional[Payload] = None
        # If we should be updating the RPC no matter what. Generally used for Client ID switching and reconnections
        self.force_update = True
        self.last_update = 0
        # Authorize spotify, so we can connect and pull data.
        self.auth_spotify()
        self.vid_is_public: dict[str, bool] = {}

    def auth_spotify(self):
        self.log.debug("Authorising Spotify")
        auth_manager = SpotifyOAuth(
            scope="user-read-currently-playing user-read-playback-state", **self.config["spotify"])
        self.sp = Spotify(auth_manager=auth_manager)
        self.sp._auth

    def reconnect(self, client_id=None):
        # If a client ID hasn't been set, just go with default
        client_id = client_id or self.config["default_cid"]
        if self.connected:  # Reset connection if necessary
            self.RPC.close()
            self.connected = False
        self.log.info(f"Connecting with Client ID {client_id}")
        while True:  # Loop indefinitely until connection is established. Will loop here if discord isn't open
            try:
                # Reinit presence class
                self.RPC = Presence(client_id=client_id)
                self.RPC.connect()
            except (InvalidID, InvalidPipe, DiscordError, DiscordNotFound) as e:
                self.log.debug(f"Retrying... ({e})")
            else:
                break
            sleep(2)
        self.log.info("Connected")
        self.force_update = True  # Client ID switched, ensure we update no matter what
        self.connected = True  # Since we escaped the loop, we must be connected

    # Determine if payload is identical, override if force update required.
    def same_payload(self, payload) -> bool:
        if self.previous_payload == None:
            self.previous_payload = payload
        if self.force_update:
            self.force_update = False
            return False
        return payload == self.previous_payload

    def get_payload(self):
        # Set payload defaults
        extra_button = None
        media_button = None
        payload = Payload(details=self.config["fallback_details"],
                        state=self.config["fallback_state"],
                        large_image=choice(
                        self.config["large_image_urls"]).lower(),
                        large_text=self.config["fallback_largetext"])
        # If enabled, use the extra button information set in the config
        if self.config["use_extra_button"]:
            extra_button = self.config["extra_button"]
        client_id = None

        ### SPOTIFY ###

        if self.config["show_spotify"]:  # If spotify is enabled, fetch data for it
            try:
                spotify_np = self.sp.current_user_playing_track()
            except SpotifyException:
                try:
                    self.auth_spotify()
                except SpotifyException:
                    self.log.error("Unable to connect to spotify!")
                    spotify_np = None
                else:
                    spotify_np = self.sp.current_user_playing_track()
            if spotify_np:
                if spotify_np["is_playing"]:  # If a song isn't playing, move on
                    try:
                        payload.state = f"{spotify_np['item']['name']} - {spotify_np['item']['artists'][0]['name']}"
                        media_button = {
                            "label": "Play on Spotify",
                            "url": spotify_np["item"]["external_urls"]["spotify"]
                        }
                        if self.config["use_time_left_media"]:
                            payload.end = time() + \
                                (int(spotify_np["item"]["duration_ms"] /
                                1000) - int(spotify_np["progress_ms"]/1000))
                        else:
                            payload.start = int(
                                time() - int(spotify_np["progress_ms"]/1000))
                        # Get small image spotify icon
                        payload.small_image = self.config["spotify_icon"]
                        client_id = self.config["spotify_cid"]
                    except KeyError as e:  # If something failed, just log it and move on
                        self.log.error(self.get_traceback(e))

        ### OTHER MEDIA ###

        # If we want to show VLC or games, we need to fetch the process list, storing the data, along with their config information
        if self.config["show_other_media"] or self.config["show_games"]:
            games = list(self.config["games"].keys())+["vlc.exe", "plex.exe"]
            processes: dict[str, dict[str, Union[Process, dict]]] = {p.name(): {"object": p, "info": self.config["games"].get(
                p.name().lower(), None)} for p in process_iter() if p.name().lower() in games}


        if self.config["show_other_media"]:
            # Check if VLC is in the running processes list.

            ### VLC ###

            if process := processes.get("vlc.exe"):
                process_info = process["info"]
                try:  # If VLC is running, make a request to it's API to fetch what if currently playing. If it fails, just ignore and move on. It does fail alot
                    r = get("http://localhost:8080/requests/status.xml", verify=False,
                            auth=("", self.config["vlc_http_password"]), timeout=2)
                except (ConnectionError, ConnectTimeout) as e:
                    self.log.debug(
                        f"Connection error processing VLC dict: {e}")
                else:
                    try:
                        # Use the xml parser to parse the mess of response that VLC gives us
                        p = xmltodict.parse(r.text)["root"]
                        if p["state"] == "playing":
                            vlctitle = None
                            vlcartist = None
                            # Parse VLC information, with some fallbacks. Some media files contain data that others don't
                            for x in p["information"]["category"][0]["info"]:
                                if type(p["information"]["category"][0]["info"]) is not list:
                                    x = p["information"]["category"][0]["info"]
                                if x["@name"] == "title":
                                    vlctitle = x["#text"]
                                if x["@name"] == "filename":
                                    vlcfilename = x["#text"]
                                if x["@name"] == "artist":
                                    vlcartist = x["#text"]
                            vlctitle = vlctitle or vlcfilename
                            # Ensure that the name doesn't hit the character limit, limiting it to 112 characters
                            payload.state = f"{vlctitle}{' - ' if vlcartist else ''}{vlcartist or ''}"[:112]
                            # Set unix time of start/end time
                            if self.config["use_time_left_media"] == True:
                                payload.end = int(
                                    time() + (int(p["length"]) - int(p["time"])))
                            else:
                                payload.start = int(time() - int(p["time"]))
                            # And finally set small icon and client ID, since we know everything else worked
                            payload.small_image = self.config["vlc_icon"]
                            client_id = self.config["vlc_cid"]
                    except KeyError as e:  # In case any weird errors occured fetching data, I'd wanna find out why
                        self.log.error(self.get_traceback(e))

            ### PLEX ###

            if process := processes.get("Plex.exe"):
                process_info = process["info"]
                try:  # If Plex is running, make a request to it's API to fetch what if currently playing. If it fails, just ignore and move on. This only works if video is being played on the same network or VPN at the Pie
                    r = get(
                        f"http://192.168.0.237:32400/status/sessions/?X-Plex-Token={self.config['plex_token']}")
                except (ConnectionError, ConnectTimeout) as e:
                    self.log.debug(
                        f"Connection error processing Plex XML: {e}")
                else:
                    if r.status_code == 200:
                        try:
                            plex_xml = xmltodict.parse(r.text)
                            if int(plex_xml["MediaContainer"]["@size"]) > 0:
                                if type(plex_xml["MediaContainer"]["Video"]) == list:
                                    for i, stream in enumerate(plex_xml["MediaContainer"]["Video"], 0):
                                        if stream["User"]["@title"] == self.config["plex_user"]:
                                            p = plex_xml["MediaContainer"]["Video"][i]
                                else:
                                    p = plex_xml["MediaContainer"]["Video"]
                                if p:
                                    if p["Player"]["@state"] == "playing":
                                        # If an episode, show the season and episode along with show name
                                        # Ensure that the name doesn't hit the character limit, limiting it to 112 characters
                                        if p["@type"] == "episode":
                                            payload.state = f"{p['@grandparentTitle'][:104]} S{p['@parentIndex']} E{p['@index']}"
                                        elif p["@type"] == "movie":  # Otherwise, just show the movie name
                                            payload.state = f"{p['@title']}"[:112]
                                        # Set unix time of start/end time
                                        if self.config["use_time_left_media"] == True:
                                            payload.end = int(
                                                time() + (int(p["@duration"])/1000 - (int(p["@viewOffset"])/1000)))
                                        else:
                                            payload.start = int(
                                                time() - (int(p["@viewOffset"])/1000))
                                        # And finally set small icon and client ID, since we know everything else worked
                                        payload.small_image = self.config["plex_icon"]
                                        client_id = self.config["plex_cid"]
                        except KeyError as e:
                            self.log.error(self.get_traceback(e))
                    elif r.status_code == 401:
                        self.log.error("Plex token expired")

            ### WEBNOWPLAYING ###

            if WNPRedux.mediaInfo.State == "PLAYING":
                # Check if the player type is defined in the config, so we use their custom client ids/etc
                if WNPRedux.mediaInfo.Player.lower() in self.config["other_media"].keys():
                    client_id = self.config["other_media"][WNPRedux.mediaInfo.Player.lower()]["client_id"]
                    if WNPRedux.mediaInfo.Player.lower() == "youtube":
                        try:
                            video_id = WNPRedux.mediaInfo.CoverUrl.split("/")[-2]
                            if self.vid_is_public.get(video_id) == None:
                                try:
                                    response = get(f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=status&key={self.config['yt_api_key']}")
                                    video = response.json()["items"][0]
                                    is_public = True if video["status"]["privacyStatus"] == "public" else False
                                    self.vid_is_public[video_id] = is_public
                                except KeyError:
                                    is_public = False
                            else:
                                is_public = self.vid_is_public[video_id]
                        except IndexError:
                            is_public = False
                        if is_public:
                            skip = False
                        else:
                            skip = True
                    else:
                        skip = False

                    if not skip:
                        # Run some weird maths to cut off the title if it is too long, while ensuring the artist length won't make it too long
                        if len(f"{WNPRedux.mediaInfo.Title} - {WNPRedux.mediaInfo.Artist}") > 128:
                            payload.state = f"{WNPRedux.mediaInfo.Title[:-(len(WNPRedux.mediaInfo.Artist)-(128-len(WNPRedux.mediaInfo.Artist)-3))]}... - {WNPRedux.mediaInfo.Artist}"
                        else:
                            payload.state = f"{WNPRedux.mediaInfo.Title} - {WNPRedux.mediaInfo.Artist}"
                        # Set the small image defined for the player
                        payload.small_image = self.config["other_media"][WNPRedux.mediaInfo.Player.lower()]["icon"]
                        # Check is player is twitch, giving a button for other people to click on to join the stream
                        if WNPRedux.mediaInfo.Player == "Twitch":
                            media_button = {
                                "label": "Watch on Twitch", "url": f"https://twitch.tv/{WNPRedux.mediaInfo.Artist.lower()}"}
                            payload.state = f"Watching {WNPRedux.mediaInfo.Artist} on Twitch"
                        # For youtube, parse the cover url to get the video id, and add a button to watch the video
                        elif WNPRedux.mediaInfo.Player.lower() == "youtube":
                            if WNPRedux.mediaInfo.CoverUrl != "":
                                try:
                                    video_id = WNPRedux.mediaInfo.CoverUrl.split("/")[-2]
                                    media_button = {
                                        "label": "Watch on Youtube", "url": f"https://youtube.com/watch?v={video_id}"}
                                except (IndexError, KeyError):
                                    pass

                        if self.config["use_time_left_media"]:
                            payload.end = int(time() + (WNPRedux.mediaInfo.PositionSeconds - WNPRedux.mediaInfo.PositionSeconds))
                        else:
                            payload.start = int(time() - WNPRedux.mediaInfo.PositionSeconds)
                    else:
                        self.log.info(f"Not including YouTube video {video_id} as video is not public")

        ### GAMES ###
        
        if self.config["show_games"]:  # If we want any games to show
            processes.pop("vlc.exe", None)
            processes.pop("Plex.exe", None)
            if processes != {}:
                # Sort processes in order of oldest to newest using their PID
                sorted_processes = sorted([p for p in list(
                    processes.values())], key=lambda p: p["object"].pid, reverse=True)
                process = sorted_processes[0]
                process_info = process["info"]
                # If no client ID is provided, we want to disconnect the RPC instead
                process_info["client_id"] = process_info["client_id"] or NoRPC
                # Only log if the client ID has changed
                if self.prev_cid != process_info["client_id"]:
                    self.log.debug(
                        f"Matched process {process['object'].name()} to client ID {process_info['client_id']} with name {process_info['name']}")
                try:
                    # Fetch how long the process has been running, so we can put it into the RPC.
                    create_time = process["object"].create_time()
                except OSError:
                    # system processes, using boot time instead
                    create_time = boot_time()
                epoch = time() - create_time  # Then format it into a human reable format
                conv = {
                    "days": str(epoch // 86400).split('.')[0],
                    "hours": str(epoch // 3600 % 24).split('.')[0],
                    "minutes": str(epoch // 60 % 60).split('.')[0],
                    "seconds": str(epoch % 60).split('.')[0],
                    "full": strftime('%Y-%m-%d %I:%M:%S %p %Z', localtime(create_time))
                }
                time_info = f"for {conv['days'] if conv['days'] != '0' else ''}{'' if conv['days'] == '0' else 'd, '}{conv['hours'] if conv['hours'] != '0' else ''}{'' if conv['hours'] == '0' else 'h, '}{conv['minutes'] if conv['minutes'] != '0' else ''}{'' if conv['minutes'] == '0' else 'm'}"

                # Everything worked, set the client id
                client_id = process_info["client_id"]
                payload.details = f"{time_info}"
                payload.small_image = process_info.get("icon", None)

        if media_button is not None:
            payload.add_button(media_button)
        if extra_button is not None:
            payload.add_button(extra_button)

        return client_id, payload

    def main(self):
        # Fetch what Client ID we should be using, and the payload data
        client_id, payload = self.get_payload()
        if self.prev_cid != client_id:
            self.log.info(f"Switching from {self.prev_cid} to {client_id}")
            # We changed client ID, reconnect the RPC with the new client ID
            self.prev_cid = client_id
            if client_id != NoRPC:
                self.reconnect(client_id=client_id)
            else:
                if self.connected:  # If we don't have a client ID, just clear the presence
                    self.RPC.clear()
        # If for some reason the RPC isn't connected and we have a client id, connect
        if not self.connected and client_id != NoRPC:
            self.reconnect(client_id=client_id)
        # Check if payloads are the same, and if not, push and update
        if not self.same_payload(payload) or self.last_update+300 < time():
            self.previous_payload = payload
            self.log.debug(f"Setting presence with payload {json.dumps(payload.to_dict(), indent=4)}")
            if client_id != NoRPC:
                while True:
                    try:
                        self.RPC.update(**payload.to_dict())
                        self.last_update = time()
                    # Errors usually occur if discord is restarted or killed and we try to update the RPC,
                    # and since we don't have any other way to check, this is where the errors happen
                    except InvalidID:
                        self.log.warning("Invalid ID, restarting...")
                        self.reconnect(client_id=client_id)
                    except InvalidPipe:
                        self.log.warning(
                            "InvalidPipe, is discord running? Reconnecting...")
                        self.reconnect(client_id=client_id)
                    else:
                        break
            # Sleep for 15 seconds, since we can only update the rich presence every 15 seconds
            sleep(15)
        else:
            self.log.debug("Ignoring same payload")
            # We don't want to constantly try fetch a new payload if nothing has changed, so only sleep for 5 seconds
            sleep(5)
        try:
            # Reread the config file to see if it has been updated, ignore if errors
            with open("config.json") as f:
                self.config = json.load(f)
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            self.log.warning(f"Error reading config file {e}")

    # Properly shutdown the rich presence, disconnecting cleanly. Not sure if this even works
    def close(self, signal, frame):
        self.log.info("Stopping...")
        try:
            self.RPC.close()
            WNPRedux.Close()
        except AttributeError:
            pass
        sys.exit()

    def get_traceback(self, e: Exception) -> str:
        return "Traceback (most recent call last):\n" + ''.join(format_tb(e.__traceback__)) + f"{type(e).__name__}: {e}"


if __name__ == "__main__":
    rpc = CustomRPC()
    while True:
        try:
            rpc.main()
        except Exception as e:  # If any exceptions occur, try log them
            rpc.log.error(rpc.get_traceback(e))
