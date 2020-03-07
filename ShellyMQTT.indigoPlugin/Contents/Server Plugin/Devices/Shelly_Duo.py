# coding=utf-8
import indigo
import json
from Shelly import Shelly


class Shelly_Duo(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "shellies/announce",
                "{}/online".format(address),
                "{}/light/{}/status".format(address, self.getChannel()),
                "{}/light/{}/power".format(address, self.getChannel()),
                "{}/light/{}/energy".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/light/{}/status".format(self.getAddress(), self.getChannel()):
            # the payload will be json in the form: {"ison": true/false, "mode": "white", "brightness": x}
            payload = json.loads(payload)
            if payload['ison']:
                # we will accept a brightness value and save it
                self.device.updateStateOnServer("brightnessLevel", payload['brightness'])
                self.device.updateStateOnServer("whiteLevel", payload['white'])
                self.device.updateStateOnServer("whiteTemperature", payload['temp'])
            else:
                # The light should be off regardless of a reported brightness value
                self.turnOff()
        elif topic == "{}/light/{}/power".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('curEnergyLevel', payload, uiValue='{} W'.format(payload))
        elif topic == "{}/light/{}/energy".format(self.getAddress(), self.getChannel()):
            self.updateEnergy(int(payload))
        else:
            Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            self.turnOn()
            self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "on")
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            self.turnOff()
            self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "off")
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            self.device.updateStateOnServer("brightnessLevel", action.actionValue)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
            newBrightness = self.device.brightness + action.actionValue
            if newBrightness > 100:
                newBrightness = 100
            self.device.updateStateOnServer("brightnessLevel", newBrightness)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.DimBy:
            newBrightness = self.device.brightness - action.actionValue
            if newBrightness < 0:
                newBrightness = 0
            self.device.updateStateOnServer("brightnessLevel", newBrightness)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.SetColorLevels:
            if 'whiteLevel' in action.actionValue:
                self.device.updateStateOnServer("whiteLevel", action.actionValue['whiteLevel'])
            if 'whiteTemperature' in action.actionValue:
                self.device.updateStateOnServer("whiteTemperature", action.actionValue['whiteTemperature'])
            self.set()
        elif action.deviceAction == indigo.kUniversalAction.EnergyReset:
            self.resetEnergy()
        elif action.deviceAction == indigo.kUniversalAction.EnergyUpdate:
            # This will be handled by making a status request
            self.sendStatusRequestCommand()
        else:
            Shelly.handleAction(self, action)

    def set(self):
        brightness = self.device.states.get('brightnessLevel', 0)
        white = self.device.states.get('whiteLevel', 0)
        temp = self.device.states.get('whiteTemperature', 5000)
        turn = "on" if brightness >= 1 else "off"
        payload = {
            "turn": turn,
            "brightness": brightness,
            # "white": white,
            # "temp": temp
        }
        self.publish("{}/light/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))
