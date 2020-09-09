from cx_Freeze import setup, Executable
from os import listdir, remove, path
from shutil import rmtree as rmdir
from shutil import move
from subprocess import Popen, PIPE
from time import sleep
from sys import platform

exe_name = "rpc"
py_file = "ui.pyw"
donotremove = [
    py_file,
    "imports",
    "rpc icons",
    path.basename(__file__)
]
output = Popen(["taskkill", "/im", f"{exe_name}.exe", "/f"], stdout=PIPE)
sleep(1)

for file in listdir(path.dirname(path.realpath(__file__))):
    if file not in donotremove:
        try:
            remove(f"{path.dirname(path.realpath(__file__))}\\{file}")
        except PermissionError:
            rmdir(f"{path.dirname(path.realpath(__file__))}\\{file}")

buildOptions = dict(packages = [], excludes = [], includes=[], include_files=[])

base = "Win32GUI" if platform == "win32" else None
#base = 'Win32Service' if platform=='win32' else None
#base = "Console"

executables = [
    Executable(
        py_file,
        base = base,
        targetName = exe_name,
        icon = f"{path.dirname(path.realpath(__file__))}\\..\\icon.ico"
    )
]

setup(name="CustomRPC",
      version = "4.0",
      description = "RPC",
      options = dict(build_exe = buildOptions),
      executables = executables)

builddir = listdir(f"{path.dirname(path.realpath(__file__))}\\build")[0]
for file in listdir(f"{path.dirname(path.realpath(__file__))}\\build\\{builddir}"):
    move(f"{path.dirname(path.realpath(__file__))}\\build\\{builddir}\\{file}", file)
rmdir(f"{path.dirname(path.realpath(__file__))}\\build")