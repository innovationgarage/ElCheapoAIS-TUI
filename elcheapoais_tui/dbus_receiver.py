import sys
import traceback

import dbus
import dbus.service
import dbus.mainloop.glib
import gi.repository.GLib
import gi.repository.GObject
import threading
import json
import os
from . import wifi_manager

def get(bus, bus_name, obj_path, interface_name, parameter_name, default=None):
    try:
        return bus.get_object(bus_name, obj_path).Get(interface_name, parameter_name)
    except:
        return default

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
        gi.repository.GObject.threads_init()
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = getattr(dbus, os.environ.get("ELCHEAPOAIS_DBUS", "SystemBus"))()
#        self.bus_name = dbus.service.BusName('no.innovationgarage.elcheapoais.tui', self.bus)
        self.tui = tui
        self.nm_connections = {}
        self.wifi_manager = wifi_manager.WifiManager(self.bus)
        threading.Thread.__init__(self)
    
    def nmea_signal(self, msg):
        msg = json.loads(msg)
        if msg and "lat" in msg and "lon" in msg:
            self.tui.main_screen["latlon"] = (msg["lat"], msg["lon"])

    def manhole_signal(self, status, errno):
        self.tui.main_screen["net"] = status

    def PropertiesChanged(self, interface_name, properties_modified, properties_deleted, dbus_message):
        if interface_name == "no.innovationgarage.elcheapoais.receiver":    
            for key, value in properties_modified.items():
                if key == "station_id":
                    self.tui.main_screen["mmsi"] = value
                
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
        print("NANANANANANANANA")

        self.bus.add_signal_receiver(
            self.nmea_signal,
            dbus_interface = "no.innovationgarage.elcheapoais",
            signal_name = "NMEA")
        self.bus.add_signal_receiver(
            self.manhole_signal,
            dbus_interface = "no.innovationgarage.elcheapoais",
            signal_name = "manhole")
        self.bus.add_signal_receiver(
            self.nm_state_changed,
            dbus_interface = "org.freedesktop.NetworkManager.Connection.Active",
            signal_name = "StateChanged",
            message_keyword='dbus_message')
        self.bus.add_signal_receiver(
            self.PropertiesChanged,
            dbus_interface = "org.freedesktop.DBus.Properties",
            signal_name = "PropertiesChanged",
            message_keyword='dbus_message')

        self.tui.config_screen["max_message_per_sec"] = get(self.bus,
            'no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/downsampler',
            "no.innovationgarage.elcheapoais.downsampler", "max_message_per_sec", 0.01)
        self.tui.config_screen["max_message_per_mmsi_per_sec"] = get(self.bus,
            'no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/downsampler',
            "no.innovationgarage.elcheapoais.downsampler", "max_message_per_mmsi_per_sec", 0.01)

        self.tui.main_screen["mmsi"] = get(self.bus,
            'no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/receiver',
            "no.innovationgarage.elcheapoais.receiver", "station_id", "unknown")
        
        try:
            nm = dbus.Interface(self.bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"), "org.freedesktop.DBus.Properties")
            connections = nm.Get("org.freedesktop.NetworkManager", "ActiveConnections")
            print("XXXXXXXXXXXXXXXXXX", connections)
            for connection in connections:
                self.nm_add_connection(connection)
        except Exception as e:
            print("YYYYYYYYYYYYYYYYYYYY")
            print(e)
                
        loop = gi.repository.GLib.MainLoop()
        loop.run()
    
