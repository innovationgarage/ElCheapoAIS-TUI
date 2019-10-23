import termios

all_flags = {"iflag": ["IGNBRK","BRKINT","IGNPAR","PARMRK","INPCK","ISTRIP","INLCR","IGNCR","ICRNL","IUCLC","IXON","IXANY","IXOFF","IMAXBEL","IUTF8"], "oflag": ["OPOST","OLCUC","ONLCR","OCRNL","ONOCR","ONLRET","OFILL","OFDEL","NLDLY","CRDLY","TABDLY","BSDLY","VTDLY","FFDLY"], "cflag": ["CBAUD","CBAUDEX","CSIZE","CSTOPB","CREAD","PARENB","PARODD","HUPCL","CLOCAL","LOBLK","CIBAUD","CMSPAR","CRTSCTS"], "lflag": ["ISIG","ICANON","XCASE","ECHO","ECHOE","ECHOK","ECHONL","ECHOCTL","ECHOPRT","ECHOKE","DEFECHO","FLUSHO","NOFLSH","TOSTOP","PENDIN","IEXTEN","VDISCARD","VDSUSP","VEOF","VEOL","VEOL2","VERASE","VINTR","VKILL","VLNEXT","VMIN","VQUIT","VREPRINT","VSTART","VSTATUS","VSTOP","VSUSP","VSWTCH","VTIME","VWERASE"], "speed": ["B0","B50","B75","B110","B134","B150","B200","B300","B600","B1200","B1800","B2400","B4800","B9600","B19200","B38400","B57600","B115200","B230400"]}

all_values = {}
for grp, flags in all_flags.items():
    all_values[grp] = {}
    for flag in flags:
        if hasattr(termios, flag):
            all_values[grp][getattr(termios, flag)] = flag

iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(1)
iflag = [name for value, name in all_values["iflag"].items() if value & iflag]
oflag = [name for value, name in all_values["oflag"].items() if value & oflag]
cflag = [name for value, name in all_values["cflag"].items() if value & cflag]
lflag = [name for value, name in all_values["lflag"].items() if value & lflag]
ispeed = all_values["speed"][ispeed]
ospeed = all_values["speed"][ospeed]
tcattr = {"iflag": iflag, "oflag": oflag, "cflag": cflag, "lflag": lflag, "ispeed": ispeed, "ospeed": ospeed, "cc": cc}

print(tcattr)
