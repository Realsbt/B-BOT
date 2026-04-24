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
        self.last_hello = ""

    def _recv_line(self, timeout: float = 1.0) -> str:
        self._sock.settimeout(timeout)
        data = bytearray()
        while True:
            b = self._sock.recv(1)
            if not b:
                raise TransportError("TCP connection closed before newline")
            data.extend(b)
            if b == b"\n":
                return data.decode("ascii", errors="replace").strip()

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
        try:
            self.last_hello = self._recv_line(timeout=1.0)
        except (OSError, TransportError):
            self.last_hello = ""

    def write_line(self, line: str) -> None:
        return self.write_line_with_ack(line)

    def write_line_with_ack(self, line: str):
        try:
            self._ensure_open()
            payload = line.rstrip("\r\n")
            t0_ns = time.monotonic_ns()
            self._sock.sendall((payload + "\n").encode("ascii"))
            ack = self._recv_line(timeout=1.0)
            t1_ns = time.monotonic_ns()
            parts = ack.split(",", 3)
            return {
                "pc_send_ns": t0_ns,
                "pc_ack_ns": t1_ns,
                "ack_latency_ms": (t1_ns - t0_ns) / 1e6,
                "ack_kind": parts[0] if len(parts) > 0 else "",
                "esp_ms": parts[1] if len(parts) > 1 else "",
                "rc": parts[2] if len(parts) > 2 else "",
                "ack_command": parts[3] if len(parts) > 3 else "",
                "raw_ack": ack,
                "hello": self.last_hello,
            }
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
