# coding=utf-8
import indigo
from .Shelly_Addon import Shelly_Addon


class Shelly_Addon_Detached_Switch(Shelly_Addon):
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
                "{}/input/{}".format(address, self.getChannel()),
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/input/{}".format(self.getAddress(), self.getChannel()):
            # For some reason, the shelly reports the temperature with a preceding colon...
            invert = self.device.pluginProps.get("invert", False)
            state = (payload == '0') if invert else (payload == '1')
            if self.device.states['onOffState'] != state:
                self.logCommandReceived("{}".format("on" if state else "off"))
            self.device.updateStateOnServer(key="onOffState", value=state)
        elif topic == "{}/online".format(self.getAddress()):
            Shelly_Addon.handleMessage(self, topic, payload)

        # Update the display state after data changed
        # self.device.updateStateOnServer(key="status", value='{}'.format("on" if self.device.states.get("sw-input", False) else "off"))
        self.updateStateImage()

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly_Addon.handleAction(self, action)

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return: None
        """

        if self.device.states.get('onOffState', True):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        return Shelly_Addon.validateConfigUI(valuesDict, typeId, devId)
