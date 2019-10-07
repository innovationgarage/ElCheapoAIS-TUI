#! /usr/bin/python

import sys
import os
import serial
import datetime

SCREENW=32
SCREENH=9

empty_screen = "\n".join([" " * SCREENW] * SCREENH)


def sopen():
    global term
    term = serial.Serial(os.environ.get("TTGOTERM", "/dev/ttyUSB0"), baudrate=int(os.environ.get("TTGOTERM_SPEED", 115200)), timeout=3.0)

sopen()

def rd():
    while True:
        try:
            return term.read(1)
        except Exception as e:
            print(e)
            time.sleep(0.1)
            try:
                sopen()
            except:
                pass

def wr(s):
    while True:
        try:
            return term.write(s)
        except Exception as e:
            print(e)
            time.sleep(0.1)
            try:
                sopen()
            except:
                pass
    
class Menu(object):
    def __init__(self, entries):
        self.entries = entries

    def run(self):
        self.display()
        res = self.handle_input()
        action = "action_%s" % res
        if hasattr(self, action):
            return getattr(self, action)()
        else:
            return res
        
    def display(self):
        wr(b"\x1bc\x1b[2J")
        wr(b"*" * SCREENW + b"\r\n")
        for entry in self.entries:
            wr(b"*" + (b" " * (SCREENW-2)) + b"*" + b"\r\n")
        wr(b"*" * SCREENW + b"\r\n")
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
        self.displaying = False

    def run(self):
        try:
            self.displaying = True
            self.display()
            res = self.handle_input()
        finally:
            self.displaying = False
        action = "action_%s" % res
        if hasattr(self, action):
            return getattr(self, action)()
        else:
            return res
        
    def display(self):
        wr(b"\x1bc\x1b[2J")
        wr(self.content.replace("\n", "\r\n").encode("utf-8"))
            
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

class Dial(object):
    def __init__(self, label, value, inc=1):
        self.y = len(label.split("\n"))
        self.x = len(label.split("\n")[-1]) + 1
        self.label = label.replace("\n", "\r\n").encode("utf-8")
        self.value = value
        self.len = 0
        self.inc = inc
    
    def run(self):
        try:
            self.displaying = True
            self.display()
            self.handle_input()
        finally:
            self.displaying = False
        if hasattr(self, "action"):
            return self.action(self.value)
        else:
            return self.value
            
    def display(self):
        wr(b"\x1bc\x1b[2J")
        wr(self.label)
        self.set_value(self.value)

    def set_value(self, value):
        self.value = value
        if self.displaying:
            wr(b"\x1b[%s;%sH" % (str(self.y).encode("utf-8"), str(self.x).encode("utf-8")))
            s = str(self.value)
            pad = " " * (max(self.len - len(s), 0))
            self.len = len(s)
            wr((s+pad).encode("utf-8"))
            
    def handle_input(self):
        while True:
            c1 = rd()
            if c1 == b"\x1b":
                c2 = rd()
                if c2 == b"[":
                    while True:
                        c3 = rd()
                        if c3 == b"A":
                            self.set_value(self.value + self.inc)
                            break
                        elif c3 == b"B":
                            self.set_value(self.value - self.inc)
                            break
            elif c1 == b"\n" or c1 == b"\r":
                return

class TextEntry(object):
    def __init__(self, label, value=""):
        self.y = len(label.split("\n"))
        self.x = len(label.split("\n")[-1]) + 1
        self.label = label.replace("\n", "\r\n").encode("utf-8")
        self.value = value
    
    def run(self):
        try:
            self.displaying = True
            self.display()
            self.handle_input()
        finally:
            self.displaying = False
        if hasattr(self, "action"):
            return self.action(self.value)
        else:
            return self.value
            
    def display(self):
        wr(b"\x1bc\x1b[2J")
        wr(self.label)
        self.set_value(self.value)

    def set_value(self, value):
        self.value = value
        if self.displaying:
            wr(b"\x1b[%s;%sH" % (str(self.y).encode("utf-8"), str(self.x).encode("utf-8")))
            wr(self.value.encode("utf-8"))
            
    def handle_input(self):
        while True:
            c1 = rd()
            if c1 == b"\n" or c1 == b"\r":
                return
            elif c1 == b"\b":
                self.value = self.value[:-1]
                wr(b"\x1b[%s;%sH " % (str(self.y).encode("utf-8"), str(self.x + len(self.value)).encode("utf-8")))
            else:
                self.value = self.value + c1.decode("utf-8")
                wr(b"\x1b[%s;%sH%s" % (str(self.y).encode("utf-8"), str(self.x + len(self.value) - 1).encode("utf-8"), c1))


class TextScroll(object):
    def __init__(self, content):
        self.content = []
        for line in content.split("\n"):
            while line:
                self.content.append(line[:SCREENW])
                line = line[SCREENW:]
        self.pos = 0
    
    def run(self):
        self.display()
        self.handle_input()
        if hasattr(self, "action"):
            return self.action()
        else:
            return True
            
    def display(self):
        wr(b"\x1bc\x1b[2J")
        lines = self.content[self.pos:self.pos + SCREENH]
        for line in lines:
            wr(line.encode("utf-8") + b"\r\n")

    def handle_input(self):
        while True:
            c1 = rd()
            if c1 == b"\x1b":
                c2 = rd()
                if c2 == b"[":
                    while True:
                        c3 = rd()
                        if c3 == b"A":
                            self.display()
                            self.pos = max(self.pos - 1, 0)
                            break
                        elif c3 == b"B":
                            self.pos = min(self.pos + 1, len(self.content) - SCREENH)
                            self.display()
                            break
            elif c1 == b"\n" or c1 == b"\r":
                return

