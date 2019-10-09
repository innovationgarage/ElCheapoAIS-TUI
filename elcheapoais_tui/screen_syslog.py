from . import screen

class SyslogScreen(screen.TextScroll):
    def __init__(self, tui):
        self.tui = tui
        with open("/var/log/syslog") as f:
            content = f.read()
        content = content.replace(": ", ":\n")
        screen.TextScroll.__init__(self, content)

    def action(self, value):
        return self.tui.debug_screen
