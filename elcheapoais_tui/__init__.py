#! /usr/bin/python

import sys
import os
import serial
import threading
import datetime
from . import screen
from . import monitor_ip
import time

def dbg(s):
    sys.stderr.write(s + "\n")
    sys.stderr.flush()

def strw(s, x, y, c):
    y -= 1
    x -= 1
    lines = s.split("\n")
    return "\n".join(lines[:y] + [lines[y][:x] + c + lines[y][x+len(c):]] + lines[y+1:])
    
class MainScreen(screen.DisplayScreen):
    def __init__(self):
        s = screen.empty_screen
        s = strw(s, 1, 1, "MMSI:")
        s = strw(s, 1, 2, "IP:")
        s = strw(s, 1, 3, "Lat:")
        s = strw(s, 1, 4, "Lon:")
        s = strw(s, 1, 5, "Last pos:")

        s = strw(s, 1, screen.SCREENH, "CFG")
        s = strw(s, screen.SCREENW//2-1, screen.SCREENH, "CAT")    
        s = strw(s, screen.SCREENW-2, screen.SCREENH, "DBG")

        self.nmea = False
        self.net = False
        self.ip = "192.168.4.36"
        self.mmsi = "257098740"
        self.lat = 4.12345
        self.lon = 40.33218
        self.time = datetime.datetime.now()
        
        screen.DisplayScreen.__init__(self, s)

    def display(self):
        screen.DisplayScreen.display(self)
        self.set_nmea(self.nmea)
        self.set_net(self.net)
        self.set_mmsi(self.mmsi)
        self.set_ip(self.ip)
        self.set_latlon(self.lat, self.lon, self.time)
        
    def set_nmea(self, up):
        self.nmea = up
        if self.displaying:
            screen.wr(b"\x1b[1;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + (b"  UP" if up else b"DOWN"))
                
    def set_net(self, up):
        self.net = up
        if self.displaying:
            screen.wr(b"\x1b[2;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + (b"  UP" if up else b"DOWN"))
            
    def set_mmsi(self, mmsi):
        self.mmsi = mmsi
        if self.displaying:
            screen.wr(b"\x1b[1;7H" + b" " * 9)
            screen.wr(b"\x1b[1;7H" + mmsi.encode("utf-8"))

    def set_ip(self, ip):
        self.ip = ip
        if self.displaying:
            screen.wr(b"\x1b[2;5H" + strw(" " * 15, 1, 1, (ip or "")).encode("utf-8"))

    def set_latlon(self, lat, lon, time=None):
        self.lat = lat
        self.lon = lon
        if lat is not None and lon is not None:
            self.set_nmea(True)
            if time is None:
                time = datetime.datetime.now()
            self.time = time
        else:
            self.set_nmea(False)
        if self.displaying:
            screen.wr(b"\x1b[3;6H" + strw(" " * (screen.SCREENW-6), 1, 1, str(lat) if lat is not None else "").encode("utf-8"))
            screen.wr(b"\x1b[4;6H" + strw(" " * (screen.SCREENW-6), 1, 1, str(lon) if lon is not None else "").encode("utf-8"))
            screen.wr(b"\x1b[5;11H" + strw(" " * (screen.SCREENW-11), 1, 1,
                                           self.time.strftime("%Y-%m-%d %H:%M:%S")
                                           if lat is not None and lon is not None
                                           else b"No positions received").encode("utf-8"))

    def action_0(self):
        return config_screen
    def action_1(self):
        return cat_screen
    def action_2(self):
        return debug_screen
    
class ConfigMenu(screen.Menu):
    def __init__(self):
        screen.Menu.__init__(self, [
            "Back",
            "Msgs/min: 100",
            "Msgs/min/mmsi: 10",
        ])
        
    def action_0(self):
        return main_screen
    def action_1(self):
        return main_screen
    def action_2(self):
        return main_screen

class DebugMenu(screen.Menu):
    def __init__(self):
        screen.Menu.__init__(self, [
            "Back",
            "Ping server",
            "Show last msg",
            "Filesystem status"
        ])
        
    def action_0(self):
        return main_screen
    def action_1(self):
        return main_screen
    def action_2(self):
        return main_screen
    def action_3(self):
        return main_screen

class CatScreen(screen.DisplayScreen):
    def __init__(self):
        s = screen.empty_screen
        cat = r"""       _..---..,""-._     ,/}/)
    .''       ,      ``..'(/-<
   /   _     {      )         \
  ;   _ `.    `.   <         a(
 /   ( \  )     `.  \ __.._ .: y
( <\_-) )'-.___...\  `._   //-'
 \ `-' /-._))      `-._)))
  `...'
"""
#         cat = r"""              _ |\_
#               \` ..\
#          __,.-" =__Y=
#        ."        )
#  _    /   ,    \/\_
# ((____|    )_-\ \_-`
# `-----'`-----` `--`
# """
        for idx, line in enumerate(cat.split("\n")):
            s = strw(s, 1, idx+1, line)
        
        screen.DisplayScreen.__init__(self, s)

    def action_0(self):
        return main_screen
    def action_1(self):
        return main_screen
    def action_2(self):
        return main_screen

    
main_screen = MainScreen()
config_screen = ConfigMenu()
debug_screen = DebugMenu()
cat_screen = CatScreen()
current = main_screen

class Screen(threading.Thread):
    def run(self):
        global current
        while current:
            current = current.run()
            print("XXXXXXXXXXXXX", current)

class Status(threading.Thread):
    def run(self):
        for line in sys.stdin:
            eval(line)

class IpStatus(threading.Thread):
    def run(self):
        while True:
            current_ip = None
            for ip in monitor_ip.get_ips():
                if ip != '127.0.0.1':
                    current_ip = ip
            main_screen.set_ip(current_ip)
            time.sleep(1)
        
def main():
    Screen().start()
    Status().start()
    IpStatus().start()
