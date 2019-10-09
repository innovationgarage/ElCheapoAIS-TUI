from . import screen
import termios
import subprocess

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
