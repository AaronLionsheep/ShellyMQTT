# coding=utf-8
import indigo
from Shelly import Shelly


class Shelly_Door_Window(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "{}/sensor/state".format(address),
                "{}/sensor/lux".format(address),
                "{}/sensor/battery".format(address)
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/sensor/state".format(self.getAddress()):
            self.device.updateStateOnServer(key='status', value=payload)
            if self.device.pluginProps['useCase'] == "door":
                if payload == "closed":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.DoorSensorClosed)
                elif payload == "opened":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.DoorSensorOpened)
            elif self.device.pluginProps['useCase'] == "window":
                if payload == "closed":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.WindowSensorClosed)
                elif payload == "opened":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.WindowSensorOpened)
        elif topic == "{}/sensor/lux".format(self.getAddress()):
            self.device.updateStateOnServer(key="lux", value=payload)
        elif topic == "{}/sensor/battery".format(self.getAddress()):
            self.device.updateStateOnServer(key="batteryLevel", value=payload, uiValue='{}%'.format(payload))

    def handleAction(self, action):
        pass
