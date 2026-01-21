import socket
from typing import Optional


class TcpClient:
    """
    Simple TCP client for testing a PLC TCP server.
    """

    def __init__(self, timeout_sec: float = 5.0, buffer_size: int = 1024):
        self.timeout_sec = timeout_sec
        self.buffer_size = buffer_size
        self._socket: Optional[socket.socket] = None
        self._last_error: Optional[str] = None

    def connect(self, ip_address: str, port: int) -> bool:
        """
        Connect to the PLC TCP server.
        """
        self._last_error = None

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout_sec)
            self._socket.connect((ip_address, port))
            return True

        except socket.error as e:
            self._last_error = str(e)
            self._socket = None
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from the PLC.
        """
        try:
            if self._socket:
                self._socket.close()
                self._socket = None
            return True
        except socket.error as e:
            self._last_error = str(e)
            return False

    @property
    def is_connected(self) -> bool:
        return self._socket is not None

    @property
    def error(self) -> bool:
        return self._last_error is not None

    @property
    def get_error(self) -> str:
        return self._last_error or ""

    def send(self, data: bytes) -> int:
        """
        Send raw bytes to the PLC.
        Returns number of bytes sent.
        """
        if not self._socket:
            self._last_error = "Not connected"
            return 0

        try:
            sent = self._socket.send(data)
            return sent
        except socket.error as e:
            self._last_error = str(e)
            return 0

    def is_data_available(self) -> bool:
        """
        Non-blocking check if data is available.
        """
        if not self._socket:
            return False

        try:
            self._socket.setblocking(False)
            data = self._socket.recv(1, socket.MSG_PEEK)
            return len(data) > 0
        except BlockingIOError:
            return False
        except socket.error as e:
            self._last_error = str(e)
            return False
        finally:
            self._socket.setblocking(True)

    def receive(self, max_length: int) -> bytes:
        """
        Receive data from the PLC.
        """
        if not self._socket:
            self._last_error = "Not connected"
            return b""

        try:
            data = self._socket.recv(max_length)
            return data
        except socket.timeout:
            return b""
        except socket.error as e:
            self._last_error = str(e)
            return b""

    def reset_error(self):
        self._last_error = None
