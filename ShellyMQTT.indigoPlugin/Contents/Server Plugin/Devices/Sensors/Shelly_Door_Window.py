# coding=utf-8
import indigo
from ..Shelly import Shelly


class Shelly_Door_Window(Shelly):
    """
    The Shelly Door/Window is small battery-operated contact sensor that reports lux values.
    """

    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        """
        Default method to return a list of topics that the device subscribes to.

        :return: A list of topics.
        """

        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "shellies/announce",
                "{}/online".format(address),
                "{}/sensor/state".format(address),
                "{}/sensor/lux".format(address),
                "{}/sensor/tilt".format(address),
                "{}/sensor/vibration".format(address),
                "{}/sensor/battery".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/sensor/state".format(self.getAddress()):
            if self.device.states['status'] != payload:
                self.logger.info("\"{}\" {}".format(self.device.name, payload))
            self.device.updateStateOnServer(key='status', value=payload)

            if self.device.pluginProps['useCase'] == "door":
                if payload == "closed":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.DoorSensorClosed)
                elif payload == "opened":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.DoorSensorOpened)
            elif self.device.pluginProps['useCase'] == "window":
                if payload == "closed":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.WindowSensorClosed)
                elif payload == "opened":
                    self.device.updateStateImageOnServer(indigo.kStateImageSel.WindowSensorOpened)
        elif topic == "{}/sensor/lux".format(self.getAddress()):
            self.device.updateStateOnServer(key="lux", value=payload)
        elif topic == "{}/sensor/tilt".format(self.getAddress()):
            self.device.updateStateOnServer(key="tilt", value=payload, uiValue="{}°".format(payload))
        elif topic == "{}/sensor/vibration".format(self.getAddress()):
            self.device.updateStateOnServer(key="vibration", value=(payload == "1"))
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
