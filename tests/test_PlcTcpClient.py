import logging
from Helper.AdsHandler import AdsHandler
from tests.Helper.TcpServer import TcpServer
from common import PLCSettings, wait_until
import pytest


TIMEOUT_SEC = 15.0
TCP_CLIENT_TEST_SUITE_START = "PRG_TEST.fb_TcpClient.startTcpClientTest"
TCP_CLIENT_TEST_SUITE_DONE = "PRG_TEST.fb_TcpClient.tcpClientTestDone"
RECV_BUFFER_SIZE = 255
TEST_MESSAGE = b"Hello from Python TCP server"


class TestPlcTcpClient:

    @pytest.fixture(autouse=True)
    def setup_teardown(self, plc_options: PLCSettings):
        """
        Setup and teardown for each test.
        - Initialize TCP server
        - Connect to PLC via ADS
        """
        self.server = TcpServer(host="0.0.0.0", port=plc_options.clientport)
        self.ads = AdsHandler(NetID=plc_options.netid, NetPort=plc_options.netport)
        self.ads.OpenConnection()
        self.plcIp = plc_options.ip
        self.serverPort = plc_options.clientport

        # Start the Python TCP server
        assert self.server.start(), "Failed to start TCP server"
        logging.info(f"TCP server started on port {self.serverPort}")

        yield  # Run test

        # Cleanup
        self.server.stop()
        self.ads.CloseConnection()
        logging.info("TCP server stopped and ADS connection closed")

    def test_plc_tcp_client(self):
        """
        Test the PLC as a TCP client connecting to the Python TCP server.
        Flow:
        1. Start PLC TCP client test suite
        2. Wait for PLC to connect to Python server
        3. Receive data from PLC
        4. Send response back to PLC
        5. Wait for PLC to disconnect
        6. Verify PLC test completes
        """
        plcReady = self.ads.GetPlcState()
        logging.info(f"PLC is running: {plcReady}")
        assert plcReady, "PLC not ready for test. End script"

        logging.info("- - - Start test: TCP client test - - -")

        # Start the PLC TCP client test
        self.ads.StartTestSuite(TestSuiteVariable=TCP_CLIENT_TEST_SUITE_START)
        logging.info("Started PLC TCP client test suite")

        # Wait for PLC to connect to Python server
        assert wait_until(
            self.server.is_client_connected,
            TIMEOUT_SEC,
            "Wait for PLC to connect to server",
        ), "PLC TCP client did not connect to server"
        logging.info("PLC TCP client connected to Python server")

        # Wait for data from PLC
        assert wait_until(
            lambda: len(self.server.get_received_data()) > 0,
            TIMEOUT_SEC,
            "Wait for data from PLC",
        ), "No data received from PLC TCP client"

        data = self.server.get_received_data()
        logging.info(f"Received from PLC: {data}")

        # Send response back to PLC
        try:
            if self.server._client_socket:
                self.server._client_socket.send(TEST_MESSAGE)
                logging.info(f"Sent to PLC: {TEST_MESSAGE}")
        except Exception as e:
            logging.warning(f"Failed to send response: {e}")

        # Wait for client to close connection
        assert wait_until(
            lambda: not self.server.is_client_connected(),
            TIMEOUT_SEC,
            "Wait for PLC to disconnect",
        ), "PLC TCP client did not disconnect"

        # Wait for test suite to complete
        assert wait_until(
            lambda: self.ads.IsTestSuiteDone(TCP_CLIENT_TEST_SUITE_DONE),
            TIMEOUT_SEC,
            "Wait for test suite to be done",
        ), "Test suite did not complete"

        logging.info("- - - End test: TCP client test - - -")
