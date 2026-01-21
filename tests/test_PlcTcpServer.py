import logging
from Helper.AdsHandler import AdsHandler
from Helper.TcpClient import TcpClient
from common import PLCSettings, wait_until
import pytest


TIMEOUT_SEC = 15.0
TCP_SERVER_TEST_SUITE_START = "PRG_TEST.fb_TcpServer.startTcpServerTest"
TCP_SERVER_TEST_SUITE_DONE = "PRG_TEST.fb_TcpServer.tcpServerTestDone"
RECV_BUFFER_SIZE = 255
TEST_MESSAGE = b"Hello from PC test script"


class TestPlcTcpServer:
    """
    Test the PLC as a TCP server accepting connections from a Python TCP client.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self, plc_options: PLCSettings):
        """
        Setup and teardown for each test.
        - Initialize TCP client
        - Connect to PLC via ADS
        """
        self.client = TcpClient(timeout_sec=TIMEOUT_SEC)  # socket timeout stays short
        self.ads = AdsHandler(NetID=plc_options.netid, NetPort=plc_options.netport)
        self.ads.OpenConnection()
        self.plcIp = plc_options.ip
        self.serverPort = plc_options.serverport

        yield  # Run test

        self.ads.CloseConnection()

    def test_plc_tcp_server(self):
        """
        Test the PLC as a TCP server accepting connections from a Python TCP client.
        Flow:
        1. Start PLC TCP server test suite
        2. Connect Python TCP client to PLC server
        3. Send data to PLC server
        4. Wait for and receive response from PLC server
        5. Disconnect from PLC server
        6. Verify PLC test completes
        """
        plcReady = self.ads.GetPlcState()
        logging.info(f"PLC is running: {plcReady}")
        assert plcReady, "PLC not ready for test. End script"

        logging.info("- - - Start test: TCP server test - - -")
        self.ads.StartTestSuite(TestSuiteVariable=TCP_SERVER_TEST_SUITE_START)

        assert self.client.connect(
            self.plcIp, self.serverPort
        ), f"Connect failed: {self.client.get_error}"
        logging.info("TCP client connected to PLC TCP server")

        sent = self.client.send(TEST_MESSAGE)
        logging.info(f"Sent {sent} bytes")

        assert wait_until(
            self.client.is_data_available, TIMEOUT_SEC, "Wait for data to be ready"
        ), "No data available from TCP server"
        data = self.client.receive(RECV_BUFFER_SIZE)
        logging.info(f"Received: {data}")

        self.client.disconnect()
        logging.info("TCP client disconnected from PLC TCP server")

        assert wait_until(
            lambda: self.ads.IsTestSuiteDone(TCP_SERVER_TEST_SUITE_DONE),
            TIMEOUT_SEC,
            "Wait for test suite to be done",
        ), "Test suite did not complete"

        logging.info("- - - End test: TCP server test - - -")
