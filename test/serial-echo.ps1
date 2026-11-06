# Echo everything that arrives on a serial port back out of it. Bytes that can't be written
# within 50 ms are dropped, as a real UART drops them when its buffer is full: blocking here
# would stall the other end's drain (see pty-loopback.py).
param([string]$Port = 'COM11')
$serial = [System.IO.Ports.SerialPort]::new($Port, 115200)
$serial.Handshake = 'None'
$serial.WriteTimeout = 50
$serial.Open()
$stream = $serial.BaseStream
$buffer = [byte[]]::new(4096)
"echoing on $Port"
while ($true) {
  try {
    $n = $stream.Read($buffer, 0, $buffer.Length)
  } catch [System.IO.IOException] {
    # e.g. the other end purging while a read is pending; keep going
    "read: $($_.Exception.Message)"
    continue
  }
  try { $stream.Write($buffer, 0, $n) } catch [System.TimeoutException] { } catch [System.IO.IOException] { "write: $($_.Exception.Message)" }
}
