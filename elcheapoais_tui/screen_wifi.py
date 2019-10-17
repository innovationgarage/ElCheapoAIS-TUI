from . import screen
from .utils import strw

class WifiScreen(screen.Menu):
    def __init__(self, tui):
        self.tui = tui
        screen.Menu.__init__(self, [
            "Back",
        ])

    def display(self):
        self.aps = [(iface, ssid, connected, existing, path)
                    for iface, (aps, iface_path) in self.tui.dbus_thread.wifi_manager.aps().items()
                    for ssid, (connected, existing, path) in aps.items()]
        
        self.entries = ["Back"] + ["%s%s%s" % ("o " if connected else "  ", ssid, "" if existing else " (New)")
                                   for (iface, ssid, connected, existing, path) in self.aps]
        screen.Menu.display(self)
        
    def action(self, item):
        if item == 0:
            return self.tui.config_screen
        iface, ssid, connected, existing, path = self.aps[item-1]
        if existing:
            self.tui.dbus_thread.wifi_manager.connect(iface, ssid)
            return self
        else:
            self.tui.wifi_password_screen.ap = (iface, ssid, connected, existing, path)
            return self.tui.wifi_password_screen

class PasswordScreen(screen.TextEntry):
    def __init__(self, tui):
        self.tui = tui
        screen.TextEntry.__init__(self, "Password:\n", value="")

    def action(self, value):
        iface, ssid, connected, existing, path = self.ap
        self.tui.dbus_thread.wifi_manager.connect(iface, ssid, value)
        return self.tui.wifi_screen
    
