#! /usr/bin/python

import sys
import os
import serial
import threading
import datetime
from . import screen

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
        s = strw(s, screen.SCREENW//2-1, screen.SCREENH, "EXT")    
        s = strw(s, screen.SCREENW-2, screen.SCREENH, "DBG")

        self.nmea = False
        self.net = False
        self.ip = "192.168.4.36"
        self.mmsi = "257098740"
        self.lat = 4.12345
        self.lon = 40.33218
        self.time = datetime.datetime.now()
        
        screen.DisplayScreen.__init__(self, s)

    def run(self):
        return getattr(self, "action_%s" % screen.DisplayScreen.run(self))()

    def display(self):
        screen.DisplayScreen.display(self)
        self.set_nmea(self.nmea)
        self.set_net(self.net)
        self.set_mmsi(self.mmsi)
        self.set_ip(self.ip)
        self.set_latlon(self.lat, self.lon, self.time)
        
    def set_nmea(self, up):
        self.nmea = up
        if up:
            screen.wr(b"\x1b[1;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + b"  UP")
        else:
            screen.wr(b"\x1b[1;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + b"DOWN")

    def set_net(self, up):
        self.net = up
        if up:
            screen.wr(b"\x1b[2;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + b"  UP")
        else:
            screen.wr(b"\x1b[2;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + b"DOWN")
            
    def set_mmsi(self, mmsi):
        self.mmsi = mmsi
        screen.wr(b"\x1b[1;7H" + b" " * 9)
        screen.wr(b"\x1b[1;7H" + mmsi.encode("utf-8"))

    def set_ip(self, ip):
        self.ip = ip
        screen.wr(b"\x1b[2;5H" + b" " * 15)
        screen.wr(b"\x1b[2;5H" + ip.encode("utf-8"))

    def set_latlon(self, lat, lon, time=None):
        self.lat = lat
        self.lon = lon
        screen.wr(b"\x1b[3;6H" + b" " * (screen.SCREENW-6))
        if lat is not None:
            screen.wr(b"\x1b[3;6H" + str(lat).encode("utf-8"))
        screen.wr(b"\x1b[4;6H" + b" " * (screen.SCREENW-6))
        if lon is not None:
            screen.wr(b"\x1b[4;6H" + str(lon).encode("utf-8"))
        screen.wr(b"\x1b[5;11H" + b" " * (screen.SCREENW-11))
        if lat is not None and lon is not None:
            self.set_nmea(True)
            if time is None:
                time = datetime.datetime.now()
            self.time = time
            time = time.strftime("%Y-%m-%d %H:%M:%S")
            screen.wr(b"\x1b[5;11H" + time.encode("utf-8"))
        else:
            self.set_nmea(False)
            screen.wr(b"\x1b[5;11HNo positions received")

    def action_0(self):
        return config_screen
    def action_1(self):
        sys.exit(1)
    def action_2(self):
        return debug_screen
    
class ConfigMenu(screen.Menu):
    def __init__(self):
        screen.Menu.__init__(self, [
            "Back",
            "Msgs/min: 100",
            "Msgs/min/mmsi: 10",
        ])
        
    def run(self):
        return getattr(self, "action_%s" % screen.Menu.run(self))()

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
        
    def run(self):
        return getattr(self, "action_%s" % screen.Menu.run(self))()

    def action_0(self):
        return main_screen
    def action_1(self):
        return main_screen
    def action_2(self):
        return main_screen
    def action_3(self):
        return main_screen
    
main_screen = MainScreen()
config_screen = ConfigMenu()
debug_screen = DebugMenu()
current = main_screen

class Screen(threading.Thread):
    def run(self):
        global current
        while current:
            current = current.run()

class Status(threading.Thread):
    def run(self):
        for line in sys.stdin:
            eval(line)
            
def main():
    Status().start()
    Screen().start()
