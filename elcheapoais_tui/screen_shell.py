from . import screen
import termios
import subprocess

class ShellScreen(object):
    proper_terminal = {'cflag': ['CREAD', 'CBAUD', 'CSIZE'],
                       'oflag': ['OPOST', 'ONLCR'],
                       'iflag': ['IXON', 'ICRNL'],
                       'lflag': ['VQUIT', 'VERASE', 'VKILL', 'VTIME', 'VMIN', 'VSWTCH', 'VSTART', 'VSTOP', 'VEOL', 'VREPRINT',
                                 'VDISCARD', 'VLNEXT', 'VEOL2', 'ECHOCTL', 'ECHOK', 'VSUSP', 'IEXTEN', 'ECHOKE', 'VWERASE']}
    
    def __init__(self, tui):
        self.tui = tui
    def run(self):
        fd = screen.term.fileno()
        old = termios.tcgetattr(fd)
        new = [self.to_termios(self.proper_terminal["iflag"]),
               self.to_termios(self.proper_terminal["oflag"]),
               self.to_termios(self.proper_terminal["cflag"]),
               self.to_termios(self.proper_terminal["lflag"])] + old[4:]
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, new)
            subprocess.run("/bin/bash", stdin=fd, stdout=fd, stderr=fd)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

        return self.tui.debug_screen

    def to_termios(self, flags):
        res = 0
        for flag in flags:
            res |= getattr(termios, flag)
        return res
    
