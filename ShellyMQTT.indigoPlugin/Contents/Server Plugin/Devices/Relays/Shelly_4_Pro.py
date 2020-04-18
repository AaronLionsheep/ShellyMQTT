# coding=utf-8
import indigo
from Shelly_1PM import Shelly_1PM


class Shelly_4_Pro(Shelly_1PM):
    """
    The Shelly 4Pro is a relay device that is four Shelly 1PM's in the same din-mountable enclosure.
    The each channel is represented by a single Indigo device.
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
                "{}/input/{}".format(address, self.getChannel()),
                "{}/relay/{}/power".format(address, self.getChannel()),
                "{}/relay/{}/energy".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: The payload of the message.
        :return: None
        """

        Shelly_1PM.handleMessage(self, topic, payload)
