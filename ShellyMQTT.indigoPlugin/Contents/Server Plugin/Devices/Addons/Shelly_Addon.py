# coding=utf-8
import indigo
import json
from ..Shelly import Shelly


class Shelly_Addon(Shelly):
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

        pass

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.getHostDevice().sendStatusRequestCommand()

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

    def getIpAddress(self):
        """
        Helper function to get the ip address of the device.

        :return: The device ip address
        """

        if self.getHostDevice():
            return self.getHostDevice().getIpAddress()
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

    def isAddon(self):
        """
        Helper method to determine if a device is an addon device. This defaults to false since most devices
        are not add-ons.

        :return: True if the device is an addon.
        """

        return True

    def parseAnnouncement(self, payload):
        """
        Parses the data from an announce message. The payload is expected to be of the form:
        {
            "id": <SOME_ID>,
            "mac": <MAC_ADDRESS>,
            "ip": <IP_ADDRESS>,
            "fw_ver": <FIRMWARE_VERSION>,
            "new_fw": <true/false>
        }

        :param payload: The payload of the announce message.
        :return: None
        """

        pass

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        errors = indigo.Dict()
        isValid = True
        # The Shelly 1 needs to ensure the user has selected a Broker device, supplied the address, and supplied the message type.
        # If the user has indicated that announcement messages are separate, then they need to supply that message type as well.

        # Validate the broker
        brokerId = valuesDict.get('host-id', None)
        if not brokerId.strip():
            isValid = False
            errors['host-id'] = u"You must select the broker to which the Shelly is connected to."

        return isValid, valuesDict, errors
