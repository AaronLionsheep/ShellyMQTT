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

        Shelly_1PM.handleMessage(self, topic, payload)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        return Shelly_1PM.validateConfigUI(valuesDict, typeId, devId)