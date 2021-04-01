# coding=utf-8
import indigo
import json
from Relays.Shelly_1PM import Shelly_1PM


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
                "{}/input/{}".format(address, self.getChannel()),
                "{}/light/{}/status".format(address, self.getChannel()),
                "{}/light/{}/power".format(address, self.getChannel()),
                "{}/light/{}/energy".format(address, self.getChannel()),
                "{}/temperature".format(address),
                "{}/overtemperature".format(address),
                "{}/overload".format(address),
                "{}/input_event/{}".format(address, self.getChannel())
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
            try:
                payload = json.loads(payload)
                if payload['ison']:
                    # we will accept a brightness value and save it

                    if self.isOff():
                        # self.logger.info(u"\"{}\" on to {}%".format(self.device.name, payload['brightness']))
                        self.logCommandReceived(u"brightness to {}%".format(payload['brightness']))
                    elif self.device.states['brightnessLevel'] != payload['brightness']:
                        # Brightness will change
                        # self.logger.info(u"\"{}\" set to {}%".format(self.device.name, payload['brightness']))
                        self.logCommandReceived(u"brightness to {}%".format(payload['brightness']))

                    self.applyBrightness(payload['brightness'])
                else:
                    # The light should be off regardless of a reported brightness value
                    if not self.isOff():
                        self.logCommandReceived("off")
                    self.turnOff()
            except ValueError:
                self.logger.error(u"Problem parsing JSON: {}".format(payload))
        elif topic == "{}/overload".format(self.getAddress()):
            overloaded = (payload == '1')
            if not self.device.states['overload'] and overloaded:
                self.logger.error(u"\"{}\" was overloaded!".format(self.device.name))
            self.device.updateStateOnServer('overload', overloaded)
        else:
            Shelly_1PM.handleMessage(self, topic.replace("light", "relay"), payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        def on():
            if self.device.pluginProps.get('restore-brightness', False):
                # Turn on without passing a brightness
                self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "on")
            else:
                self.applyBrightness(100)
                self.set()
            self.logCommandSent("on")

        def off():
            if self.device.pluginProps.get('restore-brightness', False):
                # Turn off without passing a brightness
                self.publish("{}/light/{}/command".format(self.getAddress(), self.getChannel()), "off")
            else:
                self.applyBrightness(0)
                self.set()
            self.logCommandSent("off")

        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            on()
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            off()
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            self.applyBrightness(action.actionValue)
            self.set()
            self.logCommandSent(u"brightness to {}%".format(action.actionValue))
        elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
            newBrightness = min(100, self.device.brightness + action.actionValue)
            self.applyBrightness(newBrightness)
            self.set()
            self.logCommandSent(u"brightness to {}%".format(newBrightness))
        elif action.deviceAction == indigo.kDeviceAction.DimBy:
            newBrightness = max(0, self.device.brightness - action.actionValue)
            self.applyBrightness(newBrightness)
            self.set()
            self.logCommandSent(u"brightness to {}%".format(newBrightness))
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            # Override the toggle since dimmer's need their brightness set.
            if self.isOn():
                off()
            elif self.isOff():
                on()
        else:
            Shelly_1PM.handleAction(self, action)

    def applyBrightness(self, brightness):
        """
        Updates the device states with the appropriate values based on the brightness value.

        :param brightness: The brightness value to set.
        :return: None
        """

        if brightness > 0:
            # if self.device.states['brightnessLevel'] != brightness:
            #     if self.isOn():
            #         self.logger.info(u"\"{}\" set to {}%".format(self.device.name, brightness))
            #     else:
            #         self.logger.info(u"\"{}\" on to {}%".format(self.device.name, brightness))
            self.turnOn()
        else:
            self.turnOff()

        self.device.updateStateOnServer("brightnessLevel", brightness)

    def set(self):
        """
        Sets and sends the brightness value and on/off data.

        :return: None
        """

        brightness = self.device.states.get('brightnessLevel', 0)
        turn = "on" if self.isOn() else "off"
        payload = {
            "turn": turn,
            "brightness": brightness
        }
        self.publish("{}/light/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))

    def turnOn(self):
        """
        Turns on the device.

        :return: None
        """

        self.device.updateStateOnServer(key='onOffState', value=True)
        self.updateStateImage()

    def updateStateImage(self):
        """
        Sets the state image based on the device states.

        :return: None
        """

        if self.isOn():
            self.device.updateStateImageOnServer(indigo.kStateImageSel.DimmerOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.DimmerOff)

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