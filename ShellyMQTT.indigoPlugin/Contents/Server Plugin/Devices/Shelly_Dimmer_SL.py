# coding=utf-8
import indigo
import json
from Shelly_1PM import Shelly_1PM


class Shelly_Dimmer_SL(Shelly_1PM):
    def __init__(self, device):
        Shelly_1PM.__init__(self, device)

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
                "{}/light/{}/status".format(address, self.getChannel()),
                "{}/light/{}/power".format(address, self.getChannel()),
                "{}/light/{}/energy".format(address, self.getChannel()),
                "{}/temperature".format(address),
                "{}/overtemperature".format(address),
                "{}/overload".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/light/{}/status".format(self.getAddress(), self.getChannel()):
            # the payload will be json in the form: {"ison": true/false, "mode": "white", "brightness": x}
            payload = json.loads(payload)
            if payload['ison']:
                # we will accept a brightness value and save it
                self.device.updateStateOnServer("brightnessLevel", payload['brightness'])
            else:
                # The light should be off regardless of a reported brightness value
                self.turnOff()
        elif topic == "{}/overload".format(self.getAddress()):
            self.device.updateStateOnServer('overload', (payload == '1'))
        else:
            Shelly_1PM.handleMessage(self, topic.replace("light", "relay"), payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            self.turnOn()
            self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "on")
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            self.turnOff()
            self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "off")
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            self.setAndSendBrightness(action.actionValue)
        elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
            newBrightness = self.device.brightness + action.actionValue
            if newBrightness > 100:
                newBrightness = 100
            self.setAndSendBrightness(newBrightness)
        elif action.deviceAction == indigo.kDeviceAction.DimBy:
            newBrightness = self.device.brightness - action.actionValue
            if newBrightness < 0:
                newBrightness = 0
            self.setAndSendBrightness(newBrightness)
        else:
            Shelly_1PM.handleAction(self, action)

    def setAndSendBrightness(self, level):
        """
        Sets and send the brightness values.

        :param level: The brightness level to set.
        :return: None
        """

        self.device.updateStateOnServer("brightnessLevel", level)
        payload = {
            "turn": "on" if level >= 1 else "off",
            "brightness": level
        }
        self.publish("{}/light/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))
