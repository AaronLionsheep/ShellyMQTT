import indigo
from ..Shelly import Shelly


class Shelly_1(Shelly):
    """
    The Shelly 1 is a simple on/off relay.
    """

    def __init__(self, device):
        Shelly.__init__(self, device)

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
                "{}/relay/{}".format(address, self.getChannel()),
                "{}/input/{}".format(address, self.getChannel()),
                "{}/longpush/{}".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            if payload == "on":
                self.turnOn()
            elif payload == "off":
                self.turnOff()
        elif topic == "{}/input/{}".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer(key="sw-input", value=(payload == '1'))
        elif topic == "{}/longpush/{}".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer(key="longpush", value=(payload == '1'))
        else:
            Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            self.turnOn()
            self.publish("{}/relay/{}/command".format(self.getAddress(), self.getChannel()), "on")
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            self.turnOff()
            self.publish("{}/relay/{}/command".format(self.getAddress(), self.getChannel()), "off")
        elif action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.sendStatusRequestCommand()
