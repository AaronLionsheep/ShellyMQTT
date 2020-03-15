# coding=utf-8
import indigo
from Shelly_Addon import Shelly_Addon


class Shelly_Addon_DS1820(Shelly_Addon):
    """
    The Shelly Temperature Add-on is a sensor tht attaches to a host device.
    The host devices can be a Shelly 1 or Shelly 1PM.
    """

    def __init__(self, device):
        Shelly_Addon.__init__(self, device)

    def getSubscriptions(self):
        """
        Default method to return a list of topics that the device subscribes to.

        :return: A list.
        """

        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "{}/online".format(address),
                "{}/ext_temperature/{}".format(address, self.getProbeNumber()),
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/ext_temperature/{}".format(self.getAddress(), self.getProbeNumber()):
            # For some reason, the shelly reports the temperature with a preceding colon...
            temperature = float(payload)
            self.setTemperature(temperature)
        elif topic == "{}/online".format(self.getAddress()):
            Shelly_Addon.handleMessage(self, topic, payload)

        # Update the display state after data changed
        temp = self.device.states['temperature']
        temp_decimals = int(self.device.pluginProps.get('temp-decimals', 1))
        temp_units = self.device.pluginProps.get('temp-units', 'F')[-1]
        self.device.updateStateOnServer(key="status", value='{:.{}f}°{}'.format(temp, temp_decimals, temp_units))

        # Set the icon based on the online status
        if self.device.states.get('online', True):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly_Addon.handleAction(self, action)

    def getProbeNumber(self):
        """
        Getter for the identifier of the probe.

        :return: The probe number to be used in the topic.
        """

        return self.device.pluginProps.get('probe-number', None)
