# coding=utf-8
import indigo
import logging
import json


class Shelly:
    def __init__(self, device):
        self.device = device
        self.logger = logging.getLogger("Plugin.ShellyMQTT")

    def getSubscriptions(self):
        return []

    def subscribe(self):
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

    def unsubscribe(self):
        return None

    def handleMessage(self, topic, payload):
        if topic == "shellies/announce":
            self.parseAnnouncement(payload)
        elif topic == "{}/online".format(self.getAddress()):
            self.device.updateStateOnServer(key='online', value=(payload == "true"))
        return None

    def handleAction(self, action):
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
            self.logger.info(u"\"%s\" published \"%s\" to \"%s\"", self.device.name, payload, topic)

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
        payload = json.loads(payload)
        id = payload.get('id', None)
        mac_address = payload.get('mac', None)
        ip_address = payload.get('ip', None)
        firmware_version = payload.get('fw_ver', None)
        has_firmware_update = payload.get('new_fw', False)

        # id should appear in part of the device address
        if id and self.getAddress() and id in self.getAddress():
            self.logger.info(u"\"%s\" refreshed meta-data from announcement message", self.device.name)
            # self.device.updateStateOnServer('mac-address', mac_address)
            # self.device.updateStateOnServer('ip-address', ip_address)
            # self.device.updateStateOnServer('firmware-version', firmware_version)
            self.device.updateStateOnServer('has-firmware-update', has_firmware_update)