from imports import CustomRPC
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys
from imports._shared_imports import getLogger
from os import path



# class A(QMainWindow):
#     from imports._ui import readConfig 
#     def __init__(self, *args, **kwargs):
#         super(A, self).__init__(*args, **kwargs)
#         self.root = path.dirname(path.abspath(__file__))
#         self.log = getLogger(self, "DEBUG")
#         #self.rpc = RPCController(logger=self.log)
#         #self.rpc.controller()
#         config = self.readConfig()
#         self.rpc = CustomRPC(config["client_id"], logger=self.log) #Initialize rpc script
#         self.rpc.mainLoop()


# if __name__ == "__main__":
#     while True:
#         try:
#             app = QApplication(sys.argv) #Create application
#             window = A() #Init window
#             sys.exit(app.exec_()) #Run process
#         except Exception:
#             pass
from imports._ui import readConfig 

if __name__ == "__main__":
    config = readConfig()
    rpc = CustomRPC(config["client_id"]) #Initialize rpc script
    rpc.mainLoop()