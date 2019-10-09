#! /usr/bin/python

import sys
import os
import serial
import threading
import datetime
from . import screen
from . import monitor_ip
from . import dbus_receiver
from . import screen_main
from . import screen_config
from . import screen_debug
from . import screen_ping
from . import screen_cat
from . import screen_syslog
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
                
class IpStatusThread(threading.Thread):
    def __init__(self, tui):
        self.tui = tui
        threading.Thread.__init__(self)
    def run(self):
        while True:
            current_ip = None
            for ip in monitor_ip.get_ips():
                if ip != '127.0.0.1':
                    current_ip = ip
            self.tui.main_screen["ip"] = current_ip
            time.sleep(1)
        

class TUI(object):
    def __init__(self):
        self.main_screen = screen_main.MainScreen(self)

        self.config_screen = screen_config.ConfigMenu(self)
        self.msgs_min_screen = screen_config.MsgsMinScreen(self)
        self.msgs_min_mmsi_screen = screen_config.MsgsMinMmsiScreen(self)

        self.cat_screen = screen_cat.CatScreen(self)
        
        self.debug_screen = screen_debug.DebugMenu(self)
        self.ping_screen = screen_ping.PingScreen(self)
        self.pinging_screen = screen_ping.PingingScreen(self)
        self.syslog_screen = screen_syslog.SyslogScreen(self)
        self.shell_screen = screen_shell.ShellScreen(self)
        
        self.current = self.main_screen

        self.screen_thread = ScreenThread(self)
        self.screen_thread.start()
        self.status_thread = StatusThread(self)
        self.status_thread.start()
        self.ip_status_thread = IpStatusThread(self)
        self.ip_status_thread.start()
        self.dbus_thread = dbus_receiver.DBusReceiver(self)
        self.dbus_thread.start()

def main():
    TUI()
