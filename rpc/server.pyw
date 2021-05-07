#!/usr/bin/env python3

import asyncio
import websockets
from json import dumps
from time import time


class WebNowPlaying:
    def __init__(self, port, loop=None):
        # Init variables
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

        start_server = websockets.serve(self.handler, "localhost", port)
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.loop.run_until_complete(start_server)

    def run(self):
        self.loop.run_forever()

    async def handler(self, websocket, path):
        async for message in websocket:
            print(message)
            setattr(self, message.split(":", 1)[0].lower(), message.split(":", 1)[1])
            self.last_update = time()

            dict = {"player": self.player, "state": self.state, "title": self.title, "artist": self.artist, "album": self.album, "duration": self.duration,
                    "position": self.position, "volume": self.volume, "rating": self.rating, "repeat": self.repeat, "shuffle": self.shuffle, "cover": self.cover, "last_update": self.last_update}
            with open("info.json", "w") as f:
                f.write(dumps(dict, indent=4))


w = WebNowPlaying(port=8975)
try:
    w.run()
except KeyboardInterrupt:
    with open("info.json", "w") as f:
        f.write("")
