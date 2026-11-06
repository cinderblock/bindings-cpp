"""Echo stdin to stdout like a serial loopback jumper, dropping bytes instead of blocking.

Use it as the far end of a pty, for TEST_PORT_TYPE=pty test runs:

    socat pty,raw,echo=0,link=/tmp/ttyLOOP exec:"python3 test/pty-echo.py" &
    TEST_PORT=/tmp/ttyLOOP TEST_PORT_TYPE=pty npm test

Plain `exec:cat` deadlocks. The tests don't read back everything they write, so the echo fills
the pty's input queue (small on macOS) and `cat` blocks. Then nothing drains the pty's output,
and write()/drain() never finish. A real UART drops bytes when its receive buffer overflows,
and this script does the same.
"""
import fcntl
import os

fcntl.fcntl(1, fcntl.F_SETFL, fcntl.fcntl(1, fcntl.F_GETFL) | os.O_NONBLOCK)

while True:
    data = os.read(0, 4096)
    if not data:
        break
    try:
        os.write(1, data)  # a short write drops the rest, like an overflowing RX buffer
    except BlockingIOError:
        pass
