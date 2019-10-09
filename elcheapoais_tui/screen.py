#! /usr/bin/python

import sys
import os
import serial
import datetime
import threading
import time

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

def write(s):
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

class Screen(object):
    def __init__(self, **properties):
        self.writegroup = threading.RLock()
        self.properties = properties
        self.displaying = False
        
    def wr(self, s):
        if self.displaying:
            with self.writegroup:
                write(s)
            
    def run(self):
        self.displaying = True
        with self.writegroup:
            self.display()
            for name, value in self.properties.items():
                self._display_property(name, value)
        res = self.handle_input()
        self.displaying = False
        return self.action(res)

    def action(self, value):
        action = "action_%s" % value
        if hasattr(self, action):
            return getattr(self, action)()
        else:
            return res

    def __setitem__(self, name, value):
        self.properties[name] = value
        self._display_property(name, value)
        notify = "updated_%s" % name
        if hasattr(self, notify):
            getattr(self, notify)(value)

    def __getitem__(self, name):
        return self.properties[name]        

    def _display_property(self, name, value):
        if not self.displaying: return
        renderer = "display_%s" % name
        if hasattr(self, renderer):
            with self.writegroup:
                getattr(self, renderer)(value)
                
class Menu(Screen):
    def __init__(self, entries, **properties):
        Screen.__init__(self, **properties)
        self.entries = entries

    def display(self):
        self.wr(b"\x1bc\x1b[2J")
        self.wr(b"*" * SCREENW + b"\r\n")
        for entry in self.entries:
            self.wr(b"*" + (b" " * (SCREENW-2)) + b"*" + b"\r\n")
        self.wr(b"*" * SCREENW + b"\r\n")
        for idx, entry in enumerate(self.entries):
            self.wr(b"\x1b[%s;3H%s" % (str(idx + 2).encode("utf-8"), entry.encode("utf-8")))

    def move(self, direction):
        self.wr(b"\x1b[%s;2H " % ((str(self.pos + 2).encode("utf-8"))))
        self.pos += direction
        if self.pos < 0:
            self.pos = 0
        if self.pos >= len(self.entries):
            self.pos = len(self.entries) - 1
        self.wr(b"\x1b[%s;2H>" % ((str(self.pos + 2).encode("utf-8"))))
            
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

class DisplayScreen(Screen):
    def __init__(self, content, **properties):
        Screen.__init__(self, **properties)
        self.content = content
        self.displaying = False

    def display(self):
        self.wr(b"\x1bc\x1b[2J")
        self.wr(self.content.replace("\n", "\r\n").encode("utf-8"))
            
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

class Dial(Screen):
    def __init__(self, label, value, inc=1, **properties):
        Screen.__init__(self, value=value, **properties)
        self.y = len(label.split("\n"))
        self.x = len(label.split("\n")[-1]) + 1
        self.label = label.replace("\n", "\r\n").encode("utf-8")
        self.len = 0
        self.inc = inc
    
    def display(self):
        self.wr(b"\x1bc\x1b[2J")
        self.wr(self.label)

    def display_value(self, value):
        self.wr(b"\x1b[%s;%sH" % (str(self.y).encode("utf-8"), str(self.x).encode("utf-8")))
        s = str(value)
        pad = " " * (max(self.len - len(s), 0))
        self.len = len(s)
        self.wr((s+pad).encode("utf-8"))
            
    def handle_input(self):
        while True:
            c1 = rd()
            if c1 == b"\x1b":
                c2 = rd()
                if c2 == b"[":
                    while True:
                        c3 = rd()
                        if c3 == b"A":
                            self["value"] = self["value"] + self.inc
                            break
                        elif c3 == b"B":
                            self["value"] = self["value"] - self.inc
                            break
            elif c1 == b"\n" or c1 == b"\r":
                return self["value"]

class TextEntry(Screen):
    def __init__(self, label, value="", **properties):
        Screen.__init__(self, **properties)
        self.y = len(label.split("\n"))
        self.x = len(label.split("\n")[-1]) + 1
        self.label = label.replace("\n", "\r\n").encode("utf-8")
        self.value = value
    
    def display(self):
        self.wr(b"\x1bc\x1b[2J")
        self.wr(self.label)
        self.set_value(self.value)

    def set_value(self, value):
        self.value = value
        if self.displaying:
            self.wr(b"\x1b[%s;%sH" % (str(self.y).encode("utf-8"), str(self.x).encode("utf-8")))
            self.wr(self.value.encode("utf-8"))
            
    def handle_input(self):
        while True:
            c1 = rd()
            if c1 == b"\n" or c1 == b"\r":
                return self.value
            elif c1 == b"\b":
                self.value = self.value[:-1]
                self.wr(b"\x1b[%s;%sH " % (str(self.y).encode("utf-8"), str(self.x + len(self.value)).encode("utf-8")))
            else:
                self.value = self.value + c1.decode("utf-8")
                self.wr(b"\x1b[%s;%sH%s" % (str(self.y).encode("utf-8"), str(self.x + len(self.value) - 1).encode("utf-8"), c1))


class TextScroll(Screen):
    def __init__(self, content, **properties):
        self.content = []
        for line in content.split("\n"):
            while line:
                self.content.append(line[:SCREENW])
                line = line[SCREENW:]
        self.pos = 0
        Screen.__init__(self, **properties)

    def display(self):
        self.wr(b"\x1bc\x1b[2J")
        lines = self.content[self.pos:self.pos + SCREENH]
        for line in lines:
            self.wr(line.encode("utf-8") + b"\r\n")

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
                return 0

