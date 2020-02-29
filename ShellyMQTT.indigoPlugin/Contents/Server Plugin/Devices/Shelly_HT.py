# coding=utf-8
import indigo
from Shelly import Shelly


class Shelly_HT(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "{}/sensor/temperature".format(address),
                "{}/sensor/humidity".format(address),
                "{}/sensor/battery".format(address)
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/sensor/temperature".format(self.getAddress()):
            self.device.updateStateOnServer(key="temperature", value=payload, uiValue='{}°F'.format(payload))
        elif topic == "{}/sensor/humidity".format(self.getAddress()):
            self.device.updateStateOnServer(key="humidity", value=payload, uiValue='{}%'.format(payload))
        elif topic == "{}/sensor/battery".format(self.getAddress()):
            self.device.updateStateOnServer(key="batteryLevel", value=payload, uiValue='{}%'.format(payload))

        self.device.updateStateOnServer(key="status", value='{}°F / {}%'.format(self.device.states['temperature'], self.device.states['humidity']))
        self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)

    def handleAction(self, action):
        pass
