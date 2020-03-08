# coding=utf-8
import indigo
import logging
import json


class Shelly:
    """
    The base class for all Shelly devices.
    """

    def __init__(self, device):
        self.device = device
        self.logger = logging.getLogger("Plugin.ShellyMQTT")

    def getSubscriptions(self):
        """
        Default method to return a list of topics that the device subscribes to.

        :return: A list.
        """

        return []

    def subscribe(self):
        """
        Subscribes the device to all required topics on the specified broker.

        :return: None
        """

        mqtt = self.getMQTT()
        if mqtt is not None:
            for subscription in self.getSubscriptions():
                # Band-aid for bug in MQTT-Connector (Issue #10 on MQTT-Connector GitHub)
                if indigo.activePlugin.pluginPrefs.get('connector-fix', False):
                    subscription = "0:%s" % subscription

                props = {
                    'topic': subscription,
                    'qos': 0
                }
                mqtt.executeAction("add_subscription", deviceId=self.getBrokerId(), props=props)

    def handleMessage(self, topic, payload):
        """
        The default handler for incoming messages.
        These are messages that are handled by ANY Shelly device.

        :param topic: The topic of the incoming message.
        :param payload: THe content of the massage.
        :return:  None
        """

        if topic == "shellies/announce":
            self.parseAnnouncement(payload)
        elif topic == "{}/online".format(self.getAddress()):
            self.device.updateStateOnServer(key='online', value=(payload == "true"))
        return None

    def handleAction(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        return None

    def publish(self, topic, payload):
        """
        Publishes a message on a given topic to the device's broker.

        :param topic: The topic to send data to.
        :param payload: The data to send over the topic.
        :return: None
        """

        mqtt = self.getMQTT()
        if mqtt is not None:
            props = {
                'topic': topic,
                'payload': payload,
                'qos': 0,
                'retain': 0,
            }
            mqtt.executeAction("publish", deviceId=self.getBrokerId(), props=props, waitUntilDone=False)
            self.logger.debug(u"\"%s\" published \"%s\" to \"%s\"", self.device.name, payload, topic)

    def getAddress(self):
        """
        Helper function to get the base address of this device. Trailing '/' will be removed.

        :return: The cleaned base address.
        """

        address = self.device.pluginProps.get('address', None)
        if not address or address == '':
            return None

        address.strip()
        if address.endswith('/'):
            address = address[:-1]
        return address

    def getMQTT(self):
        """
        Helper function to get the MQTT plugin instance.

        :return: The MQTT Connector plugin if it is running, otherwise None.
        """

        mqtt = indigo.server.getPlugin("com.flyingdiver.indigoplugin.mqtt")
        if not mqtt.isEnabled():
            self.logger.error(u"MQTT plugin must be enabled!")
            return None
        else:
            return mqtt

    def getBrokerId(self):
        """
        Gets the Indigo deviceId of the broker that this device connects to.

        :return: The Indigo deviceId of the broker for this device.
        """

        brokerId = self.device.pluginProps.get('broker-id', None)
        if brokerId is None or brokerId == '':
            return None
        else:
            return int(brokerId)

    def getMessageType(self):
        """
        Helper method to get the message type that this device will process.

        :return: The message type for this device.
        """

        return self.device.pluginProps.get('message-type', "")

    def getAnnounceMessageType(self):
        """
        Helper method to get the message type for announcement messages.

        :return: The message type for announce messages, or None if this is the same as the regular message type.
        """

        if not self.device.pluginProps.get('announce-message-type-same-as-message-type', True):
            return self.device.pluginProps.get('announce-message-type', "")
        else:
            return None

    def getMessageTypes(self):
        """
        Helper method to return all message types this device accepts.

        :return: A list of messages types for this device.
        """

        messageTypes = []
        if self.getMessageType() != "":
            messageTypes.append(self.getMessageType())
        if self.getAnnounceMessageType():
            messageTypes.append(self.getAnnounceMessageType())
        return messageTypes

    def sendStatusRequestCommand(self):
        """
        Tells the shelly device to send out it's status.

        :return: None
        """

        if self.getAddress() is not None:
            self.publish("{}/command".format(self.getAddress()), "update")

    def announce(self):
        """
        Sends the command to tell this device to announce itself.

        :return: None
        """

        self.publish("{}/command".format(self.getAddress()), "announce")

    def sendUpdateFirmwareCommand(self):
        """
        Sends the command to attempt a firmware update if one exists.

        :return: None
        """

        if self.getAddress() is not None:
            if not self.device.states.get('has-firmware-update', False):
                self.logger.warning(u"\"%s\" has not notified that it has a newer firmware. Attempting to update anyway...", self.device.name)
            self.publish("{}/command".format(self.getAddress()), "update_fw")

    def setTemperature(self, temperature, state="temperature", unitsProps="temp-units"):
        """
        Helper function to set the temperature of a device.

        :param temperature: The temperature to set.
        :param state: The state key to update.
        :param unitsProps: The props containing the units to use or to convert to.
        :return: None
        """

        units = self.device.pluginProps.get(unitsProps, None)
        if units == "F":
            self.device.updateStateOnServer(state, temperature, uiValue='{} °F'.format(temperature))
        elif units == "C->F":
            temperature = self.convertCtoF(temperature)
            self.device.updateStateOnServer(state, temperature, uiValue='{} °F'.format(temperature))
        elif units == "C":
            self.device.updateStateOnServer(state, temperature, uiValue='{} °C'.format(temperature))
        elif units == "F->C":
            temperature = self.convertFtoC(temperature)
            self.device.updateStateOnServer(state, temperature, uiValue='{} °C'.format(temperature))

    def convertCtoF(self, celsius):
        """
        Handles a conversion from Celsius to Fahrenheit.

        :param celsius: The temperature in celsius.
        :return: The temperature in Fahrenheit.
        """

        return (celsius * 9 / 5) + 32

    def convertFtoC(self, fahrenheit):
        """
        Handles a conversion from Fahrenheit to Celsius.

        :param fahrenheit: The temperature in fahrenheit.
        :return: The temperature in Celsius.
        """

        return (fahrenheit - 32) * 5 / 9

    def parseAnnouncement(self, payload):
        """
        Parses the data from an announce message. The payload is expected to be of the form:
        {
            "id": <SOME_ID>,
            "mac": <MAC_ADDRESS>,
            "ip": <IP_ADDRESS>,
            "fw_ver": <FIRMWARE_VERSION>,
            "new_fw": <true/false>
        }

        :param payload: The payload of the announce message.
        :return: None
        """

        payload = json.loads(payload)
        identifier = payload.get('id', None)
        mac_address = payload.get('mac', None)
        ip_address = payload.get('ip', None)
        firmware_version = payload.get('fw_ver', None)
        has_firmware_update = payload.get('new_fw', False)

        # id should appear in part of the device address
        if identifier and self.getAddress() and identifier in self.getAddress():
            self.logger.info(u"\"%s\" refreshed meta-data from announcement message", self.device.name)
            self.device.updateStateOnServer('mac-address', mac_address)
            self.device.updateStateOnServer('ip-address', ip_address)
            self.device.updateStateOnServer('firmware-version', firmware_version)
            self.device.updateStateOnServer('has-firmware-update', has_firmware_update)

    def updateEnergy(self, energy):
        """
        pluginProps['resetEnergyOffset'] stores the energy reported the last time a reset was requested
        If this value is greater than the current energy being reported, then the device must have been powered off
        and reset back to 0.

        :param energy: The energy utilization counter.
        :return: None
        """

        resetEnergyOffset = int(self.device.pluginProps.get('resetEnergyOffset', 0))
        new_energy = energy - resetEnergyOffset
        if new_energy < 0:  # If the offset is greater than what is being reported, the device must have reset
            # our last known energy total can be used to determine the previous energy usage
            self.logger.info(u"%s: Must have lost power and the energy usage has reset to 0. Determining previous usage based on last know energy usage value...")
            resetEnergyOffset = self.device.states.get('accumEnergyTotal', 0) * 60 * 1000 * -1
            newProps = self.device.pluginProps
            newProps['resetEnergyOffset'] = resetEnergyOffset
            self.device.replacePluginPropsOnServer(newProps)
            new_energy = energy - resetEnergyOffset

        kwh = float(new_energy) / 60 / 1000  # energy is reported in watt-minutes
        if kwh < 0.01:
            uiValue = '{:.4f} kWh'.format(kwh)
        elif kwh < 1:
            uiValue = '{:.3f} kWh'.format(kwh)
        elif kwh < 10:
            uiValue = '{:.2f} kWh'.format(kwh)
        else:
            uiValue = '{:.1f} kWh'.format(kwh)

        self.device.updateStateOnServer('accumEnergyTotal', kwh, uiValue=uiValue)

    def resetEnergy(self):
        """
        We can't tell the device to reset it's internal energy usage
        Record the current value being reported so we can offset from it later on

        :return: None
        """

        currEnergyWattMins = self.device.states.get('accumEnergyTotal', 0) * 60 * 1000
        previousResetEnergyOffset = int(self.device.pluginProps.get('resetEnergyOffset', 0))
        offset = currEnergyWattMins + previousResetEnergyOffset
        newProps = self.device.pluginProps
        newProps['resetEnergyOffset'] = offset
        self.device.replacePluginPropsOnServer(newProps)
        self.device.updateStateOnServer('accumEnergyTotal', 0.0)

    def turnOn(self):
        """
        Turns on the device.

        :return: None
        """

        if not self.isOn():
            self.logger.info(u"\"{}\" on".format(self.device.name))
        self.device.updateStateOnServer(key='onOffState', value=True)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.PowerOn)

    def turnOff(self):
        """
        Turns off the device.

        :return: None
        """

        if not self.isOff():
            self.logger.info(u"\"{}\" off".format(self.device.name))
        self.device.updateStateOnServer(key='onOffState', value=False)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.PowerOff)

    def isOn(self):
        """
        Helper to determine if a device is on.

        :return: True if the device is on.
        """

        return self.device.states.get('onOffState', False)

    def isOff(self):
        """
        Helper to determine if a device is off.

        :return: True if the device is off.
        """

        return not self.device.states.get('onOffState', False)

    def getChannel(self):
        """
        Getter for the device channel.

        :return: The channel of the device. If no channel is found, then 0.
        """

        return self.device.pluginProps.get('channel', 0)
