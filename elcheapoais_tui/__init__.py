#! /usr/bin/python

import sys
import os
import serial
import threading
import datetime
from . import screen
from . import dbus_receiver
from . import screen_main
from . import screen_config
from . import screen_wifi
from . import screen_debug
from . import screen_ping
from . import screen_cat
from . import screen_directory
from . import screen_shell
import time
import subprocess
import time
import re
import traceback
import termios

def dbg(s):
    sys.stderr.write(s + "\n")
    sys.stderr.flush()



class ScreenThread(threading.Thread):
    def __init__(self, tui):
        self.tui = tui
        threading.Thread.__init__(self)
    def run(self):
        while self.tui.current:
            self.tui.current = self.tui.current.run()
            print("XXXXXXXXXXXXX", self.tui.current)

class StatusThread(threading.Thread):
    def __init__(self, tui):
        self.tui = tui
        threading.Thread.__init__(self)
    def run(self):
        for line in sys.stdin:
            try:
                eval(line)
            except Exception as e:
                print(e)
                traceback.print_exc()
                

class NMEAStatusThread(threading.Thread):
    def __init__(self, tui):
        self.tui = tui
        threading.Thread.__init__(self)
    def run(self):
        while True:
            if (datetime.datetime.now() - self.tui.main_screen["time"]).total_seconds() > 10:
                self.tui.main_screen["nmea"] = False
            time.sleep(1)

                
class TUI(object):
    def __init__(self):
        self.main_screen = screen_main.MainScreen(self)

        self.config_screen = screen_config.ConfigMenu(self)
        self.msgs_min_screen = screen_config.MsgsMinScreen(self)
        self.msgs_min_mmsi_screen = screen_config.MsgsMinMmsiScreen(self)
        self.wifi_screen = screen_wifi.WifiScreen(self)
        self.wifi_password_screen = screen_wifi.PasswordScreen(self)
        
        self.cat_screen = screen_cat.CatScreen(self)
        
        self.debug_screen = screen_debug.DebugMenu(self)
        self.ping_screen = screen_ping.PingScreen(self)
        self.pinging_screen = screen_ping.PingingScreen(self)
        self.directory_screen = screen_directory.DirectoryScreen(self)
        self.file_screen = screen_directory.FileScreen(self)
        self.shell_screen = screen_shell.ShellScreen(self)
        
        self.current = self.main_screen

        self.screen_thread = ScreenThread(self)
        self.status_thread = StatusThread(self)
        self.dbus_thread = dbus_receiver.DBusReceiver(self)
        self.nmea_status_thread = NMEAStatusThread(self)
        
        self.screen_thread.start()
        self.status_thread.start()
        self.dbus_thread.start()        
        self.nmea_status_thread.start()

def main():
    TUI()
