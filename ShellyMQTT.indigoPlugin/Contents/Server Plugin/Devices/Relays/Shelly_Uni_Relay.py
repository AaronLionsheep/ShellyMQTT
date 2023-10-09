import indigo
import json
from .Shelly_1 import Shelly_1


class Shelly_Uni_Relay(Shelly_1):
    """

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
                "{}/info".format(address),
                "{}/relay/{}".format(address, self.getChannel()),
                "{}/ext_temperatures".format(address),
                "{}/ext_humidities".format(address)
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
        elif topic == "{}/info".format(self.getAddress()):
            try:
                payload = json.loads(payload)
                adcs = payload.get('adcs', [])
                if len(adcs) > 0 and type(adcs[0]) is dict:
                    voltage = adcs[0].get('voltage', None)
                    self.device.updateStateOnServer(key="voltage", value=voltage)
            except ValueError:
                self.logger.error(u"Problem parsing JSON: {}".format(payload))
        else:
            Shelly_1.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly_1.handleAction(self, action)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        return Shelly_1.validateConfigUI(valuesDict, typeId, devId)
