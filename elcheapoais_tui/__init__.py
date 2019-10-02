#! /usr/bin/python

import sys
import os
import serial

SCREENW=32
SCREENH=9

empty_screen = "\n".join([" " * SCREENW] * SCREENH)


term = serial.Serial(os.environ.get("TTGOTERM", "/dev/ttyUSB0"), baudrate=int(os.environ.get("TTGOTERM_SPEED", 9600)), timeout=3.0)

def rd():
    return term.read(1)
def wr(s):
    term.write(s)
def dbg(s):
    sys.stderr.write(s + "\n")
    sys.stderr.flush()

def strw(s, x, y, c):
    y -= 1
    x -= 1
    lines = s.split("\n")
    return "\n".join(lines[:y] + [lines[y][:x] + c + lines[y][x+len(c):]] + lines[y+1:])

    
class Menu(object):
    def __init__(self, entries):
        self.entries = entries

    def run(self):
        self.display()
        return self.handle_input()
        
    def display(self):
        wr(b"\x1bc")
        wr(b"*" * SCREENW)
        for entry in self.entries:
            wr(b"*" + (b" " * (SCREENW-2)) + b"*")
        wr(b"*" * SCREENW)
        for idx, entry in enumerate(self.entries):
            wr(b"\x1b[%s;3H%s" % (str(idx + 2).encode("utf-8"), entry.encode("utf-8")))

    def move(self, direction):
        wr(b"\x1b[%s;2H " % ((str(self.pos + 2).encode("utf-8"))))
        self.pos += direction
        if self.pos < 0:
            self.pos = 0
        if self.pos >= len(self.entries):
            self.pos = len(self.entries) - 1
        wr(b"\x1b[%s;2H>" % ((str(self.pos + 2).encode("utf-8"))))
            
    def handle_input(self):
        self.pos = 0
        self.move(0)

        while True:
            c1 = rd()
            if c1 == b"\x1b":
                c2 = rd()
                if c2 == b"[":
                    while True:
                        c3 = rd()
                        if c3 == b"A":
                            self.move(-1)
                            break
                        elif c3 == b"B":
                            self.move(1)
                            break
            elif c1 == b"\n" or c1 == b"\r":
                return self.pos
        return self.pos

class DisplayScreen(object):
    def __init__(self, content):
        self.content = content

    def run(self):
        self.display()
        return self.handle_input()
        
    def display(self):
        wr(b"\x1bc")
        wr(self.content.encode("utf-8"))
            
    def handle_input(self):
        while True:
            c1 = rd()
            if c1 == b"\x1b":
                c2 = rd()
                if c2 == b"[":
                    while True:
                        c3 = rd()
                        if c3 == b"A":
                            return 0
                        elif c3 == b"B":
                            return 2
            elif c1 == b"\n" or c1 == b"\r":
                return 1
        return self.pos

class MainScreen(DisplayScreen):
    def __init__(self):
        s = empty_screen
        s = strw(s, 1, 1, "MMSI: 257098740")
        s = strw(s, 1, 2, "IP: 192.168.4.36")
        s = strw(s, 1, 3, "Lat: 69.65143")
        s = strw(s, 1, 4, "Lon: 18.96868")
        s = strw(s, 1, 5, "Last msg: 2019-10-02 15:17:01")

        s = strw(s, 1, SCREENH, "CFG")
        s = strw(s, SCREENW//2-1, SCREENH, "EXT")    
        s = strw(s, SCREENW-2, SCREENH, "DBG")

        s = strw(s, SCREENW-1, 1, "UP")
        s = strw(s, SCREENW-1, 2, "UP")
        DisplayScreen.__init__(self, s)

    def run(self):
        return getattr(self, "action_%s" % DisplayScreen.run(self))()

    def action_0(self):
        return config_screen
    def action_1(self):
        return None
    def action_2(self):
        return debug_screen
    
class ConfigMenu(Menu):
    def __init__(self):
        Menu.__init__(self, [
            "Back",
            "Msgs/min: 100",
            "Msgs/min/mmsi: 10",
        ])
        
    def run(self):
        return getattr(self, "action_%s" % Menu.run(self))()

    def action_0(self):
        return main_screen
    def action_1(self):
        return main_screen
    def action_2(self):
        return main_screen

class DebugMenu(Menu):
    def __init__(self):
        Menu.__init__(self, [
            "Back",
            "Ping server",
            "Show last msg",
            "Filesystem status"
        ])
        
    def run(self):
        return getattr(self, "action_%s" % Menu.run(self))()

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

def main():
    current = main_screen
    while current:
        current = current.run()
