import datetime
from . import screen
from .utils import strw

class MainScreen(screen.DisplayScreen):
    def __init__(self, tui):
        self.tui = tui
        
        s = screen.empty_screen
        s = strw(s, 1, 1, "MMSI:")
        s = strw(s, 1, 2, "IP:")
        s = strw(s, 1, 3, "Lat:")
        s = strw(s, 1, 4, "Lon:")
        s = strw(s, 1, 5, "Last pos:")

        s = strw(s, 1, screen.SCREENH, "CFG")
        s = strw(s, screen.SCREENW//2-1, screen.SCREENH, "CAT")    
        s = strw(s, screen.SCREENW-2, screen.SCREENH, "DBG")

        screen.DisplayScreen.__init__(self, s)
        
        self["ip"] = "192.168.4.36"
        self["mmsi"] = "257098740"
        self["latlon"] = (4.12345, 40.33218)
        self["time"] = datetime.datetime.now()
        self["nmea"] = False
        self["net"] = False
        
    def display(self):
        screen.DisplayScreen.display(self)

    def display_nmea(self, up):
        self.wr(b"\x1b[1;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + (b"  UP" if up else b"DOWN"))
                
    def display_net(self, up):
        self.wr(b"\x1b[2;%sH" % (str(screen.SCREENW-3).encode("utf-8"),) + (b"  UP" if up else b"DOWN"))
            
    def display_mmsi(self, mmsi):
        self.wr(b"\x1b[1;7H" + b" " * 9)
        self.wr(b"\x1b[1;7H" + str(mmsi).encode("utf-8"))

    def display_ip(self, ip):
        self.wr(b"\x1b[2;5H" + strw(" " * 15, 1, 1, (ip or "")).encode("utf-8"))

    def updated_latlon(self, value):
        if value is not None:
            self["nmea"] = True
            self["time"] = datetime.datetime.now()
        else:
            self["nmea"] = False
        
    def display_latlon(self, value):
        if value is not None:
            lat, lon = value
        else:
            lat = lon = ""
        self.wr(b"\x1b[3;6H" + strw(" " * (screen.SCREENW-6), 1, 1, str(lat) if lat is not None else "").encode("utf-8"))
        self.wr(b"\x1b[4;6H" + strw(" " * (screen.SCREENW-6), 1, 1, str(lon) if lon is not None else "").encode("utf-8"))
        
    def display_time(self, value):
        self.wr(b"\x1b[5;11H" + strw(" " * (screen.SCREENW-11), 1, 1,
                                     value.strftime("%Y-%m-%d %H:%M:%S")
                                     if self["latlon"] is not None
                                     else "No positions received").encode("utf-8"))

    def action_0(self):
        return self.tui.config_screen
    def action_1(self):
        return self.tui.cat_screen
    def action_2(self):
        return self.tui.debug_screen
    
