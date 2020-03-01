# coding=utf-8
import indigo
import json
from Shelly_1PM import Shelly_1PM


class Shelly_Dimmer_SL(Shelly_1PM):
    def __init__(self, device):
        Shelly_1PM.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "{}/light/{}/status".format(address, self.getChannel()),
                "{}/light/{}/power".format(address, self.getChannel()),
                "{}/light/{}/energy".format(address, self.getChannel()),
                "{}/temperature".format(address),
                "{}/overtemperature".format(address),
                "{}/overload".format(address)
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/light/{}/status".format(self.getAddress(), self.getChannel()):
            # the payload will be json in the form: {"ison": true/false, "mode": "white", "brightness": x}
            payload = json.loads(payload)
            self.device.updateStateOnServer("brightnessLevel", payload['brightness'])
            pass
        elif topic == "{}/overload".format(self.getAddress()):
            self.device.updateStateOnServer('overload', (payload == '1'))
        else:
            Shelly_1PM.handleMessage(self, topic.replace("light", "relay"), payload)

    def handleAction(self, action):
        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            self.turnOn()
            self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "on")
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            self.turnOff()
            self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "off")
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            newBrightness = action.actionValue
            self.setBrightness(newBrightness)
        elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
            newBrightness = self.device.brightness + action.actionValue
            if newBrightness > 100:
                newBrightness = 100
            self.setBrightness(newBrightness)
        elif action.deviceAction == indigo.kDeviceAction.DimBy:
            newBrightness = self.device.brightness - action.actionValue
            if newBrightness < 0:
                newBrightness = 0
            self.setBrightness(newBrightness)
        else:
            Shelly_1PM.handleAction(self, action)

    def setBrightness(self, level):
        self.device.updateStateOnServer("brightnessLevel", level)
        payload = {
            "turn": "on" if level >= 1 else "off",
            "brightness": level
        }
        self.publish("{}/light/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))
