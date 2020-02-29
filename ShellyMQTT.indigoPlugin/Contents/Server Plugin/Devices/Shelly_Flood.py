# coding=utf-8
import indigo
from Shelly import Shelly


class Shelly_Flood(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "{}/sensor/temperature".format(address),
                "{}/sensor/flood".format(address),
                "{}/sensor/battery".format(address)
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/sensor/temperature".format(self.getAddress()):
            self.device.updateStateOnServer(key="temperature", value=payload, uiValue='{}°F'.format(payload))
        elif topic == "{}/sensor/flood".format(self.getAddress()):
            if payload == 'true':
                self.device.updateStateOnServer(key='onOffState', value=True, uiValue='Wet')
                self.device.updateStateImageOnServer(indigo.kStateImageSel.SprinklerOn)
            elif payload == 'false':
                self.device.updateStateOnServer(key='onOffState', value=False, uiValue='Dry')
                self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
        elif topic == "{}/sensor/battery".format(self.getAddress()):
            self.device.updateStateOnServer(key="batteryLevel", value=payload, uiValue='{}%'.format(payload))

    def handleAction(self, action):
        pass
