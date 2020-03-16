# coding=utf-8
import indigo
from ..Shelly import Shelly


class Shelly_HT(Shelly):
    """
    The Shelly H&T is a small temperature and humidity sensor.
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
                "{}/sensor/humidity".format(address),
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
        elif topic == "{}/sensor/humidity".format(self.getAddress()):
            decimals = int(self.device.pluginProps.get('humidity-decimals', 1))
            offset = 0
            try:
                offset = float(self.device.pluginProps.get('humidity-offset', 0))
            except ValueError:
                self.logger.error(u"Unable to convert offset of \"{}\" into a float!".format(self.device.pluginProps.get('humidity-offset', 0)))

            humidity = float(payload) + offset
            self.device.updateStateOnServer(key="humidity", value=humidity, uiValue='{:.{}f}%'.format(humidity, decimals), decimalPlaces=decimals)
        elif topic == "{}/sensor/battery".format(self.getAddress()):
            self.device.updateStateOnServer(key="batteryLevel", value=payload, uiValue='{}%'.format(payload))
        else:
            Shelly.handleMessage(self, topic, payload)

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

        Shelly.handleAction(self, action)

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return:
        """

        if self.device.states.get('online', True):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
