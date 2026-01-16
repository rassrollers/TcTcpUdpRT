from tests.common import PLCSettings
import pytest

    
def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--plc.ip", action="store", default="192.168.1.10")
    parser.addoption("--plc.netid", action="store", default="192.168.17.10.1.1")
    parser.addoption("--plc.netport", action="store", default=851)
    parser.addoption("--plc.serverport", action="store", default=9900)
    parser.addoption("--plc.clientport", action="store", default=9901)


def pytest_collection_modifyitems(config, items):
    file_order = ["test_PlcTcpServer.py", "test_PlcTcpClient.py"]

    def sort_key(item):
        # file priority
        file_priority = file_order.index(item.location[0].split("/")[-1]) if item.location[0].split("/")[-1] in file_order else 999
        # class priority
        return (file_priority)
    
    items.sort(key=sort_key)


@pytest.fixture
def plc_options(pytestconfig) -> PLCSettings:
    settings = PLCSettings(
        pytestconfig.getoption("plc.ip"),
        pytestconfig.getoption("plc.netid"),
        pytestconfig.getoption("plc.netport"),
        pytestconfig.getoption("plc.serverport"),
        pytestconfig.getoption("plc.clientport"),
    )
    return settings
    