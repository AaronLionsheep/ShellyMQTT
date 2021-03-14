# coding=utf-8
import indigo
import json
from Shelly_i3 import Shelly_i3


class Shelly_Uni_Input(Shelly_i3):
    """

    """

    def __init__(self, device):
        Shelly_i3.__init__(self, device)

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
                "{}/input/{}".format(address, self.getChannel()),
                "{}/input_event/{}".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: The payload of the message.
        :return: None
        """

        if topic == "{}/info".format(self.getAddress()):
            try:
                payload = json.loads(payload)
                adcs = payload.get('adcs', [])
                if len(adcs) > 0 and type(adcs[0]) is dict:
                    voltage = adcs[0].get('voltage', None)
                    self.device.updateStateOnServer(key="voltage", value=voltage)
            except ValueError:
                self.logger.error(u"Problem parsing JSON: {}".format(payload))
        else:
            Shelly_i3.handleMessage(self, topic, payload)

        # Update the display state after data changed
        self.updateStateImage()

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.sendStatusRequestCommand()

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return: None
        """

        if self.device.states.get('onOffState', True):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        return Shelly_i3.validateConfigUI(valuesDict, typeId, devId)
