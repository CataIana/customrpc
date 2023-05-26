#!/usr/bin/env python3

import asyncio
from websockets import client as wclient
from websockets.exceptions import ConnectionClosed
import sys
import json
import logging

class ConfigError(Exception):
    pass


class PubSubLogging:
    def __init__(self):
        self.logging = logging.getLogger()
        self.logging.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(module)s %(funcName)s %(lineno)d]: %(message)s", "%Y-%m-%d %I:%M:%S%p")

        # Console logging
        chandler = logging.StreamHandler(sys.stdout)
        chandler.setLevel(self.logging.level)
        chandler.setFormatter(formatter)
        self.logging.addHandler(chandler)

        self._tasks: list[asyncio.Task] = []

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.main())

    async def main(self):
        while True:  # Tasks will finish if connection is closed, loop ensures everything reconnects
            failed_attempts = 0
            while True:  # Not sure if it works, but an attempt at a connecting backoff, using while True since self.connection isn't defined yet
                self.connection = await wclient.connect(f"ws://localhost:2946/BSDataPuller/MapData")
                if self.connection.closed:
                    if 2**failed_attempts > 128:
                        await asyncio.sleep(120)
                    else:
                        await asyncio.sleep(2**failed_attempts)
                    failed_attempts += 1 # Continue to back off exponentially with every failed connection attempt up to 2 minutes
                    self.logging.warning(
                        f"{failed_attempts} failed attempts to connect.")
                else:
                    break
            self.logging.info("Connected to websocket")
            self._tasks = [
                self.loop.create_task(self.message_reciever())
            ]
            try:
                await asyncio.wait(self._tasks) # Tasks will run until the connection closes, we need to re-establish it if it closes
            except asyncio.exceptions.CancelledError:
                pass
            self.logging.info("Reconnecting")

    async def message_reciever(self):
        while not self.connection.closed:
            try:
                message = json.loads(await self.connection.recv())
                print(json.dumps(message, indent=4))
            except ConnectionClosed:
                self.logging.warning("Connection with server closed")
        [task.cancel() for task in self._tasks if task is not asyncio.tasks.current_task()]

if __name__ == "__main__":
    p = PubSubLogging()
    p.run()
