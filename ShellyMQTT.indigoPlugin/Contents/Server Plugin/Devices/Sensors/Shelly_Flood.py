# coding=utf-8
import indigo
from ..Shelly import Shelly


class Shelly_Flood(Shelly):
    """
    The Shelly Flood is a small flood detector that also reports temperature.
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
                "{}/sensor/temperature".format(address),
                "{}/sensor/flood".format(address),
                "{}/sensor/battery".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: The payload of the message.
        :return: None
        """

        if topic == "{}/sensor/temperature".format(self.getAddress()):
            self.setTemperature(float(payload))
        elif topic == "{}/sensor/flood".format(self.getAddress()):
            if payload == 'true':
                self.device.updateStateOnServer(key='onOffState', value=True, uiValue='wet')
            elif payload == 'false':
                self.device.updateStateOnServer(key='onOffState', value=False, uiValue='dry')

            self.updateStateImage()
        elif topic == "{}/sensor/battery".format(self.getAddress()):
            self.device.updateStateOnServer(key="batteryLevel", value=payload, uiValue='{}%'.format(payload))
        else:
            Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly.handleAction(self, action)

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return: None
        """

        if self.device.states['onOffState']:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
