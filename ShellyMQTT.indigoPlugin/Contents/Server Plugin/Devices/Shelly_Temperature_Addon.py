# coding=utf-8
import indigo
from Shelly import Shelly


class Shelly_Temperature_Addon(Shelly):
    """
    The Shelly Temperature Add-on is a sensor tht attaches to a host device.
    The host devices can be a Shelly 1 or Shelly 1PM.
    """

    def __init__(self, device):
        Shelly.__init__(self, device)

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
            temperature = payload[1:]
            self.setTemperature(float(temperature))

        elif topic == "{}/online".format(self.getAddress()):
            Shelly.handleMessage(self, topic, payload)

        temp_units = self.device.pluginProps.get('temp-units', 'F')[-1]
        self.device.updateStateOnServer(key="status", value='{}°{}'.format(self.device.states['temperature'], temp_units))

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

        pass

    def getProbeNumber(self):
        """
        Getter for the identifier of the probe.

        :return: The probe number to be used in the topic.
        """

        return self.device.pluginProps.get('probe-number', None)

    def getHostDevice(self):
        """
        Getter for the host device.

        :return: The Shelly object that the sensor is attached to.
        """

        dev = self.device.pluginProps.get('host-id', None)
        if dev:
            return indigo.activePlugin.shellyDevices.get(int(dev), None)

    def getBrokerId(self):
        """
        Getter for the broker id.

        :return: The broker id of the host device.
        """

        if self.getHostDevice():
            return self.getHostDevice().getBrokerId()
        else:
            return None

    def getAddress(self):
        """
        Getter for the address.

        :return: The address of the host device.
        """

        if self.getHostDevice():
            return self.getHostDevice().getAddress()
        else:
            return None

    def getMessageType(self):
        """
        Getter for the message type.

        :return: The message type of the host device.
        """

        if self.getHostDevice():
            return self.getHostDevice().getMessageType()
        else:
            return None

    def getMessageTypes(self):
        """
        Getter for the message types.

        :return: A list of message type being listened to.
        """

        if self.getHostDevice():
            return [self.getHostDevice().getMessageType()]
        else:
            return []
