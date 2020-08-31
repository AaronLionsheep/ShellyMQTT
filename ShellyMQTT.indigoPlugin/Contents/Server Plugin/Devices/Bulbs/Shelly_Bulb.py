# coding=utf-8
import indigo
import json
from Shelly_Bulb_Vintage import Shelly_Bulb_Vintage


class Shelly_Bulb(Shelly_Bulb_Vintage):
    """
    The Shelly Duo is a light-bulb with dimming, white, and white-temperature control.
    """

    def __init__(self, device):
        Shelly_Bulb_Vintage.__init__(self, device)

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
            # the payload will be json in the form
            # {
            #     "ison": false,        /* whether the bulb is on */
            #     "has_timer": false,   /* whether a timer is currently armed */
            #     "timer_remaining": 0, /* if there is an active timer, shows seconds until timer elapses; 0 otherwise */
            #     "mode": "color",      /* currently configured mode */
            #     "red": 255,           /* red brightness, 0..255, applies in mode="color" */
            #     "green": 125,         /* green brightness, 0..255, applies in mode="color" */
            #     "blue": 0,            /* blue brightness, 0..255, applies in mode="color" */
            #     "white": 0,           /* white brightness, 0..255, applies in mode="color" */
            #     "gain": 100,          /* gain for all channels, 0..100, applies in mode="color" */
            #     "temp": 5406,         /* color temperature in K, 3000..6500, applies in mode="white" */
            #     "brightness": 90,     /* brightness, 0..100, applies in mode="white" */
            #     "effect": 0           /* currently applied effect */
            # }
            try:
                payload = json.loads(payload)
                if payload['ison']:
                    # we will accept a brightness value and save it
                    self.device.updateStateOnServer("brightnessLevel", payload['brightness'])
                    self.turnOn()
                else:
                    # The light should be off regardless of a reported brightness value
                    self.turnOff()

                # Record the color data
                self.device.updateStateOnServer("redLevel", payload.get("red", 0))
                self.device.updateStateOnServer("greenLevel", payload.get("green", 0))
                self.device.updateStateOnServer("blueLevel", payload.get("blue", 0))
                self.device.updateStateOnServer("whiteLevel", payload.get("white", 0))
            except ValueError:
                self.logger.error(u"Problem parsing JSON: {}".format(payload))
        else:
            Shelly_Bulb_Vintage.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.SetColorLevels:
            if 'whiteLevel' in action.actionValue:
                self.device.updateStateOnServer("whiteLevel", action.actionValue['whiteLevel'])
            if 'redLevel' in action.actionValue:
                self.device.updateStateOnServer("redLevel", int(action.actionValue['redLevel']))
            if 'greenLevel' in action.actionValue:
                self.device.updateStateOnServer("greenLevel", int(action.actionValue['greenLevel']))
            if 'blueLevel' in action.actionValue:
                self.device.updateStateOnServer("blueLevel", int(action.actionValue['blueLevel']))
            self.set()
        else:
            Shelly_Bulb_Vintage.handleAction(self, action)

    def set(self):
        """
        Method that sets the data on the device. The Duo has a topic where you set all parameters.

        :return: None
        """

        red = self.device.states.get('redLevel', 0)
        green = self.device.states.get('greenLevel', 0)
        blue = self.device.states.get('blueLevel', 0)
        white = self.device.states.get('whiteLevel', 0)
        brightness = self.device.states.get('brightnessLevel', 0)
        turn = "on" if brightness >= 1 else "off"

        # Ensure all values are in the 8-bit range
        red, green, blue, white, brightness = (min(255, max(0, c)) for c in (red, green, blue, white, brightness))

        payload = {
            "mode": "color",
            "turn": turn,
            "white": white,
            "red": red,
            "blue": blue,
            "green": green,
            "gain": brightness
        }

        try:
            self.publish("{}/light/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))
        except ValueError:
            self.logger.error(u"Problem building JSON: {}".format(payload))

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        return Shelly_Bulb_Vintage.validateConfigUI(valuesDict, typeId, devId)
