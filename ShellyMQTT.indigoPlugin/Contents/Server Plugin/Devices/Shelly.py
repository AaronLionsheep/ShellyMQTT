# coding=utf-8
import indigo
import logging


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
        return None

    def handleAction(self, action):
        return None

    def publish(self, topic, payload):
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
        address = self.device.pluginProps.get('address', None)
        if not address or address == '':
            return None

        address.strip()
        if address.endswith('/'):
            address = address[:-1]
        return address

    def getMQTT(self):
        mqtt = indigo.server.getPlugin("com.flyingdiver.indigoplugin.mqtt")
        if not mqtt.isEnabled():
            self.logger.error(u"MQTT plugin must be enabled!")
            return None
        else:
            return mqtt

    def getBrokerId(self):
        brokerId = self.device.pluginProps.get('broker-id', None)
        if brokerId is None or brokerId == '':
            return None
        else:
            return int(brokerId)

    def getMessageType(self):
        return self.device.pluginProps.get('message-type', "")

    def sendStatusRequestCommand(self):
        """
        Tells the shelly device to send out it's status
        :return: None
        """
        if self.getAddress() is not None:
            self.publish("{}/command".format(self.getAddress()), "update")

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
