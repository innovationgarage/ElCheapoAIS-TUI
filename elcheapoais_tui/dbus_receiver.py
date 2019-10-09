import sys
import traceback

import dbus
import dbus.mainloop.glib
import gi.repository.GLib
import threading

class DBusReceiver(threading.Thread):
    def __init__(self, tui):
        self.tui = tui
        threading.Thread.__init__(self)
    
    def nmea_signal(msg):
        print("Received a hello signal and it says " + msg)
        
    def run(self, *arg, **kw):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        bus = dbus.SessionBus()
        bus.add_signal_receiver(self.nmea_signal, dbus_interface = "no.innovationgarage.elcheapoais", signal_name = "NMEA")

        loop = gi.repository.GLib.MainLoop()
        loop.run()
    
