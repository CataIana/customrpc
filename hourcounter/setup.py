from cx_Freeze import setup, Executable
from os import listdir, remove, getcwd, path
from shutil import rmtree as rmdir
from shutil import move
from subprocess import Popen, PIPE
from time import sleep
from sys import platform

exe_name = "hourcount"
py_file = "hourcount.py"
donotremove = [
    py_file,
    path.basename(__file__)
]
output = Popen(["taskkill", "/im", f"{exe_name}.exe", "/f"], stdout=PIPE)
sleep(1)

for file in listdir():
    if file not in donotremove:
        try:
            remove(file)
        except PermissionError:
            rmdir(file)


buildOptions = dict(packages = [], excludes = [])

base = 'Win32GUI' if platform=='win32' else None
#base = "Console"

executables = [
    Executable(
        py_file,
        base = base,
        targetName = exe_name,
        icon = "\\".join(getcwd().split('\\')[:-1] + ["\\icon.ico"])
    )
]

setup(name='RPC Hour Counter',
      version = '1.0',
      description = 'RPC Hour Counter',
      options = dict(build_exe = buildOptions),
      executables = executables)

builddir = listdir("build")[0]
for file in listdir(f"build/{builddir}"):
    move(f"build/{builddir}/{file}", file)
rmdir("build")