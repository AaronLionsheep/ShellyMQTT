# coding=utf-8
import indigo
from Shelly import Shelly


class Shelly_Temperature_Addon(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "{}/online".format(address),
                "{}/ext_temperature/{}".format(address, self.getProbeNumber()),
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/ext_temperature/{}".format(self.getAddress(), self.getProbeNumber()):
            # For some reason, the shelly reports the temperature with a preceding colon...
            temperature = payload[1:]
            self.setTemperature(float(temperature))
        elif topic == "{}/online".format(self.getAddress()):
            Shelly.handleMessage(self, topic, payload)

        temp_units = self.device.pluginProps.get('temp-units', 'F')[-1]
        self.device.updateStateOnServer(key="status", value='{}°{}'.format(self.device.states['temperature'], temp_units))
        if self.device.states.get('online', True):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)

    def handleAction(self, action):
        pass

    def getProbeNumber(self):
        return self.device.pluginProps.get('probe-number', None)

    def getHostDevice(self):
        dev = self.device.pluginProps.get('host-id', None)
        if dev:
            return indigo.activePlugin.shellyDevices.get(int(dev), None)

    def getBrokerId(self):
        if self.getHostDevice():
            return self.getHostDevice().getBrokerId()
        else:
            return None

    def getAddress(self):
        if self.getHostDevice():
            return self.getHostDevice().getAddress()
        else:
            return None

    def getMessageType(self):
        if self.getHostDevice():
            return self.getHostDevice().getMessageType()
        else:
            return None

    def getMessageTypes(self):
        if self.getHostDevice():
            return [
                self.getHostDevice().getMessageType()
            ]
        else:
            return []
