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
            self.logger.info(u"published '%s' to '%s'", payload, topic)

    def getAddress(self):
        address = self.device.pluginProps.get('address', None)
        if not address:
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
        id = self.device.pluginProps.get('brokerID', None)
        if id is None:
            return None
        else:
            return int(id)