import logging
from os import path, getcwd

def getLogger(level):
    log = logging.getLogger("RPC UI")
    log.setLevel(level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(module)s %(funcName)s %(lineno)d]: %(message)s", "%Y-%m-%d %I:%M:%S%p")

    ch = logging.StreamHandler()
    ch.setLevel(level)
    
    ch.setFormatter(formatter)
    log.addHandler(ch)
    
    try:
        root = path.dirname(path.realpath(__file__))
    except NameError:
        root = getcwd()
    fh = logging.FileHandler(f"{root}\\log.log")
    fh.setLevel(level)
    
    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log