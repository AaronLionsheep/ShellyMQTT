# coding=utf-8
import indigo
from .Shelly_1 import Shelly_1


class Shelly_1PM(Shelly_1):
    """
    The Shelly 1PM is a Shelly 1 with power, energy, and temperature reporting.
    """

    def __init__(self, device):
        Shelly_1.__init__(self, device)

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
                "{}/relay/{}".format(address, self.getChannel()),
                "{}/input/{}".format(address, self.getChannel()),
                "{}/longpush/{}".format(address, self.getChannel()),
                "{}/relay/{}/power".format(address, self.getChannel()),
                "{}/relay/{}/overpower_value".format(address, self.getChannel()),
                "{}/relay/{}/energy".format(address, self.getChannel()),
                "{}/temperature".format(address),
                "{}/overtemperature".format(address),
                "{}/input_event/{}".format(address, self.getChannel()),
                "{}/ext_temperatures".format(address),
                "{}/ext_humidities".format(address),
                "{}/temperature_status".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: The payload of the message.
        :return: None
        """

        if topic == "{}/relay/{}/power".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('curEnergyLevel', payload, uiValue='{} W'.format(payload))
        elif topic == "{}/relay/{}/overpower_value".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer('overpower-value', payload, uiValue='{} W'.format(payload))
            # Fire all triggers watching for an overpower event
            for trigger in indigo.activePlugin.triggers.values():
                if trigger.pluginTypeId == "overpower-any":
                    indigo.trigger.execute(trigger)
                elif trigger.pluginTypeId == "overpower-device" and int(trigger.pluginProps['device-id']) == self.device.id:
                    indigo.trigger.execute(trigger)
        elif topic == "{}/relay/{}/energy".format(self.getAddress(), self.getChannel()):
            try:
                self.updateEnergy(int(payload))
            except ValueError:
                self.logger.error(u"Unable to convert value of \"{}\" into an int!".format(payload))
        elif topic == "{}/temperature".format(self.getAddress()):
            try:
                self.setTemperature(float(payload), state='internal-temperature', unitsProps='int-temp-units')
            except ValueError:
                self.logger.error(u"Unable to convert value of \"{}\" into a float!".format(payload))
        elif topic == "{}/overtemperature".format(self.getAddress()):
            self.device.updateStateOnServer('overtemperature', (payload == '1'))
        elif topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            # The 1PM will report overpower as well as on and off
            # Pass the on/off messages to the Shelly 1 implementation.
            overpower = (payload == 'overpower')
            # Set overpower in any case since on/off should clear the overpower state
            self.device.updateStateOnServer('overpower', (payload == 'overpower'))
            if overpower:
                indigo.device.turnOff(self.device.id)
                self.logCommandReceived("off (overpower)")
            else:
                Shelly_1.handleMessage(self, topic, payload)
        else:
            Shelly_1.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kUniversalAction.EnergyReset:
            self.resetEnergy()
        elif action.deviceAction == indigo.kUniversalAction.EnergyUpdate:
            # This will be handled by making a status request
            self.sendStatusRequestCommand()
        else:
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
