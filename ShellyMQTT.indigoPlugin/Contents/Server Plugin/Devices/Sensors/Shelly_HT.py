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
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/sensor/temperature".format(self.getAddress()):
            self.setTemperature(float(payload))
        elif topic == "{}/sensor/humidity".format(self.getAddress()):
            self.device.updateStateOnServer(key="humidity", value=payload, uiValue='{}%'.format(payload))
        elif topic == "{}/sensor/battery".format(self.getAddress()):
            self.device.updateStateOnServer(key="batteryLevel", value=payload, uiValue='{}%'.format(payload))
        else:
            Shelly.handleMessage(self, topic, payload)

        temp_units = self.device.pluginProps.get('temp-units', 'F')[-1]
        self.device.updateStateOnServer(key="status", value='{}°{} / {}%'.format(self.device.states['temperature'], temp_units, self.device.states['humidity']))
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

        Shelly.handleAction(self, action)
