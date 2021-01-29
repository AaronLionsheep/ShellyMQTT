# coding=utf-8
import indigo
from ..Shelly import Shelly


class Shelly_Button1(Shelly):
    """

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
                "shellies/announce",
                "{}/online".format(address),
                "{}/sensor/battery".format(address),
                "{}/input_event/{}".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: The payload of the message.
        :return: None
        """

        if topic == "{}/sensor/battery".format(self.getAddress()):
            Shelly.updateBatteryLevel(self, payload)
            self.device.updateStateOnServer(key="sensorValue", value=payload, uiValue='{}%'.format(payload))
        else:
            Shelly.handleMessage(self, topic, payload)

        # Update the display state after data changed
        self.updateStateImage()

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.sendStatusRequestCommand()

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return: None
        """

        """
        if self.device.states.get('onOffState', True):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
        """
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

        errors = indigo.Dict()
        isValid = True
        # The Shelly 1 needs to ensure the user has selected a Broker device, supplied the address, and supplied the message type.
        # If the user has indicated that announcement messages are separate, then they need to supply that message type as well.

        # Validate the broker
        brokerId = valuesDict.get('broker-id', None)
        if not brokerId.strip():
            isValid = False
            errors['broker-id'] = u"You must select the broker to which the Shelly is connected to."

        # Validate the address
        address = valuesDict.get('address', None)
        if not address.strip():
            isValid = False
            errors['address'] = u"You must enter the MQTT topic root for the Shelly."

        # Validate the message type
        messageType = valuesDict.get('message-type', None)
        if not messageType.strip():
            isValid = False
            errors['message-type'] = u"You must enter the message type that this Shelly will be associated with."

        # Validate the announcement message type
        hasSameAnnounceMessageType = valuesDict.get('announce-message-type-same-as-message-type', True)
        if not hasSameAnnounceMessageType:  # We would expect a supplied message type for announcement messages
            announceMessageType = valuesDict.get('announce-message-type', None)
            if not announceMessageType.strip():
                isValid = False
                errors['announce-message-type'] = u"You must supply the message type that will be associated with the announce messages."

        return isValid, valuesDict, errors
