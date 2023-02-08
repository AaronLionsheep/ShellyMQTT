# coding=utf-8
import indigo
import json
from .Shelly_Addon import Shelly_Addon


class Shelly_Addon_DHT22(Shelly_Addon):
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
                "{}/ext_temperatures".format(address),
                "{}/ext_humidity/{}".format(address, self.getProbeNumber()),
                "{}/ext_humidities".format(address)
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
            temperature = payload
            try:
                self.setTemperature(float(temperature))
            except ValueError:
                self.logger.error(u"Unable to convert value of \"{}\" into a float!".format(payload))
        elif topic == "{}/ext_humidity/{}".format(self.getAddress(), self.getProbeNumber()):
            decimals = int(self.device.pluginProps.get('humidity-decimals', 1))
            offset = 0
            try:
                offset = float(self.device.pluginProps.get('humidity-offset', 0))
            except ValueError:
                self.logger.error(u"Unable to convert offset of \"{}\" into a float!".format(self.device.pluginProps.get('humidity-offset', 0)))

            try:
                humidity = float(payload) + offset
                self.device.updateStateOnServer(key="humidity", value=humidity, uiValue='{:.{}f}%'.format(humidity, decimals), decimalPlaces=decimals)
            except ValueError:
                self.logger.error(u"Unable to convert value of \"{}\" into a float!".format(payload))
        elif topic == "{}/ext_temperatures".format(self.getAddress()) and len(self.getProbeNumber()) > 1:
            try:
                data = json.loads(payload)
                for sensor in data.values():
                    if sensor['hwID'] == self.getProbeNumber():
                        value = sensor['tC']
                        self.handleMessage("{}/ext_temperature/{}".format(self.getAddress(), self.getProbeNumber()), value)
                        break
            except ValueError:
                self.logger.warn("Unable to convert payload to json: {}".format(payload))
        elif topic == "{}/ext_humidities".format(self.getAddress()) and len(self.getProbeNumber()) > 1:
            try:
                data = json.loads(payload)
                for sensor in data.values():
                    if sensor['hwID'] == self.getProbeNumber():
                        value = sensor['hum']
                        self.handleMessage("{}/ext_humidity/{}".format(self.getAddress(), self.getProbeNumber()), value)
                        break
            except ValueError:
                self.logger.warn("Unable to convert payload to json: {}".format(payload))
        elif topic == "{}/online".format(self.getAddress()):
            Shelly_Addon.handleMessage(self, topic, payload)

        # Set the display state after data changed
        temp = self.device.states['temperature']
        temp_decimals = int(self.device.pluginProps.get('temp-decimals', 1))
        temp_units = self.device.pluginProps.get('temp-units', 'F')[-1]
        humidity = self.device.states['humidity']
        humidity_decimals = int(self.device.pluginProps.get('humidity-decimals', 1))
        self.device.updateStateOnServer(key="status", value='{:.{}f}°{} / {:.{}f}%'.format(temp, temp_decimals, temp_units, humidity, humidity_decimals))
        self.updateStateImage()

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly_Addon.handleAction(self, action)

    def getProbeNumber(self):
        """
        Getter for the identifier of the probe. For now, a single DHT22 will be on a host device.

        :return: The probe number to be used in the topic.
        """

        return self.device.pluginProps.get('probe-number', None)

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return:
        """

        if self.device.states.get('online', True):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        isValid, valuesDict, errors = Shelly_Addon.validateConfigUI(valuesDict, typeId, devId)

        # Validate that the temperature offset is a valid number
        temperature_offset = valuesDict.get("temp-offset", None)
        if temperature_offset != "":
            try:
                float(temperature_offset)
            except ValueError:
                isValid = False
                errors["temp-offset"] = u"Unable to convert to a float."

        # Validate that the humidity offset is a valid number
        humidity_offset = valuesDict.get("humidity-offset", None)
        if humidity_offset != "":
            try:
                float(humidity_offset)
            except ValueError:
                isValid = False
                errors["humidity-offset"] = u"Unable to convert to a float."

        return isValid, valuesDict, errors
