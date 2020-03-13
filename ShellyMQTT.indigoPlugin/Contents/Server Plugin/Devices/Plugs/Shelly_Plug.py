# coding=utf-8
import indigo
from ..Relays.Shelly_1PM import Shelly_1PM


class Shelly_Plug(Shelly_1PM):
    """

    """

    def __init__(self, device):
        Shelly_1PM.__init__(self, device)

    def getSubscriptions(self):
        """
        Default method to return a list of topics that the device subscribes to.

        :return: A list of topics.
        """

        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "shellies/announce",
                "{}/online".format(address),
                "{}/relay/{}".format(address, self.getChannel()),
                "{}/relay/{}/power".format(address, self.getChannel()),
                "{}/relay/{}/energy".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
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
