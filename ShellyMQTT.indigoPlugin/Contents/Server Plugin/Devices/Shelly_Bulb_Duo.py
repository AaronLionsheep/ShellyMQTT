# coding=utf-8
import indigo
import json
from Shelly_Dimmer_SL import Shelly_Dimmer_SL


class Shelly_Bulb_Duo(Shelly_Dimmer_SL):
    """
    The Shelly Duo is a light-bulb with dimming, white, and white-temperature control.
    """

    def __init__(self, device):
        Shelly_Dimmer_SL.__init__(self, device)

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
                "{}/light/{}/energy".format(address, self.getChannel())
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
                self.device.updateStateOnServer("whiteLevel", payload['white'])
                self.device.updateStateOnServer("whiteTemperature", payload['temp'])
            else:
                # The light should be off regardless of a reported brightness value
                self.turnOff()
        else:
            Shelly_Dimmer_SL.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.SetColorLevels:
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
            Shelly_Dimmer_SL.handleAction(self, action)

    def set(self):
        """
        Method that sets the data on the device. The Duo has a topic where you set all parameters.

        :return: None
        """

        brightness = self.device.states.get('brightnessLevel', 0)
        white = self.device.states.get('whiteLevel', 0)
        temp = self.device.states.get('whiteTemperature', 5000)
        turn = "on" if brightness >= 1 else "off"
        payload = {
            "turn": turn,
            "brightness": brightness,
            "white": white,
            "temp": temp
        }
        self.publish("{}/light/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))
