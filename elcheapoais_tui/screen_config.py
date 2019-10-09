from . import screen
from .utils import strw

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
