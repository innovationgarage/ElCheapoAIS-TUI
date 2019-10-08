#! /usr/bin/python

import sys
import os
import serial
import threading
import datetime
from . import screen
from . import monitor_ip
import time
import subprocess
import time
import re
import traceback

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
        return config_screen
    def action_1(self):
        return cat_screen
    def action_2(self):
        return debug_screen
    
class ConfigMenu(screen.Menu):
    def __init__(self):
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
        return main_screen
    def action_1(self):
        msgs_min_screen["value"] = self["msgs_per_min"]
        return msgs_min_screen
    def action_2(self):
        msgs_min_mmsi_screen["value"] = self["msgs_per_min_per_mmsi"]
        return msgs_min_mmsi_screen

class DebugMenu(screen.Menu):
    def __init__(self):
        screen.Menu.__init__(self, [
            "Back",
            "Ping server",
            "Show syslog",
            "Shell",
            "Show last msg",
            "Filesystem status"
        ])
        
    def action_0(self):
        return main_screen
    def action_1(self):
        return ping_screen
    def action_2(self):
        return syslog_screen
    def action_3(self):
        return shell_screen
    def action_4(self):
        return main_screen
    def action_5(self):
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

class MsgsMinScreen(screen.Dial):
    def __init__(self):
        screen.Dial.__init__(self, "Messages/minute total: ", 100)

    def action(self, value):
        config_screen["msgs_per_min"] = value
        return config_screen
    
class MsgsMinMmsiScreen(screen.Dial):
    def __init__(self):
        screen.Dial.__init__(self, "Messages/minute/mmsi: ", 10)

    def action(self, value):
        config_screen["msgs_per_min_per_mmsi"] = value
        return config_screen

class PingScreen(screen.TextEntry):
    def __init__(self):
        screen.TextEntry.__init__(self, "IP/domain to ping:\n", value="8.8.8.8")

    def action(self, value):
        pinging_screen.ip = value
        return pinging_screen
    
class PingingThread(threading.Thread):
    def __init__(self, ip):
        self.ip = ip
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
                screen.wr(line.replace(b"\n", b"\r\n"))

class PingingScreen(screen.DisplayScreen):
    def __init__(self):
        self.ip = ""
        screen.DisplayScreen.__init__(self, "")

    def display(self):
        self.content = "Pinging: %s\n" % self.ip
        screen.DisplayScreen.display(self)
        self.thread = PingingThread(self.ip)
        self.thread.start()
    def action_0(self):
        self.thread.quit()
        return debug_screen
    def action_1(self):
        self.thread.quit()
        return debug_screen
    def action_2(self):
        self.thread.quit()
        return debug_screen

class SyslogScreen(screen.TextScroll):
    def __init__(self):
        with open("/var/log/syslog") as f:
            content = f.read()
        content = content.replace(": ", ":\n")
        screen.TextScroll.__init__(self, content)

    def action(self):
        return debug_screen

class ShellScreen(object):
    def __init__(self):
        pass
    def run(self):
        subprocess.run("/bin/bash", stdin=screen.term.fileno(), stdout=screen.term.fileno(), stderr=screen.term.fileno())
        return debug_screen
    
main_screen = MainScreen()
config_screen = ConfigMenu()
debug_screen = DebugMenu()
cat_screen = CatScreen()
msgs_min_screen = MsgsMinScreen()
msgs_min_mmsi_screen = MsgsMinMmsiScreen()
ping_screen = PingScreen()
pinging_screen = PingingScreen()
syslog_screen = SyslogScreen()
shell_screen = ShellScreen()

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
            try:
                eval(line)
            except Exception as e:
                print(e)
                traceback.print_exc()
                
class IpStatus(threading.Thread):
    def run(self):
        while True:
            current_ip = None
            for ip in monitor_ip.get_ips():
                if ip != '127.0.0.1':
                    current_ip = ip
            main_screen["ip"] = current_ip
            time.sleep(1)
        
def main():
    Screen().start()
    Status().start()
    IpStatus().start()
