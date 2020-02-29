import indigo
from Devices.Shelly_1 import Shelly_1
from Devices.Shelly_1PM import Shelly_1PM
from Devices.Shelly_2_5_Relay import Shelly_2_5_Relay
from Devices.Shelly_HT import Shelly_HT
from Devices.Shelly_Flood import Shelly_Flood
from Queue import Queue

kCurDevVersion = 1  # current version of plugin devices


def createDeviceObject(device):
    deviceType = device.deviceTypeId
    if deviceType == "shelly-1":
        return Shelly_1(device)
    if deviceType == "shelly-1pm":
        return Shelly_1PM(device)
    if deviceType == "shelly-2-5-relay":
        return Shelly_2_5_Relay(device)
    if deviceType == "shelly-2-5-roller":
        return None
    if deviceType == "shelly-ht":
        return Shelly_HT(device)
    if deviceType == "shelly-flood":
        return Shelly_Flood(device)


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = pluginPrefs.get("debugMode", False)
        self.shellyDevices = {}
        self.deviceSubscriptions = {}
        self.messageQueue = Queue()
        self.mqttPlugin = indigo.server.getPlugin("com.flyingdiver.indigoplugin.mqtt")

    def startup(self):
        self.logger.info(u"Starting ShellyMQTT...")
        indigo.server.subscribeToBroadcast(u"com.flyingdiver.indigoplugin.mqtt", u"com.flyingdiver.indigoplugin.mqtt-message_queued", "message_handler")

    def shutdown(self):
        self.logger.info(u"Stopped ShellyMQTT...")

    def message_handler(self, message):
        self.logger.debug(u"received MQTT message type {} from {}".format(message["message_type"], indigo.devices[int(message["brokerID"])].name))
        self.messageQueue.put(message)

    def runConcurrentThread(self):
        try:
            while True:
                if not self.mqttPlugin.isEnabled():
                    self.logger.error(u"MQTT Connector plugin not enabled, aborting.")
                    self.sleep(60)
                else:
                    self.processMessages()
                    self.sleep(0.1)

        except self.StopThread:
            pass

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if userCancelled is False:
            self.debug = valuesDict.get('debugMode', False)

        if self.debug is True:
            self.logger.info(u"Debugging on")
        else:
            self.logger.info(u"Debugging off")

    def deviceStartComm(self, device):
        self.logger.info(u"Starting %s...", device.name)

        instanceVers = int(device.pluginProps.get('devVersCount', 0))
        if instanceVers < kCurDevVersion or kCurDevVersion == 0:
            newProps = device.pluginProps
            newProps["devVersCount"] = kCurDevVersion
            device.replacePluginPropsOnServer(newProps)
            device.stateListOrDisplayStateIdChanged()
            self.logger.debug(u"%s: Updated to version %s", device.name, kCurDevVersion)
        elif instanceVers >= kCurDevVersion:
            self.logger.debug(u"{}: Device Version is up to date".format(device.name))
        else:
            self.logger.error(u"%s: Unknown device version: %s", device.name, instanceVers)

        # Add the device id to our internal list of devices
        shelly = createDeviceObject(device)
        shelly.subscribe()
        self.addDeviceSubscriptions(shelly)
        self.shellyDevices[device.id] = shelly

    def deviceStopComm(self, device):
        self.logger.info(u"Stopping %s...", device.name)
        # unsubscribe the device topics from the broker
        if not self.shellyDevices.has_key(device.id):
            self.logger.debug(u"Unknown device...")
            return

        shelly = self.shellyDevices[device.id]
        shelly.unsubscribe()
        self.removeDeviceSubscriptions(shelly)
        del self.shellyDevices[device.id]

    def processMessages(self):
        """
        Processes messages in the queue until the queue is empty. This is used to pass
        messages that have come from MQTT into the appropriate devices.
        :return: None
        """
        while not self.messageQueue.empty():
            message = self.messageQueue.get()
            if not message:
                return

            # Now we have our message
            # Find the devices that need to get this message and give it to them
            props = {'message_type': message["message_type"]}
            brokerID = int(message['brokerID'])
            while True:
                data = self.mqttPlugin.executeAction("fetchQueuedMessage", deviceId=brokerID, props=props, waitUntilDone=True)
                if data == None:
                    break
                self.logger.debug(u"Got message: %s", data)
                topic = '/'.join(data['topic_parts'])
                devices = self.deviceSubscriptions.get(topic, list())
                for device in devices:
                    shelly = self.shellyDevices.get(device, None)
                    if shelly is not None:
                        shelly.handleMessage(topic, data['payload'])

    def actionControlDevice(self, action, device):
        """
        Handles an action being performed on the device.
        :param action: The action that occurred.
        :param device: The device that was acted on.
        :return: None
        """
        shelly = self.shellyDevices.get(device.id, None)
        if shelly is not None:
            shelly.handleAction(action.deviceAction)

    def actionControlUniversal(self, action, device):
        """
        Handles an action being performed on the device.
        :param action: The action that occurred.
        :param device: The device that was acted on.
        :return: None
        """
        shelly = self.shellyDevices.get(device.id, None)
        if shelly is not None:
            shelly.handleAction(action.deviceAction)

    def getBrokerDevices(self, filter="", valuesDict=None, typeId="", targetId=0):
        """
        Gets a list of available broker devices.
        :param filter:
        :param valuesDict:
        :param typeId:
        :param targetId:
        :return: A list of brokers.
        """
        brokers = []
        for dev in indigo.devices.iter():
            if dev.protocol == indigo.kProtocol.Plugin and \
                    dev.pluginId == "com.flyingdiver.indigoplugin.mqtt" and \
                    dev.deviceTypeId != 'aggregator':
                brokers.append((dev.id, dev.name))

        brokers.sort(key=lambda tup: tup[1])
        return brokers

    def addDeviceSubscriptions(self, shelly):
        """
        Adds a Shelly device to the dictionary of device subscriptions.
        :param shelly: The Shelly device to add.
        :return: None
        """
        subscriptions = shelly.getSubscriptions()
        for subscription in subscriptions:
            # See if there is a list of devices already listening to this subscription
            if not self.deviceSubscriptions.has_key(subscription):
                # initialize a new list of devices for this subscription
                self.deviceSubscriptions[subscription] = []
            self.deviceSubscriptions[subscription].append(shelly.device.id)

    def removeDeviceSubscriptions(self, shelly):
        """
        Removes a Shelly device from the dictionary of device subscriptions.
        :param shelly: The Shelly object to remove.
        :return: None
        """
        subscriptions = shelly.getSubscriptions()
        for subscription in subscriptions:
            if self.deviceSubscriptions.has_key(subscription) and shelly.device.id in self.deviceSubscriptions[subscription]:
                self.deviceSubscriptions[subscription].remove(shelly.device.id)
