# coding=utf-8
import indigo
from Shelly_Plug import Shelly_Plug


class Shelly_Plug_S(Shelly_Plug):
    """

    """

    def __init__(self, device):
        Shelly_Plug.__init__(self, device)

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
                "{}/relay/{}/energy".format(address, self.getChannel()),
                "{}/temperature".format(address),
                "{}/overtemperature".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        Shelly_Plug.handleMessage(self, topic, payload)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        return Shelly_Plug.validateConfigUI(valuesDict, typeId, devId)
