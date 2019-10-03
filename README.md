To test on a Linux machine without a physical serial terminal:

    socat -d -d pty,raw,echo=0 pty,raw,echo=0

This will print two filenames on the form /dev/pts/N and /dev/pts/M

    minicom -D /dev/pts/N

    TTGOTERM=/dev/pts/M elcheapoais-tui
