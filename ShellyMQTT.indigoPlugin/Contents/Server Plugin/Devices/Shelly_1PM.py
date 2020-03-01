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
            self.device.updateStateOnServer(key="sw-input", value=(payload == '1'))
        elif topic == "{}/longpush/{}".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer(key="longpush", value=(payload == '1'))
        elif topic == "{}/relay/{}/power".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('curEnergyLevel', payload, uiValue='{} W'.format(payload))
        elif topic == "{}/relay/{}/energy".format(self.getAddress(), self.getChannel()):
            # pluginProps['resetEnergyOffset'] stores the energy reported the last time a reset was requested
            # If this value is greater than the current energy being reported, then the device must have been powered off
            # and reset back to 0.

            resetEnergyOffset = int(self.device.states.get('resetEnergyOffset', 0))
            energy = int(payload) - resetEnergyOffset
            if energy < 0:  # If the offset is greater than what is being reported, the device must have reset
                # our last known energy total can be used to determine the previous energy usage
                self.logger.info(u"%s: Must have lost power and the energy usage has reset to 0. Determining previous usage based on last know energy usage value...")
                resetEnergyOffset = self.device.states.get('accumEnergyTotal', 0) * 60 * 1000 * -1
                self.device.updateStateOnServer('resetEnergyOffset', resetEnergyOffset)
                energy = int(payload) - resetEnergyOffset

            kwh = float(energy) / 60 / 1000  # energy is reported in watt-minutes
            if kwh < 0.01:
                uiValue = '{:.4f} kWh'.format(kwh)
            elif kwh < 1:
                uiValue = '{:.3f} kWh'.format(kwh)
            else:
                uiValue = '{:.1f} kWh'.format(kwh)

            self.device.updateStateOnServer('accumEnergyTotal', kwh, uiValue=uiValue)
        elif topic == "{}/temperature".format(self.getAddress()):
            self.setTemperature(float(payload))
        elif topic == "{}/overtemperature".format(self.getAddress()):
            self.device.updateStateOnServer('overtemperature', (payload == '1'))

    def handleAction(self, action):
        if action == indigo.kUniversalAction.EnergyReset:
            # We can't tell the device to reset it's internal energy usage
            # Record the current value being reported so we can offset from it later on
            currEnergyWattMins = self.device.states.get('accumEnergyTotal', 0) * 60 * 1000
            previousResetEnergyOffset = int(self.device.states.get('resetEnergyOffset', 0))
            offset = currEnergyWattMins + previousResetEnergyOffset
            self.device.updateStateOnServer('resetEnergyOffset', offset)
            self.device.updateStateOnServer('accumEnergyTotal', 0.0)
        else:
            Shelly_1.handleAction(self, action)

    def turnOn(self):
        self.device.updateStateOnServer(key='onOffState', value=True)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.EnergyMeterOn)

    def turnOff(self):
        self.device.updateStateOnServer(key='onOffState', value=False)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.EnergyMeterOff)
