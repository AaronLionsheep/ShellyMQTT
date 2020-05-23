# coding=utf-8
import indigo
import json
from ..Relays.Shelly_1PM import Shelly_1PM


class Shelly_RGBW2_Color(Shelly_1PM):
    """
    The Shelly Duo is a light-bulb with dimming, white, and white-temperature control.
    """

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
                "{}/color/{}/status".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/color/{}/status".format(self.getAddress(), self.getChannel()):
            # the payload will be json in the form
            # {
            #     "ison",            /* whether the output is ON or OFF */
            #     "has_timer",       /* whether a timer is currently armed for this channel */
            #     "timer_remaining", /* if there is an active timer, shows seconds until timer elapses; 0 otherwise */
            #     "mode",            /* currently configured mode */
            #     "red",             /* red brightness, 0..255 */
            #     "green",           /* green brightness, 0..255 */
            #     "blue",            /* blue brightness, 0..255 */
            #     "white",           /* white brightness, 0..255 */
            #     "gain",            /* gain for all channels, 0..100 */
            #     "effect",          /* applied effect */
            #     "power",           /* consumed power, W */
            #     "overpower"        /* whether an overpower condition has occurred */
            # }
            try:
                payload = json.loads(payload)
                if payload.get("mode", "") != "color":
                    self.logger.error(u"\"{}\" expects the device to be in mode \"color\", but is in mode \"{}\"".format(self.device.name, payload.get("mode", "")))
                    return

                if payload.get("ison", False):
                    # we will accept a brightness value and save it
                    if self.isOff():
                        self.logger.info(u"\"{}\" on to {}%".format(self.device.name, payload['gain']))
                    elif self.device.states['brightnessLevel'] != payload['gain']:
                        # Brightness will change
                        self.logger.info(u"\"{}\" set to {}%".format(self.device.name, payload['gain']))

                    self.applyBrightness(payload['gain'])
                else:
                    # The light should be off regardless of a reported brightness value
                    self.turnOff()

                # Record the color data
                self.device.updateStateOnServer("redLevel", payload.get("red", 0))
                self.device.updateStateOnServer("greenLevel", payload.get("green", 0))
                self.device.updateStateOnServer("blueLevel", payload.get("blue", 0))
                self.device.updateStateOnServer("whiteLevel", payload.get("white", 0))

                # Record the overpower status
                overloaded = payload.get("overpower", False)
                if not self.device.states['overpower'] and overloaded:
                    self.logger.error(u"\"{}\" was overloaded!".format(self.device.name))
                self.device.updateStateOnServer('overpower', overloaded)

                # Record the current power
                power = payload.get("power", None)
                if power is not None:
                    self.device.updateStateOnServer('curEnergyLevel', power, uiValue='{} W'.format(power))

            except ValueError:
                self.logger.error(u"Problem parsing JSON: {}".format(payload))
        else:
            Shelly_1PM.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.SetColorLevels:
            if 'whiteLevel' in action.actionValue:
                self.device.updateStateOnServer("whiteLevel", int(action.actionValue['whiteLevel']))
            if 'redLevel' in action.actionValue:
                self.device.updateStateOnServer("redLevel", int(action.actionValue['redLevel']))
            if 'greenLevel' in action.actionValue:
                self.device.updateStateOnServer("greenLevel", int(action.actionValue['greenLevel']))
            if 'blueLevel' in action.actionValue:
                self.device.updateStateOnServer("blueLevel", int(action.actionValue['blueLevel']))
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.TurnOn:
            self.applyBrightness(100)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            self.applyBrightness(0)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            self.applyBrightness(action.actionValue)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
            newBrightness = min(100, self.device.brightness + action.actionValue)
            self.applyBrightness(newBrightness)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.DimBy:
            newBrightness = max(0, self.device.brightness - action.actionValue)
            self.applyBrightness(newBrightness)
            self.set()
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            # Override the toggle since dimmer's need their brightness set.
            if self.isOn():
                self.applyBrightness(0)
                self.set()
            elif self.isOff():
                self.applyBrightness(100)
                self.set()
        else:
            Shelly_1PM.handleAction(self, action)

    def applyBrightness(self, brightness):
        """
        Updates the device states with the appropriate values based on the brightness value.

        :param brightness: The brightness value to set.
        :return: None
        """

        if brightness > 0:
            if self.device.states['brightnessLevel'] != brightness:
                if self.isOn():
                    self.logger.info(u"\"{}\" set to {}%".format(self.device.name, brightness))
                else:
                    self.logger.info(u"\"{}\" on to {}%".format(self.device.name, brightness))
            self.turnOn()
        else:
            self.turnOff()

        self.device.updateStateOnServer("brightnessLevel", brightness)

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
            self.publish("{}/color/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))
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

        return Shelly_1PM.validateConfigUI(valuesDict, typeId, devId)