# coding=utf-8
import indigo
from Shelly_1PM import Shelly_1PM


class Shelly_2_5_Relay(Shelly_1PM):
    """
    The Shelly 2.5 is a relay device that is pretty much two Shelly 1PM's in the same enclosure.
    The each channel is represented by a single Indigo device, so they share internal temperature
    and the online status.
    """

    def __init__(self, device):
        Shelly_1PM.__init__(self, device)

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: The payload of the message.
        :return: None
        """

        if topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            if payload == "overpower":
                self.device.updateStateOnServer('overpower', True)
            else:
                self.device.updateStateOnServer('overpower', False)
                Shelly_1PM.handleMessage(self, topic, payload)
        else:
            Shelly_1PM.handleMessage(self, topic, payload)
