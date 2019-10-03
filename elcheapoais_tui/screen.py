#! /usr/bin/python

import sys
import os
import serial
import datetime

SCREENW=32
SCREENH=9

empty_screen = "\n".join([" " * SCREENW] * SCREENH)


term = serial.Serial(os.environ.get("TTGOTERM", "/dev/ttyUSB0"), baudrate=int(os.environ.get("TTGOTERM_SPEED", 9600)), timeout=3.0)

def rd():
    return term.read(1)
def wr(s):
    term.write(s)
    
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
