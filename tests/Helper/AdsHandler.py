import pyads as ads

class AdsHandler:
    def __init__(self, NetID, NetPort):
        self.plc = ads.Connection(NetID, NetPort)

    def OpenConnection(self):
        self.plc.open()

    def CloseConnection(self):
        self.plc.close()

    def GetPlcState(self) -> bool:
        state = self.plc.read_state()
        if state is None:
            raise ValueError("Read state returned None")
        return state[0] == ads.ADSSTATE_RUN
    
    def StartTestSuite(self, TestSuiteVariable):
        self.plc.write_by_name(TestSuiteVariable, True)

    def IsTestSuiteDone(self, TestSuiteVariable) -> bool:
        return self.plc.read_by_name(TestSuiteVariable)
