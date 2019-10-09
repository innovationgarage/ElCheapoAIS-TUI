import threading
import subprocess
import re
from . import screen

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
