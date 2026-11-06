"""A serial loopback "jumper" without hardware: a pty that echoes everything written to it.

    python3 test/pty-loopback.py /tmp/ttyLOOP &
    TEST_PORT=/tmp/ttyLOOP TEST_PORT_TYPE=pty npm test

It creates a pseudo-terminal, symlinks its device to the path given, and echoes whatever is
written to the device back to it until killed. Linux and macOS only.

Nothing in the echo path ever blocks. The tests don't read back everything they write, and a
blocking echo (`socat ... exec:cat`) fills the pty's input queue (small on macOS), stops
draining the output, and leaves write() and drain() hanging forever. When the input queue is
full, this drops bytes instead, the way a real UART's receive buffer overflows.
"""
import os
import pty
import select
import signal
import sys
import tty

link = sys.argv[1]
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # so `finally` removes the link

master, slave = pty.openpty()
tty.setraw(slave)
# Keep `slave` open: when every slave fd is closed the master reads EIO/EOF, and the tests open
# and close the port many times.
os.set_blocking(master, False)

if os.path.lexists(link):
    os.unlink(link)
os.symlink(os.ttyname(slave), link)

try:
    while True:
        select.select([master], [], [])
        try:
            data = os.read(master, 4096)
        except BlockingIOError:
            continue
        try:
            os.write(master, data)  # a short write drops the rest
        except BlockingIOError:
            pass  # input queue full: drop it all
finally:
    os.unlink(link)
