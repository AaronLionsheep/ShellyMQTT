import indigo
from Shelly_1 import Shelly_1


class Shelly_EM_Relay(Shelly_1):
    """
    The Shelly 1 is a simple on/off relay.
    """

    def __init__(self, device):
        Shelly_1.__init__(self, device)

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
                "{}/relay/{}".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            # The relay will report overpower as well as on and off
            # Pass the on/off messages to the Shelly 1 implementation.
            overpower = (payload == 'overpower')
            # Set overpower in any case since on/off should clear the overpower state
            self.device.updateStateOnServer('overpower', (payload == 'overpower'))
            if not overpower:
                Shelly_1.handleMessage(self, topic, payload)
        else:
            Shelly_1.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly_1.handleAction(self, action)
