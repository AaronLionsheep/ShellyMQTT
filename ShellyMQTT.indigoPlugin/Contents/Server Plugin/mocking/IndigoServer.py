from MQTTConnector import MQTTConnector
from IndigoPlugin import IndigoPlugin


class Indigo:

    def __init__(self):
        self.server = IndigoServer()
        self.kStateImageSel = StateImages()
        self.kDeviceAction = DeviceActions()
        self.kUniversalAction = UniversalActions()
        self.activePlugin = IndigoPlugin()


class IndigoServer:

    def __init__(self):
        self.plugins = {
            "com.flyingdiver.indigoplugin.mqtt": MQTTConnector()
        }

    def getPlugin(self, identifier):
        return self.plugins.get(identifier, None)


class StateImages:

    def __init__(self):
        self.PowerOn = "PowerOn"
        self.PowerOff = "PowerOff"


class DeviceActions:

    def __init__(self):
        self.TurnOn = "TurnOn"
        self.TurnOff = "TurnOff"
        self.Toggle = "Toggle"
        self.RequestStatus = "RequestStatus"


class UniversalActions:

    def __init__(self):
        self.EnergyReset = "EnergyReset"
        self.EnergyUpdate = "EnergyUpdate"

