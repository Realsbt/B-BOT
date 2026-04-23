import socket
import time


class TransportError(RuntimeError):
    pass


class BaseTransport:
    def write_line(self, line: str) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


class UartTransport(BaseTransport):
    def __init__(self, port: str, baud: int):
        import serial

        self._serial_mod = serial
        self.port = port
        self.baud = baud
        self._ser = None

    def _ensure_open(self):
        if self._ser and self._ser.is_open:
            return
        self._ser = self._serial_mod.Serial(self.port, self.baud, timeout=0.1)

    def write_line(self, line: str) -> None:
        self._ensure_open()
        self._ser.write((line.rstrip("\r\n") + "\n").encode("ascii"))
        self._ser.flush()

    def close(self) -> None:
        if self._ser:
            self._ser.close()


class TcpTransport(BaseTransport):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._sock = None
        self._last_connect_attempt = 0.0

    def _ensure_open(self):
        if self._sock:
            return
        now = time.monotonic()
        if now - self._last_connect_attempt < 1.0:
            raise TransportError("TCP reconnect throttled")
        self._last_connect_attempt = now
        sock = socket.create_connection((self.host, self.port), timeout=1.0)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._sock = sock

    def write_line(self, line: str) -> None:
        try:
            self._ensure_open()
            self._sock.sendall((line.rstrip("\r\n") + "\n").encode("ascii"))
        except OSError as exc:
            self.close()
            raise TransportError(str(exc)) from exc

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            finally:
                self._sock = None


class NullTransport(BaseTransport):
    def write_line(self, line: str) -> None:
        return
