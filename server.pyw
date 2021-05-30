#!/usr/bin/env python3

import asyncio
import websockets
from json import dumps
from time import time
import logging
import sys


class Client:
    def __init__(self, id):
        self.id = id
        self.player = None
        self.state = None
        self.title = None
        self.artist = None
        self.album = None
        self.duration = None
        self.position = None
        self.volume = None
        self.rating = None
        self.repeat = None
        self.shuffle = None
        self.cover = None
        self.last_update = time()

    def get_dict(self):
        return {"player": self.player, "state": self.state, "title": self.title, "artist": self.artist, "album": self.album, "duration": self.duration, "position": self.position,
                "volume": self.volume, "rating": self.rating, "repeat": self.repeat, "shuffle": self.shuffle, "cover": self.cover, "last_update": self.last_update}


class WebNowPlaying:
    def __init__(self, port, loop=None):
        self.version = "0.5.0.0"

        self.clients = {}
        self.playing_order = []

        self.format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        self.log_level = logging.DEBUG
        self.log = logging.getLogger("customrpc server")
        self.log.setLevel(self.log_level)

        fhandler = logging.FileHandler(filename="server.log", encoding="utf-8", mode="w+")
        fhandler.setLevel(logging.WARNING)
        fhandler.setFormatter(self.format)
        self.log.addHandler(fhandler)

        chandler = logging.StreamHandler(sys.stdout)                             
        chandler.setLevel(self.log_level)
        chandler.setFormatter(self.format)                                        
        self.log.addHandler(chandler)

        start_server = websockets.serve(self.handler, "localhost", port)
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.loop.run_until_complete(start_server)

    def run(self):
        self.loop.run_forever()

    async def handler(self, websocket, path):
        try:
            async for message in websocket:
                attribute = message.split(":", 1)[0].lower()
                data = message.split(":", 1)[1]
                id = websocket.request_headers["Sec-WebSocket-Key"]

                force_update = False

                if self.clients.get(id, None) is None:
                    self.clients[id] = Client(id=id)
                    await websocket.send(f"Version:{self.version}")
                    self.log.debug(f"Tab opened")

                if attribute == "state":
                    if data == "1" and self.clients[id].state in ["2", None]:
                        self.log.debug(f"Set playing for {self.clients[id].artist}")
                        self.playing_order.append(id)

                if attribute == "state":
                    if data == "2" and self.clients[id].state == "1":
                        self.log.debug(f"Set paused for {self.clients[id].artist}")
                        self.playing_order.remove(id)
                        force_update = True

                setattr(self.clients[id], attribute, data)
                self.clients[id].last_update = time()

                if force_update:
                    await self.update(id=id)

                await self.update()
        except websockets.exceptions.ConnectionClosedError:
            id = websocket.request_headers["Sec-WebSocket-Key"]
            try:
                self.playing_order.remove(id)
            except ValueError:
                pass
            old_tab = self.clients[id].artist
            del self.clients[id]
            if len(self.clients.keys()) > 0:
                recent = list(self.clients.keys())[-1]
                self.log.debug(f"Tab closed for {old_tab}, restoring to {self.clients[recent].artist}")
                await self.update(id=recent)
            else:
                self.log.debug(f"Tab closed for {old_tab}, nothing to restore to")
                with open("info.json", "w") as f:
                    f.write("")


    async def update(self, id=None):
        if self.playing_order != [] or id is not None:
            if id is not None:
                client = self.clients[id]
                self.log.debug(f"Force update for {client.artist}")
            else:
                client = self.clients[self.playing_order[-1]]

            with open("info.json", "w") as f:
                f.write(dumps(client.get_dict(), indent=4))

if __name__ == "__main__":
    w = WebNowPlaying(port=8975)
    try:
        w.run()
    except KeyboardInterrupt:
        pass
    finally:
        with open("info.json", "w") as f: #Clear file on exit
            f.write("")
