from time import time, sleep
from json.decoder import JSONDecodeError
from json import load as j_load
from random import choice
import spotipy.util as util
from os import getcwd
from psutil import process_iter, boot_time
from spotipy import Spotify, SpotifyException
from pypresence import Presence
from time import localtime, strftime


class CustomRPC():
    def __init__(self):
        with open(f"{getcwd()}/config.json") as f:
            self.config = j_load(f)
        self.client_ids = {"default": 607432133061115928,
                           "spotify": 835138322879479868}
        self.games = self.config["games"]
        self.prev_cid = None
        self.connected = False
        self.previous_payload = None
        self.force_update = True
        self.auth_spotify()

    def auth_spotify(self):
        print("Authorising Spotify")
        token = util.prompt_for_user_token(
            scope="user-read-currently-playing user-read-playback-state", **self.config["spotify"])
        self.sp = Spotify(auth=token)

    def reconnect(self, client_id=None):
        if self.connected:
            self.RPC.close()
            self.connected = False
        if client_id is None:
            print(f"Connecting with Client ID {self.client_ids['default']}")
            self.RPC = Presence(client_id=self.client_ids["default"])
        else:
            print(f"Connecting with Client ID {client_id}")
            self.RPC = Presence(client_id=client_id)
        self.force_update = True
        self.RPC.connect()
        print("Connected")
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
        payload = {
            "details": "uwu hi",
            "state": "mew :3",
            "buttons": [{"label": "I'm testing stuff go away", "url": "https://www.google.com.au"}],
            "large_image": choice(self.config["large_image_names"])
        }
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
                        payload["buttons"][0] = {
                            "label": "Play on Spotify", "url": spotify["item"]["external_urls"]["spotify"]}
                        client_id = self.client_ids["spotify"]
                        if self.config["use_time_left_media"] == True:
                            payload["end"] = time(
                            ) + (int(spotify["item"]["duration_ms"]/1000) - int(spotify["progress_ms"]/1000))
                        else:
                            payload["start"] = int(
                                time() - int(spotify["progress_ms"]/1000))
                    except KeyError:
                        pass
        if self.config["show_games"]:
            processes = [p for p in process_iter(
                ['name', 'status']) if p.name().lower() in self.games.keys()]
            process = processes[0]
            with process.oneshot():
                process_info = self.games[process.name().lower()]
                if self.prev_cid != process_info["client_id"]:
                    print(
                        f"Matched process {process.name()} to client ID {process_info['client_id']} with name {process_info['name']}")
                client_id = process_info["client_id"]
                try:
                    create_time = process.create_time()
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
                payload["details"] = f"{time_info}"
                payload["small_image"] = process_info["icon"]

        return client_id, payload

    def main(self):
        client_id, payload = self.get_payload()
        if self.prev_cid != client_id:
            print(f"Switching from {self.prev_cid} to {client_id}")
            self.prev_cid = client_id
            self.reconnect(client_id=client_id)
        if not self.connected:
            self.reconnect(client_id=client_id)
        if not self.same_payload(payload):
            print(f"Setting presence with payload {payload}")
            self.RPC.update(**payload)  # Can specify up to 2 buttons
            sleep(15)
        else:
            print("Ignoring same payload")
            sleep(5)
        try:
            with open(f"{getcwd()}/config.json") as f:
                self.config = j_load(f)
        except JSONDecodeError:
            print("Error reading config file")
            pass


rpc = CustomRPC()
while True:
    rpc.main()
