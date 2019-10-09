#! /usr/bin/python

import sys
import os
import serial
import threading
import datetime
from . import screen
from . import monitor_ip
from . import dbus_receiver
import time
import subprocess
import time
import re
import traceback
import termios

def dbg(s):
    sys.stderr.write(s + "\n")
    sys.stderr.flush()

def strw(s, x, y, c):
    y -= 1
    x -= 1
    lines = s.split("\n")
    return "\n".join(lines[:y] + [lines[y][:x] + c + lines[y][x+len(c):]] + lines[y+1:])
    
class MainScreen(screen.DisplayScreen):
    def __init__(self, tui):
        self.tui = tui
        
        s = screen.empty_screen
        s = strw(s, 1, 1, "MMSI:")
        s = strw(s, 1, 2, "IP:")
        s = strw(s, 1, 3, "Lat:")
        s = strw(s, 1, 4, "Lon:")
        s = strw(s, 1, 5, "Last pos:")

        s = strw(s, 1, screen.SCREENH, "CFG")
        s = strw(s, screen.SCREENW//2-1, screen.SCREENH, "CAT")    
        s = strw(s, screen.SCREENW-2, screen.SCREENH, "DBG")

        screen.DisplayScreen.__init__(self, s)
        
        self["nmea"] = False
        self["net"] = False
        self["ip"] = "192.168.4.36"
        self["mmsi"] = "257098740"
        self["latlon"] = (4.12345, 40.33218)
        self["time"] = datetime.datetime.now()

    def display(self):
        screen.DisplayScreen.display(self)

    def display_nmea(self, up):
        self.wr(b"\x1b[1;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + (b"  UP" if up else b"DOWN"))
                
    def display_net(self, up):
        self.wr(b"\x1b[2;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + (b"  UP" if up else b"DOWN"))
            
    def display_mmsi(self, mmsi):
        self.wr(b"\x1b[1;7H" + b" " * 9)
        self.wr(b"\x1b[1;7H" + mmsi.encode("utf-8"))

    def display_ip(self, ip):
        self.wr(b"\x1b[2;5H" + strw(" " * 15, 1, 1, (ip or "")).encode("utf-8"))

    def updated_latlon(self, value):
        if value is not None:
            self["nmea"] = True
            self["time"] = datetime.datetime.now()
        else:
            self["nmea"] = False
        
    def display_latlon(self, value):
        if value is not None:
            lat, lon = value
        else:
            lat = lon = ""
        self.wr(b"\x1b[3;6H" + strw(" " * (screen.SCREENW-6), 1, 1, str(lat) if lat is not None else "").encode("utf-8"))
        self.wr(b"\x1b[4;6H" + strw(" " * (screen.SCREENW-6), 1, 1, str(lon) if lon is not None else "").encode("utf-8"))
        
    def display_time(self, value):
        self.wr(b"\x1b[5;11H" + strw(" " * (screen.SCREENW-11), 1, 1,
                                     value.strftime("%Y-%m-%d %H:%M:%S")
                                     if self["latlon"] is not None
                                     else "No positions received").encode("utf-8"))

    def action_0(self):
        return self.tui.config_screen
    def action_1(self):
        return self.tui.cat_screen
    def action_2(self):
        return self.tui.debug_screen
    
class ConfigMenu(screen.Menu):
    def __init__(self, tui):
        self.tui = tui
        screen.Menu.__init__(self, [
            "Back",
            "Msgs/min:",
            "Msgs/min/mmsi:",
        ], msgs_per_min = 100, msgs_per_min_per_mmsi=10)

    def display_msgs_per_min(self, value):
        self.wr(b"\x1b[3;13H" + strw(" " * (screen.SCREENW-13), 1, 1, str(value)).encode("utf-8"))
        
    def display_msgs_per_min_per_mmsi(self, value):
        self.wr(b"\x1b[4;18H" + strw(" " * (screen.SCREENW-19), 1, 1, str(value)).encode("utf-8"))
        
    def action_0(self):
        return self.tui.main_screen
    def action_1(self):
        self.tui.msgs_min_screen["value"] = self["msgs_per_min"]
        return self.tui.msgs_min_screen
    def action_2(self):
        self.tui.msgs_min_mmsi_screen["value"] = self["msgs_per_min_per_mmsi"]
        return self.tui.msgs_min_mmsi_screen

class DebugMenu(screen.Menu):
    def __init__(self, tui):
        self.tui = tui
        screen.Menu.__init__(self, [
            "Back",
            "Ping server",
            "Show syslog",
            "Shell",
            "Show last msg",
            "Filesystem status"
        ])
        
    def action_0(self):
        return self.tui.main_screen
    def action_1(self):
        return self.tui.ping_screen
    def action_2(self):
        return self.tui.syslog_screen
    def action_3(self):
        return self.tui.shell_screen
    def action_4(self):
        return self.tui.main_screen
    def action_5(self):
        return self.tui.main_screen

class CatScreen(screen.DisplayScreen):
    def __init__(self, tui):
        self.tui = tui
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
        return self.tui.main_screen
    def action_1(self):
        return self.tui.main_screen
    def action_2(self):
        return self.tui.main_screen

class MsgsMinScreen(screen.Dial):
    def __init__(self, tui):
        self.tui = tui
        screen.Dial.__init__(self, "Messages/minute total: ", 100)

    def action(self, value):
        self.tui.config_screen["msgs_per_min"] = value
        return self.tui.config_screen
    
class MsgsMinMmsiScreen(screen.Dial):
    def __init__(self, tui):
        self.tui = tui
        screen.Dial.__init__(self, "Messages/minute/mmsi: ", 10)

    def action(self, value):
        self.tui.config_screen["msgs_per_min_per_mmsi"] = value
        return self.tui.config_screen

class PingScreen(screen.TextEntry):
    def __init__(self, tui):
        self.tui = tui
        screen.TextEntry.__init__(self, "IP/domain to ping:\n", value="8.8.8.8")

    def action(self, value):
        self.tui.pinging_screen.ip = value
        return self.tui.pinging_screen
    
class PingingThread(threading.Thread):
    def __init__(self, screen):
        self.screen = screen
        self.ip = screen.ip
        self.do_quit = False
        self.quit_done = False
        threading.Thread.__init__(self)
    def quit(self):
        self.do_quit = True
        self.proc.kill()
    def run(self):
        self.proc = subprocess.Popen(["ping", self.ip], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while not self.do_quit:
            line = self.proc.stdout.readline()
            line = re.sub(rb"PING ([^ ]*) \([^ ]*\) ([^ ]*) .*", rb"ip \1 \2B", line)
            line = re.sub(rb"([^ ]*) bytes from ([^:]*): icmp_seq=([^ ]*) ttl=([^ ]*) time=([^ ]*) ms", rb"\1B sq=\3 ttl=\4 \5ms", line)
            if not self.do_quit:
                self.screen.wr(line.replace(b"\n", b"\r\n"))

class PingingScreen(screen.DisplayScreen):
    def __init__(self, tui):
        self.tui = tui
        self.ip = ""
        screen.DisplayScreen.__init__(self, "")

    def display(self):
        self.content = "Pinging: %s\n" % self.ip
        screen.DisplayScreen.display(self)
        self.thread = PingingThread(self)
        self.thread.start()
    def action_0(self):
        self.thread.quit()
        return self.tui.debug_screen
    def action_1(self):
        self.thread.quit()
        return self.tui.debug_screen
    def action_2(self):
        self.thread.quit()
        return self.tui.debug_screen

class SyslogScreen(screen.TextScroll):
    def __init__(self, tui):
        self.tui = tui
        with open("/var/log/syslog") as f:
            content = f.read()
        content = content.replace(": ", ":\n")
        screen.TextScroll.__init__(self, content)

    def action(self):
        return self.tui.debug_screen

class ShellScreen(object):
    def __init__(self, tui):
        self.tui = tui
    def run(self):
        fd = screen.term.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[1] = new[1] | termios.ONLCR
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, new)
            subprocess.run("/bin/bash", stdin=fd, stdout=fd, stderr=fd)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

        return self.tui.debug_screen


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
        self.main_screen = MainScreen(self)
        self.config_screen = ConfigMenu(self)
        self.debug_screen = DebugMenu(self)
        self.cat_screen = CatScreen(self)
        self.msgs_min_screen = MsgsMinScreen(self)
        self.msgs_min_mmsi_screen = MsgsMinMmsiScreen(self)
        self.ping_screen = PingScreen(self)
        self.pinging_screen = PingingScreen(self)
        self.syslog_screen = SyslogScreen(self)
        self.shell_screen = ShellScreen(self)
        
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
