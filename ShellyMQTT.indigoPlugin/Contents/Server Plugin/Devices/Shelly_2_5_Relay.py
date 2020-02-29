# coding=utf-8
import indigo
from Shelly_1PM import Shelly_1PM


class Shelly_2_5_Relay(Shelly_1PM):
    def __init__(self, device):
        Shelly_1PM.__init__(self, device)

    def handleMessage(self, topic, payload):
        if topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            if payload == "overpower":
                self.device.updateStateOnServer('overpower', True)
            else:
                self.device.updateStateOnServer('overpower', False)
                Shelly_1PM.handleMessage(self, topic, payload)
        else:
            Shelly_1PM.handleMessage(self, topic, payload)
