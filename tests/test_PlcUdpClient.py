import logging
import time
from Helper.AdsHandler import AdsHandler
from tests.Helper.UdpClient import UdpClient
from common import PLCSettings, wait_until
import pytest


TIMEOUT_SEC = 15.0
UDP_CLIENT_TEST_SUITE_START = "PRG_TEST.fb_UdpClient.startUdpTest"
UDP_CLIENT_TEST_SUITE_DONE = "PRG_TEST.fb_UdpClient.udpTestDone"
UDP_CLIENT_LISTEN_TEST_DONE = "PRG_TEST.fb_UdpClient.waitListenTestDone"
UDP_CLIENT_RECEIVE_TEST_DONE = "PRG_TEST.fb_UdpClient.waitReceiveTestDone"
RECV_BUFFER_SIZE = 255
TEST_MESSAGE = b"Hello from Python UDP client"
UDP_TEST_PORT = 9902
UDP_LISTEN_PORT = 9901


class TestPlcUdpClient:

    @pytest.fixture(autouse=True)
    def setup_teardown(self, plc_options: PLCSettings):
        """
        Setup and teardown for each test.
        - Initialize UDP client
        - Connect to PLC via ADS
        """
        self.udp_client = UdpClient(timeout_sec=TIMEOUT_SEC, buffer_size=RECV_BUFFER_SIZE)
        self.ads = AdsHandler(NetID=plc_options.netid, NetPort=plc_options.netport)
        self.ads.OpenConnection()
        self.plcIp = plc_options.ip
        self.udpTestPort = plc_options.udpport if hasattr(plc_options, 'udpport') else UDP_TEST_PORT
        self.udpListenPort = UDP_LISTEN_PORT

        logging.info(f"UDP client initialized - will send to PLC at {self.plcIp}:{self.udpTestPort}")

        yield  # Run test

        # Cleanup
        self.udp_client.stop()
        self.ads.CloseConnection()
        logging.info("UDP client stopped and ADS connection closed")

    def test_plc_udp_client_send_and_receive(self):
        """
        Test the PLC UDP client.
        Flow:
        1. Send initial data to PLC UDP port
        2. Start listening on a local port
        3. Wait for PLC to send data back
        4. Receive and verify data from PLC
        5. Verify PLC test completes
        """
        plcReady = self.ads.GetPlcState()
        logging.info(f"PLC is running: {plcReady}")
        assert plcReady, "PLC not ready for test. End script"

        logging.info("- - - Start test: UDP client send then listen - - -")
        self.ads.StartTestSuite(TestSuiteVariable=UDP_CLIENT_TEST_SUITE_START)

        assert self.udp_client.listen(host="0.0.0.0", port=self.udpListenPort), \
            "Failed to start listening"
        logging.info(f"UDP client listening on port {self.udpListenPort}")

        assert wait_until(
            lambda: self.ads.IsTestSuiteDone(UDP_CLIENT_LISTEN_TEST_DONE),
            TIMEOUT_SEC,
            "Wait for listen test to be done",
        ), "Listen test did not complete"

        logging.info(f"Sending data to PLC at {self.plcIp}:{self.udpTestPort}")
        sent_bytes = self.udp_client.send(
            TEST_MESSAGE,
            self.plcIp,
            self.udpTestPort
        )
        assert sent_bytes > 0, "Failed to send initial data to PLC"
        logging.info(f"Sent {sent_bytes} bytes to PLC: {TEST_MESSAGE}")

        assert wait_until(
            self.udp_client.is_data_available,
            TIMEOUT_SEC,
            "Wait for data from PLC",
        ), "No data received from PLC UDP client"

        received_data = self.udp_client.receive()
        assert len(received_data) > 0, "Received data is empty"
        logging.info(f"Received {len(received_data)} bytes: {received_data}")

        assert wait_until(
            lambda: self.ads.IsTestSuiteDone(UDP_CLIENT_TEST_SUITE_DONE),
            TIMEOUT_SEC,
            "Wait for test suite to be done",
        ), "Test suite did not complete"

        logging.info("- - - End test: UDP client send then listen - - -")
