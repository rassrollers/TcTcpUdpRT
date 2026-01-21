import socket
import threading
import logging
from typing import Optional, Tuple


class UdpClient:
    """
    Simple UDP client for sending and receiving data.
    Can listen on a port and send data to specified addresses.
    """

    def __init__(self, timeout_sec: float = 5.0, buffer_size: int = 1024):
        self.timeout_sec = timeout_sec
        self.buffer_size = buffer_size
        self._socket: Optional[socket.socket] = None
        self._listen_socket: Optional[socket.socket] = None
        self._last_error: Optional[str] = None
        self._receive_thread: Optional[threading.Thread] = None
        self._running = False
        self._received_data: bytes = b""
        self._sender_address: Optional[Tuple[str, int]] = None
        self._lock = threading.Lock()

    def _ensure_socket(self) -> bool:
        """
        Ensure the socket is initialized.
        """
        if self._socket is None:
            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return True
            except socket.error as e:
                self._last_error = str(e)
                self._socket = None
                logging.error(f"Failed to create socket: {self._last_error}")
                return False
        return True

    def listen(self, host: str = "0.0.0.0", port: int = 9902) -> bool:
        """
        Start listening on a UDP port.
        """
        self._last_error = None

        try:
            # Create a new socket for listening (don't reuse send socket)
            try:
                listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except socket.error as e:
                self._last_error = str(e)
                logging.error(f"Failed to create listen socket: {self._last_error}")
                return False
            
            listen_socket.bind((host, port))
            listen_socket.settimeout(self.timeout_sec)
            
            self._listen_socket = listen_socket
            self._running = True
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            logging.info(f"UDP client listening on {host}:{port}")
            return True

        except socket.error as e:
            self._last_error = str(e)
            if listen_socket:
                try:
                    listen_socket.close()
                except:
                    pass
            logging.error(f"Failed to listen: {self._last_error}")
            return False

    def stop(self) -> bool:
        """
        Stop listening and close the socket.
        Ensures cleanup happens even if errors occur.
        """
        self._running = False
        success = True

        # Close send socket
        if self._socket:
            try:
                self._socket.close()
            except socket.error as e:
                self._last_error = str(e)
                logging.error(f"Error closing send socket: {self._last_error}")
                success = False
            finally:
                self._socket = None

        # Close listen socket
        if self._listen_socket:
            try:
                self._listen_socket.close()
            except socket.error as e:
                self._last_error = str(e)
                logging.error(f"Error closing listen socket: {self._last_error}")
                success = False
            finally:
                self._listen_socket = None

        # Stop receive thread
        if self._receive_thread:
            try:
                self._receive_thread.join(timeout=2.0)
            except Exception as e:
                self._last_error = str(e)
                logging.error(f"Error joining receive thread: {self._last_error}")
                success = False

        if success:
            logging.info("UDP client stopped")
        
        return success

    def _receive_loop(self):
        """
        Background thread loop for receiving UDP data.
        """
        while self._running:
            try:
                data, addr = self._listen_socket.recvfrom(self.buffer_size)
                with self._lock:
                    self._received_data = data
                    self._sender_address = addr
                logging.debug(f"Received {len(data)} bytes from {addr}")

            except socket.timeout:
                continue
            except socket.error as e:
                if self._running:
                    self._last_error = str(e)
                    logging.error(f"Error in receive loop: {self._last_error}")
                break

    def send(self, data: bytes, ip_address: str, port: int) -> int:
        """
        Send UDP data to a specified address.
        Returns number of bytes sent.
        """
        if not self._ensure_socket():
            self._last_error = "Failed to initialize socket"
            return 0

        try:
            sent = self._socket.sendto(data, (ip_address, port))
            logging.debug(f"Sent {sent} bytes to {ip_address}:{port}")
            return sent

        except socket.error as e:
            self._last_error = str(e)
            logging.error(f"Error sending data: {self._last_error}")
            return 0

    @property
    def is_listening(self) -> bool:
        """Check if the socket is listening."""
        return self._listen_socket is not None and self._running

    @property
    def error(self) -> bool:
        """Check if there's an error."""
        return self._last_error is not None

    @property
    def get_error(self) -> str:
        """Get the last error message."""
        return self._last_error or ""

    def is_data_available(self) -> bool:
        """
        Check if data has been received.
        """
        with self._lock:
            return len(self._received_data) > 0

    def receive(self) -> bytes:
        """
        Retrieve the last received data.
        """
        with self._lock:
            data = self._received_data
            self._received_data = b""
            return data

    def get_sender_address(self) -> Optional[Tuple[str, int]]:
        """
        Get the address of the last sender.
        Returns (ip_address, port) or None.
        """
        with self._lock:
            return self._sender_address

