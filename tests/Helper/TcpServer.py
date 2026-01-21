import socket
import threading
import logging
from typing import Optional, Callable


class TcpServer:
    """
    Simple TCP server for testing a PLC TCP client.
    Runs in a background thread and echoes received data back to the client.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9901, buffer_size: int = 1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self._socket: Optional[socket.socket] = None
        self._server_thread: Optional[threading.Thread] = None
        self._running = False
        self._client_socket: Optional[socket.socket] = None
        self._received_data: bytes = b""
        self._lock = threading.Lock()
        self._last_error: Optional[str] = None
        self._on_data_received: Optional[Callable[[bytes], bytes]] = None

    def start(self, on_data_received: Optional[Callable[[bytes], bytes]] = None) -> bool:
        """
        Start the TCP server in a background thread.
        on_data_received: Optional callback that receives data and returns response.
                         If None, echoes the data back.
        """
        if self._running:
            logging.warning("Server is already running")
            return False

        self._on_data_received = on_data_received
        self._running = True

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.host, self.port))
            self._socket.listen(1)
            self._socket.settimeout(1.0)

            self._server_thread = threading.Thread(target=self._run, daemon=True)
            self._server_thread.start()
            logging.info(f"TCP server started on {self.host}:{self.port}")
            return True

        except socket.error as e:
            self._last_error = str(e)
            self._running = False
            logging.error(f"Failed to start server: {self._last_error}")
            return False

    def stop(self) -> bool:
        """
        Stop the TCP server.
        """
        self._running = False

        try:
            if self._client_socket:
                self._client_socket.close()
                self._client_socket = None

            if self._socket:
                self._socket.close()
                self._socket = None

            if self._server_thread:
                self._server_thread.join(timeout=2.0)

            logging.info("TCP server stopped")
            return True

        except socket.error as e:
            self._last_error = str(e)
            logging.error(f"Error stopping server: {self._last_error}")
            return False

    def _run(self):
        """
        Server loop running in background thread.
        """
        while self._running:
            try:
                client_socket, addr = self._socket.accept()
                logging.info(f"Client connected from {addr}")
                self._client_socket = client_socket
                self._client_socket.settimeout(5.0)

                with self._lock:
                    self._received_data = b""

                while self._running:
                    try:
                        data = self._client_socket.recv(self.buffer_size)
                        if not data:
                            logging.info("Client disconnected")
                            break

                        with self._lock:
                            self._received_data = data

                        logging.debug(f"Received: {data}")

                        # Process data with callback or echo
                        if self._on_data_received:
                            response = self._on_data_received(data)
                        else:
                            response = data

                        self._client_socket.send(response)
                        logging.debug(f"Sent: {response}")

                    except socket.timeout:
                        continue
                    except socket.error as e:
                        logging.error(f"Socket error: {e}")
                        break

                if self._client_socket:
                    self._client_socket.close()
                    self._client_socket = None

            except socket.timeout:
                continue
            except socket.error as e:
                if self._running:
                    logging.error(f"Accept error: {e}")

    def get_received_data(self) -> bytes:
        """
        Get the last received data from the client.
        """
        with self._lock:
            return self._received_data

    def reset_received_data(self):
        """
        Clear the received data buffer.
        """
        with self._lock:
            self._received_data = b""

    def is_client_connected(self) -> bool:
        """
        Check if a client is currently connected.
        """
        return self._client_socket is not None

    @property
    def get_error(self) -> str:
        return self._last_error or ""

    def reset_error(self):
        self._last_error = None
