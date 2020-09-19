class IndigoPlugin:

    def __init__(self):
        self.pluginPrefs = {}


class ShellyPlugin(IndigoPlugin):

    def __init__(self):
        IndigoPlugin.__init__(self)
        self.shellyDevices = {}
        self.triggers = {}
        self.lowBatteryThreshold = 20
