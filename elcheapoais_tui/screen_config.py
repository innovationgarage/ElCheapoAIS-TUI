from . import screen
from .utils import strw

class ConfigMenu(screen.Menu):
    def __init__(self, tui):
        self.tui = tui
        screen.Menu.__init__(self, [
            "Back",
            "Msgs/min:",
            "Msgs/min/mmsi:",
            "Wifi",
            "Save settings"
        ], max_message_per_sec = 0.1, max_message_per_mmsi_per_sec=0.1)

    def display_max_message_per_sec(self, value):
        self.wr(b"\x1b[3;13H" + strw(" " * (screen.SCREENW-13), 1, 1, str(value)).encode("utf-8"))
        
    def display_max_message_per_mmsi_per_sec(self, value):
        self.wr(b"\x1b[4;18H" + strw(" " * (screen.SCREENW-19), 1, 1, str(value)).encode("utf-8"))

    def updated_max_message_per_sec(self, value):
        try:
            downsampler = self.tui.dbus_thread.bus.get_object('no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/downsampler')
            downsampler.Set("no.innovationgarage.elcheapoais.downsampler", "max_message_per_sec", value, dbus_interface='org.freedesktop.DBus.Properties')
        except Exception as e:
            print(e)

    def updated_max_message_per_mmsi_per_sec(self, value):
        try:
            downsampler = self.tui.dbus_thread.bus.get_object('no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/downsampler')
            downsampler.Set("no.innovationgarage.elcheapoais.downsampler", "max_message_per_mmsi_per_sec", value, dbus_interface='org.freedesktop.DBus.Properties')
        except Exception as e:
            print(e)
        
    def action_0(self):
        return self.tui.main_screen
    def action_1(self):
        self.tui.msgs_min_screen["value"] = self["max_message_per_sec"]
        return self.tui.msgs_min_screen
    def action_2(self):
        self.tui.msgs_min_mmsi_screen["value"] = self["max_message_per_mmsi_per_sec"]
        return self.tui.msgs_min_mmsi_screen
    def action_3(self):
        return self.tui.wifi_screen
    def action_4(self):
        status = os.system("rsync -a --progress /etc/ /run/etc/")
        if status == 0:
            status = os.system("overlayroot-chroot rsync -a --verbose --exclude fstab /run/etc/ /etc/")
        if status == 0:
            self.tui.save_status_screen.content = "Configuration successfully saved"
        else:
            self.tui.save_status_screen.content = "Something went wrong!"
        return self.tui.save_status_screen

class SaveStatusScreen(DisplayScreen):
    def __init__(self, tui):
        self.tui = tui
        screen.DisplayScreen.__init__(self, "")
    
class MsgsMinScreen(screen.Dial):
    def __init__(self, tui):
        self.tui = tui
        screen.Dial.__init__(self, "Messages/minute total: ", 0, inc=0.01)

    def action(self, value):
        self.tui.config_screen["max_message_per_sec"] = value
        return self.tui.config_screen
    
class MsgsMinMmsiScreen(screen.Dial):
    def __init__(self, tui):
        self.tui = tui
        screen.Dial.__init__(self, "Messages/minute/mmsi: ", 0, inc=0.01)

    def action(self, value):
        self.tui.config_screen["max_message_per_mmsi_per_sec"] = value
        return self.tui.config_screen
