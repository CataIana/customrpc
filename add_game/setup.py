from cx_Freeze import setup, Executable
from os import listdir, remove
from shutil import rmtree as rmdir
from shutil import move
from subprocess import Popen, PIPE
from time import sleep

exe_name = "add_game"
py_file = "add_game.py"
donotremove = [py_file, "add_game.old.py", "setup.py", "icon.ico"]
output = Popen(["taskkill", "/im", f"{exe_name}.exe", "/f"], stdout=PIPE)
# for line in output.stdout:
#     print(line)
sleep(1)

for file in listdir():
    if file not in donotremove:
        try:
            remove(file)
        except PermissionError:
            rmdir(file)
# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable(
        py_file,
        base = base,
        targetName = exe_name,
        icon = "../icon.ico"
    )
]

setup(name='RPCAddGame',
      version = '2.2',
      description = 'RPC Add Game',
      options = dict(build_exe = buildOptions),
      executables = executables)

builddir = listdir("build")[0]
for file in listdir(f"build/{builddir}"):
    move(f"build/{builddir}/{file}", file)
rmdir("build")