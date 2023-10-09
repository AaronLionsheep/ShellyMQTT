# coding=utf-8
import indigo
from ..Shelly import Shelly


class Shelly_Flood(Shelly):
    """
    The Shelly Flood is a small flood detector that also reports temperature.
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
                "{}/sensor/temperature".format(address),
                "{}/sensor/flood".format(address),
                "{}/sensor/battery".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: The payload of the message.
        :return: None
        """

        if topic == "{}/sensor/temperature".format(self.getAddress()):
            self.setTemperature(float(payload))
        elif topic == "{}/sensor/flood".format(self.getAddress()):
            if self.device.states['onOffState'] != (payload == 'true'):
                self.logCommandReceived("{}".format("wet" if (payload == 'true') else "dry"))
            if payload == 'true':
                self.device.updateStateOnServer(key='onOffState', value=True, uiValue='wet')
            elif payload == 'false':
                self.device.updateStateOnServer(key='onOffState', value=False, uiValue='dry')

            self.updateStateImage()
        elif topic == "{}/sensor/battery".format(self.getAddress()):
            Shelly.updateBatteryLevel(self, payload)
        else:
            Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly.handleAction(self, action)

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return: None
        """

        if self.device.states['onOffState']:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)
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

        # Validate that the temperature offset is a valid number
        temperature_offset = valuesDict.get("temp-offset", None)
        if temperature_offset != "":
            try:
                float(temperature_offset)
            except ValueError:
                isValid = False
                errors["temp-offset"] = u"Unable to convert to a float."

        return isValid, valuesDict, errors
