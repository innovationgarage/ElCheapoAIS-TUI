import dbus
import uuid

NM_DEVICE_TYPE_WIFI = 2    

class WifiManager(object):
    def __init__(self, bus):
        self.bus = bus

    def known_connections(self):
        return {
            bytes(
                dbus.Interface(
                    self.bus.get_object("org.freedesktop.NetworkManager", connpath),
                    "org.freedesktop.NetworkManager.Settings.Connection"
                ).GetSettings().get("802-11-wireless", {}).get("ssid", b"")
            ).decode("utf-8"): str(connpath)
            for connpath in dbus.Interface(self.bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/Settings"),
                                           "org.freedesktop.NetworkManager.Settings").ListConnections()}

    def wifi_devices(self):
        return {
            str(path): str(proxy.Get("org.freedesktop.NetworkManager.Device", "Interface"))
            for (path, proxy) in
            [(path, dbus.Interface(self.bus.get_object("org.freedesktop.NetworkManager", path),
                                   "org.freedesktop.DBus.Properties"))
             for path in
             dbus.Interface(self.bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"),
                            "org.freedesktop.NetworkManager").GetDevices()]
            if (proxy.Get("org.freedesktop.NetworkManager.Device", "State") > 2
                and proxy.Get("org.freedesktop.NetworkManager.Device", "DeviceType") == NM_DEVICE_TYPE_WIFI)
        }
    
    def wifi_devices_by_iface(self):
        return {iface: path for path, iface in self.wifi_devices().items()}
        
    def aps(self):
        known_connections = self.known_connections()
        return {iface: ({ssid: (appath == connected, known_connections.get(ssid, None), str(appath))
                         for (ssid, appath) in
                         ((
                             bytes(
                                 dbus.Interface(
                                     self.bus.get_object("org.freedesktop.NetworkManager", appath),
                                     "org.freedesktop.DBus.Properties"
                                 ).Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid")
                             ).decode("utf-8"),
                             appath)
                          for appath in dbus.Interface(proxy, "org.freedesktop.NetworkManager.Device.Wireless").GetAccessPoints())},
                        d)
                for (d, proxy, iface, connected) in
                ((d, proxy, iface, dbus.Interface(proxy, "org.freedesktop.DBus.Properties").Get(
                    "org.freedesktop.NetworkManager.Device.Wireless", "ActiveAccessPoint"))
                 for d, proxy, iface in
                 ((d, self.bus.get_object("org.freedesktop.NetworkManager", d), iface)
                  for d, iface in self.wifi_devices().items()))}

    def connect(self, iface, ssid, password=None):
        if not password:
            device_aps, device_path = self.aps()[iface]
            ap_connected, ap_connection, ap_path = device_aps[ssid]
            dbus.Interface(
                self.bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"),
                "org.freedesktop.NetworkManager"
            ).ActivateConnection(ap_connection, device_path, "/")
        else:
            dbus.Interface(
                self.bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"),
                "org.freedesktop.NetworkManager"
            ).AddAndActivateConnection(
                dbus.Dictionary({
                    'connection': {
                        'type': '802-11-wireless',
                        'id': ssid},
                    '802-11-wireless': {
                        'ssid': dbus.ByteArray(ssid.encode("utf-8")),
                        'mode': 'infrastructure',
                    },
                    '802-11-wireless-security': {
                        'key-mgmt': 'wpa-psk',
                        'auth-alg': 'open',
                        'psk': password,
                    },
                    'ipv4': {'method': 'auto'},
                    'ipv6': {'method': 'ignore'}
                }),
                self.wifi_devices_by_iface()[iface],
                "/")


# wifi = WifiManager(dbus.SystemBus())
# aps = wifi.aps()
# print(aps)
# iface = list(aps.keys())[0]
# wifi.connect(iface, "Holmbo3b")
