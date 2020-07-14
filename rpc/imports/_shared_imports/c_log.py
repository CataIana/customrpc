import logging
from os import path, getcwd

def getLogger(self, level):
    log = logging.getLogger("RPC UI")
    log.setLevel(level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(module)s %(funcName)s %(lineno)d]: %(message)s", "%Y-%m-%d %I:%M:%S%p")

    ch = logging.StreamHandler()
    ch.setLevel(level)

    ch.setFormatter(formatter)
    log.addHandler(ch)

    fh = logging.FileHandler(f"{self.root}\\log.log", "a+", "utf-8")
    fh.setLevel(level)

    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log
