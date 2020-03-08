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
        else:
            return [
                "shellies/announce",
                "{}/online".format(address),
                "{}/relay/{}".format(address, self.getChannel()),
                "{}/input/{}".format(address, self.getChannel()),
                "{}/longpush/{}".format(address, self.getChannel()),
                "{}/relay/{}/power".format(address, self.getChannel()),
                "{}/relay/{}/energy".format(address, self.getChannel()),
                "{}/temperature".format(address),
                "{}/overtemperature".format(address)
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/relay/{}/power".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('curEnergyLevel', payload, uiValue='{} W'.format(payload))
        elif topic == "{}/relay/{}/energy".format(self.getAddress(), self.getChannel()):
            self.updateEnergy(int(payload))
        elif topic == "{}/temperature".format(self.getAddress()):
            self.setTemperature(float(payload), state='internal-temperature', unitsProps='int-temp-units')
        elif topic == "{}/overtemperature".format(self.getAddress()):
            self.device.updateStateOnServer('overtemperature', (payload == '1'))
        elif topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('overpower', (payload == 'overpower'))
        else:
            Shelly_1.handleMessage(self, topic, payload)

    def handleAction(self, action):
        if action.deviceAction == indigo.kUniversalAction.EnergyReset:
            self.resetEnergy()
        elif action.deviceAction == indigo.kUniversalAction.EnergyUpdate:
            # This will be handled by making a status request
            self.sendStatusRequestCommand()
        else:
            Shelly_1.handleAction(self, action)
