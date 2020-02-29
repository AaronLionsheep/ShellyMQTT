# coding=utf-8
import indigo
from Shelly_1 import Shelly_1


class Shelly_1PM(Shelly_1):
    def __init__(self, device):
        Shelly_1.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []

        return [
            "{}/relay/{}".format(address, self.getChannel()),
            "{}/input/{}".format(address, self.getChannel()),
            "{}/longpush/{}".format(address, self.getChannel()),
            "{}/relay/{}/power".format(address, self.getChannel()),
            "{}/relay/{}/energy".format(address, self.getChannel()),
            "{}/temperature".format(address),
            "{}/overtemperature".format(address)
        ]

    def handleMessage(self, topic, payload):
        if topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            if payload == "on":
                self.turnOn()
            elif payload == "off":
                self.turnOff()
        elif topic == "{}/input/{}".format(self.getAddress(), self.getChannel()):
            if payload == '0':
                self.device.updateStateOnServer(key="sw-input", value=False)
            elif payload == '1':
                self.device.updateStateOnServer(key="sw-input", value=True)
        elif topic == "{}/longpush/{}".format(self.getAddress(), self.getChannel()):
            if payload == '0':
                self.device.updateStateOnServer(key="longpush", value=False)
            elif payload == '1':
                self.device.updateStateOnServer(key="longpush", value=True)
        elif topic == "{}/relay/{}/power".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('curEnergyLevel', payload, uiValue='{} W'.format(payload))
        elif topic == "{}/relay/{}/energy".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('accumEnergyTotal', payload, uiValue='{} Wh'.format(payload))
        elif topic == "{}/temperature".format(self.getAddress()):
            self.device.updateStateOnServer('temperature', payload, uiValue='{} °C'.format(payload))
        elif topic == "{}/overtemperature".format(self.getAddress()):
            overtemp = (payload == '1')
            self.device.updateStateOnServer('overtemperature', overtemp)

    def handleAction(self, action):
        if action == indigo.kUniversalAction.EnergyReset:
            self.device.updateStateOnServer('accumEnergyTotal', 0.0)
        else:
            Shelly_1.handleAction(self, action)

    def turnOn(self):
        self.device.updateStateOnServer(key='onOffState', value=True)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.EnergyMeterOn)

    def turnOff(self):
        self.device.updateStateOnServer(key='onOffState', value=False)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.EnergyMeterOff)
