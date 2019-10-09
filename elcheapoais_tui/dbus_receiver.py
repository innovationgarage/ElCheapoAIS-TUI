import sys
import traceback

import dbus
import dbus.mainloop.glib
import gi.repository.GLib
import threading
import json

def timeout(to):
    def wrapper(fn):
        gi.repository.GLib.timeout_add(to, fn)
    return wrapper

nm_states = {0: "NM_ACTIVE_CONNECTION_STATE_UNKNOWN",
             1: "NM_ACTIVE_CONNECTION_STATE_ACTIVATING",
             2: "NM_ACTIVE_CONNECTION_STATE_ACTIVATED",
             3: "NM_ACTIVE_CONNECTION_STATE_DEACTIVATING",
             4: "NM_ACTIVE_CONNECTION_STATE_DEACTIVATED"}

def get_ip(bus, connection):
    dhcp_path = dbus.Interface(
        bus.get_object("org.freedesktop.NetworkManager", connection),
        "org.freedesktop.DBus.Properties"
    ).Get("org.freedesktop.NetworkManager.Connection.Active", "Dhcp4Config")

    return dbus.Interface(
        bus.get_object("org.freedesktop.NetworkManager", dhcp_path),
        "org.freedesktop.DBus.Properties"
    ).Get(
        "org.freedesktop.NetworkManager.DHCP4Config", "Options"
    )["ip_address"]

class DBusReceiver(threading.Thread):
    def __init__(self, tui):
        self.tui = tui
        self.nm_connections = {} 
        threading.Thread.__init__(self)
    
    def nmea_signal(self, msg):
        msg = json.loads(msg)
        if msg and "lat" in msg and "lon" in msg:
            self.tui.main_screen["latlon"] = (msg["lat"], msg["lon"])

    def nm_state_changed(self, state, reason, dbus_message):
        state = nm_states[state]
        if state == "NM_ACTIVE_CONNECTION_STATE_ACTIVATED":
            self.nm_add_connection(dbus_message.get_path())
        elif state == "NM_ACTIVE_CONNECTION_STATE_DEACTIVATED":
            self.nm_remove_connection(dbus_message.get_path())

    def nm_add_connection(self, path):
        self.nm_connections[path] = get_ip(self.bus, path)
        self.tui.main_screen["ip"] = self.nm_connections[path]

    def nm_remove_connection(self, path):
        del self.nm_connections[path]
        if len(self.nm_connections):
            self.tui.main_screen["ip"] = self.nm_connections[next(iter(self.nm_connections.keys()))]
        else:
            self.tui.main_screen["ip"] = None
            
    def run(self, *arg, **kw):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.bus = dbus.SystemBus()
        
        self.bus.add_signal_receiver(
            self.nmea_signal,
            dbus_interface = "no.innovationgarage.elcheapoais",
            signal_name = "NMEA")
        self.bus.add_signal_receiver(
            self.nm_state_changed,
            dbus_interface = "org.freedesktop.NetworkManager.Connection.Active",
            signal_name = "StateChanged",
            message_keyword='dbus_message')

        nm = dbus.Interface(self.bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"), "org.freedesktop.DBus.Properties")
        connections = nm.Get("org.freedesktop.NetworkManager", "ActiveConnections")
        for connection in connections:
            self.nm_add_connection(connection)

        loop = gi.repository.GLib.MainLoop()
        loop.run()
    
