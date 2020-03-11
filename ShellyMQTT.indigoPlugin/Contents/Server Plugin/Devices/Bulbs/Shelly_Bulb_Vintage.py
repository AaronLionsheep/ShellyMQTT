# coding=utf-8
import indigo
import json
from ..Shelly_Dimmer_SL import Shelly_Dimmer_SL


class Shelly_Bulb_Vintage(Shelly_Dimmer_SL):
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
            # the payload will be json in the form:
            # {
            #     "ison": false,        /* whether the bulb is on */
            #     "has_timer": false,   /* whether a timer is currently armed */
            #     "timer_remaining": 0, /* if there is an active timer, shows seconds until timer elapses; 0 otherwise */
            #     "brightness": 90      /* brightness, 0..100 */
            # }
            try:
                payload = json.loads(payload)
                if payload['ison']:
                    # we will accept a brightness value and save it
                    self.device.updateStateOnServer("brightnessLevel", payload['brightness'])
                else:
                    # The light should be off regardless of a reported brightness value
                    self.turnOff()
            except ValueError:
                self.logger.error(u"Problem parsing JSON: {}".format(payload))
        else:
            Shelly_Dimmer_SL.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly_Dimmer_SL.handleAction(self, action)

    def set(self):
        """
        Method that sets the data on the device. The Duo has a topic where you set all parameters.

        :return: None
        """

        brightness = self.device.states.get('brightnessLevel', 0)
        turn = "on" if brightness >= 1 else "off"

        # Ensure brightness is within the 8-bit range
        brightness = min(255, max(0, brightness))

        payload = {
            "turn": turn,
            "brightness": brightness
        }

        try:
            self.publish("{}/light/{}/set".format(self.getAddress(), self.getChannel()), json.dumps(payload))
        except ValueError:
            self.logger.error(u"Problem building JSON: {}".format(payload))
