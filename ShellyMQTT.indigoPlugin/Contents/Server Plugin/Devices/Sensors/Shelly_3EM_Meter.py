# coding=utf-8
import indigo
from .Shelly_EM_Meter import Shelly_EM_Meter


class Shelly_3EM_Meter(Shelly_EM_Meter):
    """
    The Shelly 2.5 is a relay device that is pretty much two Shely 1PM's in the same enclosure.
    The each channel is represented by a single Indigo device, so they share internal temperature
    and the online status.
    """

    def __init__(self, device):
        Shelly_EM_Meter.__init__(self, device)

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
                "{}/emeter/{}/energy".format(address, self.getChannel()),
                "{}/emeter/{}/returned_energy".format(address, self.getChannel()),
                "{}/emeter/{}/power".format(address, self.getChannel()),
                "{}/emeter/{}/reactive_power".format(address, self.getChannel()),
                "{}/emeter/{}/voltage".format(address, self.getChannel()),
                "{}/emeter/{}/current".format(address, self.getChannel()),
                "{}/emeter/{}/pf".format(address, self.getChannel()),
                "{}/emeter/{}/total".format(address, self.getChannel()),
                "{}/emeter/{}/total_returned".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/emeter/{}/current".format(self.getAddress(), self.getChannel()):
            try:
                current = float(payload)
                self.device.updateStateOnServer('current', current, uiValue="{:.1f} A".format(current), decimalPlaces=1)
            except ValueError:
                self.logger.error(u"Unable to convert current of \"{}\" to a float!".format(payload))
        if topic == "{}/emeter/{}/pf".format(self.getAddress(), self.getChannel()):
            try:
                pf = float(payload)
                self.device.updateStateOnServer('power-factor', pf, uiValue="{:.1f}".format(pf), decimalPlaces=1)
            except ValueError:
                self.logger.error(u"Unable to convert power-factor of \"{}\" to a float!".format(payload))
        else:
            Shelly_EM_Meter.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly_EM_Meter.handleAction(self, action)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        return Shelly_EM_Meter.validateConfigUI(valuesDict, typeId, devId)
