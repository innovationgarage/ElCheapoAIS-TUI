import os


os.write(1, b'\x1bc\x1b[2J')
os.write(1, b'MMSI:                           \r\nIP:                             \r\nLat:                            \r\nLon:                            \r\nLast pos:                       \r\n                                \r\n                                \r\n                                \r\nCFG           CAT            DBG')
os.write(1, b'\x1b[2;5H192.168.4.36   ')
os.write(1, b'\x1b[1;7H257098740')
os.write(1, b'\x1b[3;6H4.12345                   ')
os.write(1, b'\x1b[4;6H40.33218                  ')
os.write(1, b'\x1b[1;29HDOWN')
os.write(1, b'\x1b[5;11H2019-10-18 13:13:00  ')
os.write(1, b'\x1b[2;29HDOWN')


