from . import screen

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
