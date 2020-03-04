import indigo
from Devices.Shelly_1 import Shelly_1
from Devices.Shelly_1PM import Shelly_1PM
from Devices.Shelly_2_5_Relay import Shelly_2_5_Relay
from Devices.Shelly_HT import Shelly_HT
from Devices.Shelly_Flood import Shelly_Flood
from Devices.Shelly_Door_Window import Shelly_Door_Window
from Devices.Shelly_Dimmer_SL import Shelly_Dimmer_SL
from Queue import Queue

kCurDevVersion = 0  # current version of plugin devices


def createDeviceObject(device):
    deviceType = device.deviceTypeId
    if deviceType == "shelly-1":
        return Shelly_1(device)
    elif deviceType == "shelly-1pm":
        return Shelly_1PM(device)
    elif deviceType == "shelly-2-5-relay":
        return Shelly_2_5_Relay(device)
    #elif deviceType == "shelly-2-5-roller":
    #    return None
    elif deviceType == "shelly-ht":
        return Shelly_HT(device)
    elif deviceType == "shelly-flood":
        return Shelly_Flood(device)
    elif deviceType == "shelly-door-window":
        return Shelly_Door_Window(device)
    elif deviceType == "shelly-dimmer":
        return Shelly_Dimmer_SL(device)


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = pluginPrefs.get("debugMode", False)

        # {
        #   devId: <Indigo device id>,
        #   anotherDevId: <Shelly object>
        # }
        self.shellyDevices = {}

        # {
        #   <brokerId>: {
        #       'some/topic': [dev1, dev2, dev3],
        #       'another/topic': [dev1, dev4, dev5]
        #   }
        #   <anotherBroker>: {
        #       'some/topic': [dev6, dev7],
        #       'another/unique/topic': [dev7, dev8, dev9]
        #   }
        # }
        self.brokerDeviceSubscriptions = {}
        self.messageTypes = []
        self.messageQueue = Queue()
        self.mqttPlugin = indigo.server.getPlugin("com.flyingdiver.indigoplugin.mqtt")

    def startup(self):
        indigo.server.subscribeToBroadcast(u"com.flyingdiver.indigoplugin.mqtt", u"com.flyingdiver.indigoplugin.mqtt-message_queued", "message_handler")

    def shutdown(self):
        self.logger.info(u"Stopped ShellyMQTT...")

    def message_handler(self, message):
        if message['message_type'] not in self.messageTypes:
            # None of the devices care about this message
            self.logger.debug(u"ignoring MQTT message of type \"%s\"", message["message_type"])
            return
        else:
            self.logger.debug(u"Queued MQTT message type {} from {}".format(message["message_type"], indigo.devices[int(message["brokerID"])].name))
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
        self.logger.info(u"Starting \"%s\"...", device.name)

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

        shelly = createDeviceObject(device)
        # Ensure the device has a broker and address
        if shelly.getBrokerId() is None or shelly.getAddress() is None:
            self.logger.error("%s is not properly setup! Check the broker and topic root.", device.name)
            return False

        # Add the device id to our internal list of devices
        shelly.subscribe()
        self.addDeviceSubscriptions(shelly)
        self.shellyDevices[device.id] = shelly
        self.messageTypes.append(shelly.getMessageType())
        if shelly.getAnnounceMessageType():
            self.messageTypes.append(shelly.getAnnounceMessageType())

    def deviceStopComm(self, device):
        self.logger.info(u"Stopping \"%s\"...", device.name)
        if device.id not in self.shellyDevices:
            return

        shelly = self.shellyDevices[device.id]  # The shelly object for this device
        self.removeDeviceSubscriptions(shelly)  # Remove the subscriptions for this device
        self.messageTypes.remove(shelly.getMessageType())  # This device listens for a specific message

        # Attempt to unsubscribe from topics that are no longer being listened to
        if self.mqttPlugin.isEnabled():
            brokerSubscriptions = self.brokerDeviceSubscriptions[shelly.getBrokerId()]
            topicsToRemove = []
            for topic in brokerSubscriptions:
                if not brokerSubscriptions[topic]:  # If no device is listening on this topic anymore
                    # Band-aid for bug in MQTT-Connector (Issue #10 on MQTT-Connector GitHub)
                    if self.pluginPrefs.get('connector-fix', False):
                        topic = "0:%s" % topic

                    props = {
                        'topic': topic
                    }
                    # Unsubscribe the broker from this topic and remove the record of the topic
                    self.mqttPlugin.executeAction("del_subscription", deviceId=shelly.getBrokerId(), props=props)
                    topicsToRemove.append(topic)

            # Actually remove the unneeded lists associated with the unsubscribed topics
            for topic in topicsToRemove:
                # Band-aid for bug in MQTT-Connector (Issue #10 on MQTT-Connector GitHub)
                if self.pluginPrefs.get('connector-fix', False):
                    topic = topic[2:]
                del brokerSubscriptions[topic]

        del self.shellyDevices[device.id]

    def processMessages(self):
        """
        Processes messages in the queue until the queue is empty. This is used to pass
        messages that have come from MQTT into the appropriate devices.
        :return: None
        """
        while not self.messageQueue.empty():
            # At least 1 of the devices care about this message
            message = self.messageQueue.get()
            if not message:
                return

            # We have a valid message
            # Find the devices that need to get this message and give it to them
            brokerID = int(message['brokerID'])
            props = {'message_type': message['message_type']}
            while True:
                data = self.mqttPlugin.executeAction("fetchQueuedMessage", deviceId=brokerID, props=props, waitUntilDone=True)
                if data is None:  # Ensure we got data back
                    break

                topic = '/'.join(data['topic_parts'])  # transform the topic into a single string
                payload = data['payload']
                message_type = data['message_type']
                self.logger.debug(u"    Processing: \"%s\" on topic \"%s\"", payload, topic)
                deviceSubscriptions = self.brokerDeviceSubscriptions.get(brokerID, {})  # get device subscriptions for this broker
                devices = deviceSubscriptions.get(topic, list())  # get devices listening on this broker for this topic
                for deviceId in devices:
                    shelly = self.shellyDevices.get(deviceId, None)
                    if shelly is not None and message_type in shelly.getMessageTypes():
                        # Send this message data to the shelly object
                        self.logger.debug("        \"%s\" handling \"%s\" on \"%s\"", shelly.device.name, payload, topic)
                        shelly.handleMessage(topic, payload)

    def actionControlDevice(self, action, device):
        """
        Handles an action being performed on the device.
        :param action: The action that occurred.
        :param device: The device that was acted on.
        :return: None
        """
        shelly = self.shellyDevices.get(device.id, None)
        if shelly is not None:
            shelly.handleAction(action)

    def actionControlUniversal(self, action, device):
        """
        Handles an action being performed on the device.
        :param action: The action that occurred.
        :param device: The device that was acted on.
        :return: None
        """
        shelly = self.shellyDevices.get(device.id, None)
        if shelly is not None:
            shelly.handleAction(action)

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

    def getShellyDevices(self, filter="", valuesDict=None, typeId="", targetId=0):
        """
        Gets a list of available Shelly devices.
        :return: A list of shelly device tuples of the form (deviceId, name).
        """
        shellies = []
        for dev in indigo.devices.iter("self"):
            shellies.append((dev.id, dev.name))

        shellies.sort(key=lambda d: d[1])
        return shellies

    def getUpdatableShellyDevices(self, filter=None, valuesDict={}, typeId=None, targetId=None):
        """
        Gets a list of shelly devices that can be updated.
        :return: A list of Indigo deviceId's corresponding to updatable shelly devices.
        """
        shellies = self.getShellyDevices()
        updatable = []
        for dev in shellies:
            device = indigo.devices[dev[0]]
            if device.states.get('has-firmware-update', False):
                updatable.append(dev)
        return updatable

    def menuChanged(self, valuesDict, typeId):
        """
        Dummy function used to update a ConfigUI dynamic menu
        :param valuesDict:
        :param typeId:
        :param devId:
        :return: the values currently in the ConfigUI
        """
        return valuesDict

    def discoverShelly(self, pluginAction, device, callerWaitingForResult):
        shellyDevId = int(pluginAction.props['shelly-device-id'])
        shelly = self.shellyDevices[shellyDevId]
        if shelly:
            shelly.announce()

    def discoverShellies(self, pluginAction=None, device=None, callerWaitingForResult=False):
        """
        Sends a discovery message to all currently used brokers.
        :return: None
        """
        if not self.mqttPlugin.isEnabled():
            self.logger.error(u"MQTT plugin must be enabled!")
            return None
        else:
            if self.pluginPrefs.get('all-brokers-subscribe-to-announce', True):
                # Have all shellies on all broker devices send announcements
                brokerIds = map(lambda b: b[0], self.getBrokerDevices())
            else:
                # We need to get the user-specified brokers from the plugin config
                brokerIds = self.pluginPrefs.get('brokers-subscribing-to-announce', [])

            for brokerId in brokerIds:
                brokerId = int(brokerId)
                props = {
                    'topic': 'shellies/command',
                    'payload': 'announce',
                    'qos': 0,
                    'retain': 0,
                }
                self.mqttPlugin.executeAction("publish", deviceId=brokerId, props=props, waitUntilDone=False)
                self.logger.info(u"published \"announce\" to \"shellies/command\" on broker \"%s\"", indigo.devices[brokerId].name)

    def updateShelly(self, valuesDict, typeId):
        if valuesDict['shelly-device-id'] == "":
            errors = indigo.Dict()
            errors['shelly-device-id'] = "You must select a device to update!"
            return False, valuesDict, errors
        else:
            shellyDeviceId = int(valuesDict['shelly-device-id'])
            shelly = self.shellyDevices[shellyDeviceId]
            shelly.sendUpdateFirmwareCommand()
            return True

    def addDeviceSubscriptions(self, shelly):
        """
        Adds a Shelly device to the dictionary of device subscriptions.
        :param shelly: The Shelly device to add.
        :return: None
        """
        # ensure that deviceSubscriptions has a dictionary of subscriptions for the broker
        if shelly.getBrokerId() not in self.brokerDeviceSubscriptions:
            self.brokerDeviceSubscriptions[shelly.getBrokerId()] = {}

        brokerSubscriptions = self.brokerDeviceSubscriptions[shelly.getBrokerId()]
        subscriptions = shelly.getSubscriptions()
        for topic in subscriptions:
            # See if there is a list of devices already listening to this subscription
            if topic not in brokerSubscriptions:
                # initialize a new list of devices for this subscription
                brokerSubscriptions[topic] = []
            brokerSubscriptions[topic].append(shelly.device.id)
            # self.logger.debug(u"Added '%s' to '%s' on '%s'", shelly.device.name, topic, indigo.devices[shelly.getBrokerId()].name)

    def removeDeviceSubscriptions(self, shelly):
        """
        Removes a Shelly device from the dictionary of device subscriptions.
        :param shelly: The Shelly object to remove.
        :return: None
        """
        # make sure that the device's broker has subscriptions
        if shelly.getBrokerId() in self.brokerDeviceSubscriptions:
            brokerSubscriptions = self.brokerDeviceSubscriptions[shelly.getBrokerId()]
            subscriptions = shelly.getSubscriptions()
            for topic in subscriptions:
                if topic in brokerSubscriptions and shelly.device.id in brokerSubscriptions[topic]:
                    # self.logger.debug(u"Removed '%s' from '%s' on '%s'", shelly.device.name, topic, indigo.devices[shelly.getBrokerId()].name)
                    brokerSubscriptions[topic].remove(shelly.device.id)

            # remove the broker key if there are no more devices using it
            if len(brokerSubscriptions) == 0:
                del self.brokerDeviceSubscriptions[shelly.getBrokerId()]

    def printBrokerDeviceSubscriptions(self):
        """
        Prints the data structure that contains brokers, topics, and devices
        :return: None
        """
        self.logger.debug(u"Broker-Device Subscriptions:")
        for broker in self.brokerDeviceSubscriptions:
            self.logger.debug(u"    Broker %s:", broker)
            deviceSubscriptions = self.brokerDeviceSubscriptions[broker]
            for topic in deviceSubscriptions:
                self.logger.debug(u"        %s: %s", topic, deviceSubscriptions[topic])

    def validateActionConfigUi(self, valuesDict, typeId, deviceId):
        if typeId == "update-shelly":
            if valuesDict['shelly-device-id'] == "":
                errors = indigo.Dict()
                errors['shelly-device-id'] = "You must select a device to update!"
                return False, valuesDict, errors
            else:
                return True
        elif typeId == "discover-shelly":
            if valuesDict['shelly-device-id'] == "":
                errors = indigo.Dict()
                errors['shelly-device-id'] = "You must select a device to discover!"
                return False, valuesDict, errors
            else:
                return True
