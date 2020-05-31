import tkinter as tk
from tkinter import ttk
from subprocess import Popen, PIPE
from os import getcwd
from json import load as j_load
from json import dumps as j_print

def _from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return "#%02x%02x%02x" % rgb

class RPCAddGame():
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('RPC Add Program')
        self.window.geometry('450x250')
        self.window.resizable(False, False)
        #self.window.overrideredirect(1)
        bg = _from_rgb((25, 25, 25))
        font_color = _from_rgb((200, 200, 200))
        self.window.configure(bg=bg)

        font = "Segoe UI"

        tk.Label(self.window, text = "Add program to gamelist", foreground=font_color, background=bg, font=(font, 15)).grid(row=0, column=1)
        tk.Label(self.window, text="Select Program :", foreground=font_color, background=bg, font=(font, 10)).grid(column = 0, row=5, padx=10, pady=15)
        tk.Label(self.window, text="Realname: ", foreground=font_color, background=bg, font=(font, 10)).grid(column = 0, row=15, padx=10, pady=15)
        tk.Button(self.window, text="Open gamelist", highlightbackground=bg, foreground=font_color, background=bg, font=(font, 9), command=self.opengamelist).grid(column=1, row=26)

        style = ttk.Style()

        #style.map('TCombobox', fieldbackground=[("readonly", bg)])
        style.map('TCombobox', selectbackground=[("readonly", bg)])
        style.map('TCombobox', selectforeground=[("readonly", font_color)])
        style.map('TCombobox', background=[("readonly", "bg")])
        self.window.option_add("*TCombobox*Listbox*Background", bg)
        self.window.option_add("*TCombobox*Listbox*Foreground", font_color)

        self.programchosen = ttk.Combobox(self.window, width=27, textvariable=tk.StringVar(), postcommand=self.refreshlist, state="readonly")
        self.programchosen.grid(column=1, row=5)
        self.programchosen.current()
        self.programchosen.bind("<<ComboboxSelected>>", self.check_exists)

        self.info_label = tk.Label(self.window, foreground=font_color, background=bg, font=(font, 9), text="")
        self.info_label.grid(column=1, row=30)

        self.realname_entry = tk.Entry(self.window, width=30, foreground=font_color, insertbackground=font_color, background=bg)
        self.realname_entry.grid(column=1, row=15)

        self.add_button = tk.Button(self.window, text="Add program", foreground=font_color, background=bg, font=(font, 9), command=self.add)
        self.add_button.grid(column=1, row=25)

        self.window.mainloop()

    def add(self):
        chosen = self.programchosen.get()
        realname = self.realname_entry.get()
        if chosen != "" and realname != "":
            self.info_label.configure(text=f"Adding {chosen}...")
            with open(f"{getcwd()}\\..\\data\\gamelist.json") as ga:
                gamelist = j_load(ga)
            gamelist[chosen] = realname
            with open(f"{getcwd()}\\..\\data\\gamelist.json", "w") as gw:
                gw.write(j_print(gamelist, indent=4))
            self.info_label.configure(text="Done!")
            self.window.after(1000, lambda: self.info_label.configure(text=""))
        else:
            self.info_label.configure(text="Fill out all boxes!")
            self.window.after(1000, lambda: self.info_label.configure(text=""))

    def check_exists(self):
        chosen = self.programchosen.get()
        with open(f"{getcwd()}\\..\\data\\gamelist.json") as ga:
            gamelist = j_load(ga)
        if chosen in list(gamelist.keys()):
            self.add_button.configure(state="disabled")
            self.info_label.configure(text="Executable already defined!")
        else:
            self.add_button.configure(state="normal")
            self.info_label.configure(text="")

    def opengamelist(self):
        cwd = getcwd().split("\\")
        del cwd[-1]
        cwd.append("data")
        cwd.append("gamelist.json")
        folder = "\\\\".join(cwd)
        Popen(f"start {folder}", shell=True)

    def refreshlist(self):
        exclusions = ["svchost.exe"]
        programlist = [""]

        proc = Popen('WMIC PROCESS get Caption', shell=True, stdout=PIPE)
        for line in proc.stdout:
            a = line.decode().rstrip()
            if len(a) > 0:
                if a not in exclusions:
                    programlist.append(a)
        programlist = sorted(programlist, key=str.casefold)
        self.programchosen['values'] = programlist

RPCAddGame()
