# coding=utf-8
import indigo
import json
from ShellyLogger import ShellyLogger


class Shelly:
    """
    The base class for all Shelly devices.
    """

    def __init__(self, device):
        self.device = device
        self.logger = ShellyLogger(self)
        self.triggers = []
        self.temperature_sensors = []
        self.humidity_sensors = []

    def refresh_device(self):
        """
        Gets an indigo device from the device identifier.

        :return: The indigo device object.
        """

        if self.device:
            indigo.devices[self.device.id].refreshFromServer()
            self.device = indigo.devices[self.device.id]
            self.logger.debug(u"Refreshed device info for \"{}\"".format(self.device.name))

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
        :param payload: The content of the massage.
        :return:  None
        """

        if topic == "shellies/announce":
            self.parseAnnouncement(payload)
        elif topic == "{}/online".format(self.getAddress()):
            wasOnline = self.device.states.get('online', False)
            self.device.updateStateOnServer(key='online', value=(payload == "true"))
            self.updateStateImage()
            if not wasOnline:
                self.setLastInputEventId(0)
        elif topic == "{}/input_event/{}".format(self.getAddress(), self.getChannel()):
            self.processInputEvent(payload)
        elif topic == "{}/ext_temperatures".format(self.getAddress()):
            self.processTemperatureSensors(payload)
        elif topic == "{}/ext_humidities".format(self.getAddress()):
            self.processHumiditySensors(payload)
        elif topic == "{}/temperature_status".format(self.getAddress()):
            self.processTemperatureStatus(payload)
        return None

    def handleAction(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        return None

    def handlePluginAction(self, action):
        """
        The default handler for a plugin-defined action

        :param action: The plugin action
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

    def getIpAddress(self):
        """
        Helper function to get the ip address of the device.

        :return: The device ip address
        """

        return self.device.states.get('ip-address', None)

    def updateAvailable(self):
        """
        Helper function to determine if there is a firmware update.

        :return: True or false to indicate if there is a firmware update.
        """

        return self.device.states.get('has-firmware-update', False)

    def getFirmware(self):
        """
        Getter for the device firmware.

        :return: The current firmware of the device.
        """

        return self.device.states.get('firmware-version', None)

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
            self.logCommandSent("status request")

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
            self.logCommandSent("update firmware")

    def setTemperature(self, temperature, state="temperature", unitsProps="temp-units", decimalsProps="temp-decimals", offsetProps="temp-offset"):
        """
        Helper function to set the temperature of a device.

        :param temperature: The temperature to set.
        :param state: The state key to update.
        :param unitsProps: The props containing the units to use or to convert to.
        :param decimalsProps: The props containing the number of decimals to display.
        :param offsetProps: The props containing the offset to apply after conversions.
        :return: None
        """

        units = self.device.pluginProps.get(unitsProps, None)
        decimals = int(self.device.pluginProps.get(decimalsProps, 1))
        offset = 0
        try:
            offset = float(self.device.pluginProps.get(offsetProps, 0))
        except ValueError:
            self.logger.error(u"Unable to convert offset of \"{}\" into a float!".format(self.device.pluginProps.get(offsetProps, 0)))

        if units == "F":
            temperature += offset
            self.device.updateStateOnServer(state, temperature, uiValue='{:.{}f} °F'.format(temperature, decimals), decimalPlaces=decimals)
        elif units == "C->F":
            temperature = self.convertCtoF(temperature)
            temperature += offset
            self.device.updateStateOnServer(state, temperature, uiValue='{:.{}f} °F'.format(temperature, decimals), decimalPlaces=decimals)
        elif units == "C":
            temperature += offset
            self.device.updateStateOnServer(state, temperature, uiValue='{:.{}f} °C'.format(temperature, decimals), decimalPlaces=decimals)
        elif units == "F->C":
            temperature = self.convertFtoC(temperature)
            temperature += offset
            self.device.updateStateOnServer(state, temperature, uiValue='{:.{}f} °C'.format(temperature, decimals), decimalPlaces=decimals)

    def convertCtoF(self, celsius):
        """
        Handles a conversion from Celsius to Fahrenheit.

        :param celsius: The temperature in celsius.
        :return: The temperature in Fahrenheit.
        """

        return (celsius * 9 / 5.0) + 32

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
            self.logger.debug(u"Updated device details for \"{}\" via announcement message".format(self.device.name))
            self.device.updateStateOnServer('mac-address', mac_address)
            self.device.updateStateOnServer('ip-address', ip_address)

            if self.device.states.get('firmware-version', '') not in [firmware_version, None, '']:
                self.logger.debug(u"Detected a firmware change for \"{}\"".format(self.device.name))
            self.device.updateStateOnServer('firmware-version', firmware_version)
            self.device.updateStateOnServer('has-firmware-update', has_firmware_update)

    def processInputEvent(self, eventMessage):
        """
        Parses an input event message and fires triggers if this is a new input event.

        Events are formed as: {"event":"string","event_cnt":number}
        Where the event key holds the event type and event_cnt holds the event identifier.

        Expected events are:
        - S: Short
        - L: Long
        - SS: Short + Short
        - SSS: Short + Short + Short
        - SL: Short + Long
        - LS: Long + Short

        The event identifier will increment with each input event and will start off as 0.

        :param eventMessage: The event message
        :return:
        """

        # Parse the event message
        event = json.loads(eventMessage)
        eventType = event.get('event', None)
        eventId = event.get('event_cnt', None)
        if eventType is None or eventId is None:
            self.logger.error(u"Unable to parse event message: {}".format(eventMessage))
            return

        # Determine if this is a new event
        if eventId == self.getLastInputEventId():
            # We have already processed this event message, do to process it again
            return
        self.setLastInputEventId(eventId)

        # Process all triggers for this input event
        eventName = u"input-event-{}".format(eventType.lower())
        for trigger in indigo.activePlugin.triggers.values():
            if trigger.pluginTypeId == eventName and int(trigger.pluginProps.get('device-id', -1)) == self.device.id:
                indigo.trigger.execute(trigger)

    def processTemperatureSensors(self, payload):
        """
        Parses a message containing information about all connected temperature sensors.

        The payload is expected to be of the form:
        {
            "0":{"hwID":"XXXXXXXX","tC":20.5},
            "1":{"hwID":"YYYYYYYY","tC":21.5},
            "2":{"hwID":"ZZZZZZZZ","tC":22.5}
        }

        :param payload: A json-formatted string containing sensor information
        :return: None
        """

        try:
            sensors = json.loads(payload)
            self.temperature_sensors = []
            for channel, sensor in sensors.items():
                # Invalid if the sensor reads 999
                if sensor['tC'] != 999:
                    self.temperature_sensors.append({
                        "channel": int(channel),
                        "id": sensor['hwID']
                    })
        except ValueError:
            self.logger.error(u"Problem parsing JSON: {}".format(payload))

    def processHumiditySensors(self, payload):
        """
        Parses a message containing information about all connected humidity sensors.

        The payload is expected to be of the form:
        {
            "0":{"hwID":"XXXXXXXX","hum":50}
        }

        :param payload: A json-formatted string containing sensor information
        :return: None
        """

        try:
            sensors = json.loads(payload)
            self.humidity_sensors = []
            for channel, sensor in sensors.items():
                # Invalid if the sensor reads 999
                if sensor['hum'] != 999:
                    self.humidity_sensors.append({
                        "channel": int(channel),
                        "id": sensor['hwID']
                    })
        except ValueError:
            self.logger.error(u"Problem parsing JSON: {}".format(payload))

    def processTemperatureStatus(self, payload):
        """
        Parses a message containing the temperature status for a device.

        :param payload: The payload of the temperature status
        :return: None
        """

        previous_status = self.device.states.get('temperature-status', None)
        self.device.updateStateOnServer("temperature-status", payload)

        if payload != previous_status and payload != "Normal":
            # The temperature status has changed to an abnormal value
            for trigger in indigo.activePlugin.triggers.values():
                if trigger.pluginTypeId == "abnormal-temperature-status-any":
                    indigo.trigger.execute(trigger)

    def getLastInputEventId(self):
        """
        Getter for the last processed input event identifier.

        :return: an integer of the last input event identifier.
        """

        return int(self.device.pluginProps.get('last-input-event-id', -1))

    def setLastInputEventId(self, eventId):
        """
        Sets the internal last input event count for the device.

        :param eventId: The event id
        :return: None
        """

        props = self.device.pluginProps
        props["last-input-event-id"] = int(eventId)
        self.device.replacePluginPropsOnServer(props)

    def updateEnergy(self, energy, offsetProp='resetEnergyOffset', energyState='accumEnergyTotal'):
        """
        pluginProps['resetEnergyOffset'] stores the energy reported the last time a reset was requested
        If this value is greater than the current energy being reported, then the device must have been powered off
        and reset back to 0.

        :param energy: The energy utilization counter.
        :param offsetProp: The property key that contains the offset value.
        :param energyState: The state that stores energy usage.
        :return: None
        """

        resetEnergyOffset = int(self.device.pluginProps.get(offsetProp, 0))
        new_energy = energy - resetEnergyOffset
        if new_energy < 0:  # If the offset is greater than what is being reported, the device must have reset
            # our last known energy total can be used to determine the previous energy usage
            self.logger.debug(u"%s: Must have lost power and the energy usage has reset to 0. Determining previous usage based on last known energy usage value...")
            resetEnergyOffset = self.device.states.get(energyState, 0) * 60 * 1000 * -1
            newProps = self.device.pluginProps
            newProps[offsetProp] = resetEnergyOffset
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

        self.device.updateStateOnServer(energyState, kwh, uiValue=uiValue, decimalPlaces=4)

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
        self.device.updateStateOnServer('accumEnergyTotal', 0.0)
        self.device.replacePluginPropsOnServer(newProps)

    def turnOn(self):
        """
        Turns on the device.

        :return: None
        """

        # if not self.isOn():
        #     self.logger.info(u"\"{}\" on".format(self.device.name))
        self.device.updateStateOnServer(key='onOffState', value=True)
        self.updateStateImage()

    def turnOff(self):
        """
        Turns off the device.

        :return: None
        """

        # if not self.isOff():
        #     self.logger.info(u"\"{}\" off".format(self.device.name))
        self.device.updateStateOnServer(key='onOffState', value=False)
        self.updateStateImage()

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

    def isAddon(self):
        """
        Helper method to determine if a device is an addon device. This defaults to false since most devices
        are not add-ons.

        :return: True if the device is an addon.
        """

        return False

    def updateStateImage(self):
        """
        Sets the state image based on the current device states.

        :return: None
        """

        if self.isOn():
            self.device.updateStateImageOnServer(indigo.kStateImageSel.PowerOn)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.PowerOff)

    def isMuted(self):
        """
        Helper method to determine if the device wants logging to be muted.

        :return: True if the device wants logging muted.
        """

        return self.device.pluginProps.get("muted", False)

    def getMutedLoggingMethods(self):
        """
        Getter for the default logging methods that should be muted when the device is
        set to be muted.

        :return: A list of function names that should not be executed when the device is muted.
        """

        return ["debug", "info"]

    def updateBatteryLevel(self, batteryLevel):
        """
        Helper method to update the battery level. Low battery triggers are fired from this point if present.

        :param batteryLevel: The new battery level
        :return: None
        """

        # Get the old battery level to determine if there was a change
        oldBatteryLevel = self.device.states.get('batteryLevel', 0)
        # Save the current battery level
        self.device.updateStateOnServer(key="batteryLevel", value=batteryLevel, uiValue='{}%'.format(batteryLevel))

        try:
            if indigo.activePlugin.lowBatteryThreshold >= int(batteryLevel) and int(oldBatteryLevel) != int(batteryLevel):
                # Battery level has changed
                # Fire all triggers watching for a low battery event
                for trigger in indigo.activePlugin.triggers.values():
                    if trigger.pluginTypeId == "low-battery-any":
                        indigo.trigger.execute(trigger)
                    elif trigger.pluginTypeId == "low-battery-device" and int(trigger.pluginProps['device-id']) == self.device.id:
                        indigo.trigger.execute(trigger)
        except ValueError:
            pass

    def logCommandSent(self, message):
        """
        Helper method that logs when a device command is sent.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info(u"sent \"{}\" {}".format(self.device.name, message))

    def logCommandReceived(self, message):
        """
        Helper method that logs when a command is received.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info(u"received \"{}\" {}".format(self.device.name, message))

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        # Default implementation declares all config UI's to be valid
        return True, valuesDict, None

    @staticmethod
    def didCommPropertyChange(origDev, newDev):
        """
        Determines whether changes to a device should result in the communications
        needing to be restarted.

        :param origDev: The device before changes.
        :param newDev: The device after changes.
        :return: True or false to indicate whether communication has been changed.
        """

        if origDev.pluginProps.get('broker-id', None) != newDev.pluginProps.get('broker-id', None):
            return True

        if origDev.pluginProps.get('address', None) != newDev.pluginProps.get('address', None):
            return True

        if origDev.pluginProps.get('message-type', None) != newDev.pluginProps.get('message-type', None):
            return True

        if origDev.pluginProps.get('announce-message-type', None) != newDev.pluginProps.get('announce-message-type', None):
            return True

        if origDev.pluginProps.get('channel', None) != newDev.pluginProps.get('channel', None):
            return True

        # If we are here then the device is not restarting, so we should update the device to pull in any chanegs
        shelly = indigo.activePlugin.shellyDevices.get(newDev.id)
        if shelly:
            shelly.refresh_device()
        return False
