# coding=utf-8
import indigo
from ..Shelly import Shelly


class Shelly_EM_Meter(Shelly):
    """
    The Shelly 2.5 is a relay device that is pretty much two Shely 1PM's in the same enclosure.
    The each channel is represented by a single Indigo device, so they share internal temperature
    and the online status.
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
                "{}/emeter/{}/energy".format(address, self.getChannel()),
                "{}/emeter/{}/returned_energy".format(address, self.getChannel()),
                "{}/emeter/{}/power".format(address, self.getChannel()),
                "{}/emeter/{}/reactive_power".format(address, self.getChannel()),
                "{}/emeter/{}/voltage".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/emeter/{}/energy".format(self.getAddress(), self.getChannel()):
            try:
                energy = int(payload)
                self.updateEnergy(energy, offsetProp='resetEnergyConsumedOffset', energyState='energy-consumed')
            except ValueError:
                self.logger.error(u"Unable to convert energy-consumed of \"{}\" to an int!".format(payload))
        elif topic == "{}/emeter/{}/returned_energy".format(self.getAddress(), self.getChannel()):
            try:
                energy = int(payload)
                self.updateEnergy(energy, offsetProp='resetEnergyReturnedOffset', energyState='energy-returned')
            except ValueError:
                self.logger.error(u"Unable to convert energy-returned of \"{}\" to an int!".format(payload))
        elif topic == "{}/emeter/{}/power".format(self.getAddress(), self.getChannel()):
            try:
                power = float(payload)
                self.device.updateStateOnServer('power', power, uiValue="{:.2f} W".format(power), decimalPlaces=2)
                self.device.updateStateOnServer('curEnergyLevel', power, uiValue='{:.2f} W'.format(power), decimalPlaces=2)
            except ValueError:
                self.logger.error(u"Unable to convert power of \"{}\" to a float!".format(payload))
        elif topic == "{}/emeter/{}/reactive_power".format(self.getAddress(), self.getChannel()):
            try:
                reactivePower = float(payload)
                self.device.updateStateOnServer('power-reactive', reactivePower, uiValue="{:.2f} W".format(reactivePower), decimalPlaces=2)
            except ValueError:
                self.logger.error(u"Unable to convert reactive-power of \"{}\" to a float!".format(payload))
        elif topic == "{}/emeter/{}/voltage".format(self.getAddress(), self.getChannel()):
            try:
                voltage = float(payload)
                self.device.updateStateOnServer('voltage', voltage, uiValue="{:.1f} V".format(voltage), decimalPlaces=1)
            except ValueError:
                self.logger.error(u"Unable to convert voltage of \"{}\" to a float!".format(payload))
        else:
            Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        if action.deviceAction == indigo.kUniversalAction.EnergyReset:
            # Reset energy consumed and returned
            self.resetEnergy()

            # "Reset" the ui value
            self.device.updateStateOnServer('accumEnergyTotal', 0.0)
        elif action.deviceAction == indigo.kUniversalAction.EnergyUpdate:
            # This will be handled by making a status request
            self.sendStatusRequestCommand()
        else:
            Shelly.handleAction(self, action)

    def updateEnergy(self, energy, offsetProp='resetEnergyOffset', energyState='accumEnergyTotal'):
        """
        Overrides the energy update method to update the energy UI after each energy update.

        :param energy: The energy value to update.
        :param offsetProp: The offset of energy.
        :param energyState: The state to update.
        :return: None
        """

        # Update the targeted energy value
        Shelly.updateEnergy(self, energy, offsetProp, energyState)

        # Calculate the value to display.
        displayMethod = self.device.pluginProps.get('energy-display', None)
        if displayMethod == "net":
            consumed = self.device.states.get('energy-consumed', 0)
            returned = self.device.states.get('energy-returned', 0)
            net = consumed - returned

            self.device.updateStateOnServer('accumEnergyTotal', net, uiValue=self.buildEnergyUIValue(net))
        elif displayMethod == "consumed":
            consumed = self.device.states.get('energy-consumed', 0)

            self.device.updateStateOnServer('accumEnergyTotal', consumed, uiValue=self.buildEnergyUIValue(consumed))
        elif displayMethod == "returned":
            returned = -1 * self.device.states.get('energy-returned', 0)

            self.device.updateStateOnServer('accumEnergyTotal', returned, uiValue=self.buildEnergyUIValue(returned))

    def resetEnergy(self):
        """
        We can't tell the device to reset it's internal energy usage
        Record the current value being reported so we can offset from it later on

        :return: None
        """

        newProps = self.device.pluginProps

        currEnergyWattMins = self.device.states.get('energy-consumed', 0) * 60 * 1000
        previousResetEnergyOffset = int(self.device.pluginProps.get('resetEnergyConsumedOffset', 0))
        offset = currEnergyWattMins + previousResetEnergyOffset
        newProps['resetEnergyConsumedOffset'] = offset
        self.device.updateStateOnServer('energy-consumed', 0.0)

        currEnergyWattMins = self.device.states.get('energy-returned', 0) * 60 * 1000
        previousResetEnergyOffset = int(self.device.pluginProps.get('resetEnergyReturnedOffset', 0))
        offset = currEnergyWattMins + previousResetEnergyOffset
        newProps['resetEnergyReturnedOffset'] = offset
        self.device.updateStateOnServer('energy-returned', 0.0)

        self.device.replacePluginPropsOnServer(newProps)

    def buildEnergyUIValue(self, kwh):
        """
        Builds a string to be used for the ui value in the energy display.

        :param kwh: The energy in kwh.
        :return: A formatted string.
        """

        if kwh < 0.01:
            uiValue = '{:.4f} kWh'.format(kwh)
        elif kwh < 1:
            uiValue = '{:.3f} kWh'.format(kwh)
        elif kwh < 10:
            uiValue = '{:.2f} kWh'.format(kwh)
        else:
            uiValue = '{:.1f} kWh'.format(kwh)

        return uiValue

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return: None
        """

        if self.device.states['online']:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.EnergyMeterOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.EnergyMeterOff)
