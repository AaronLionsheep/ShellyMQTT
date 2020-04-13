import indigo

# Import the relay devices
from Devices.Relays.Shelly_1 import Shelly_1
from Devices.Relays.Shelly_1PM import Shelly_1PM
from Devices.Relays.Shelly_2_5_Relay import Shelly_2_5_Relay
from Devices.Relays.Shelly_4_Pro import Shelly_4_Pro
from Devices.Relays.Shelly_EM_Relay import Shelly_EM_Relay

from Devices.Shelly_Dimmer_SL import Shelly_Dimmer_SL

# Import the sensor devices
from Devices.Sensors.Shelly_HT import Shelly_HT
from Devices.Sensors.Shelly_Flood import Shelly_Flood
from Devices.Sensors.Shelly_Door_Window import Shelly_Door_Window
from Devices.Sensors.Shelly_EM_Meter import Shelly_EM_Meter
from Devices.Sensors.Shelly_3EM_Meter import Shelly_3EM_Meter

# Import the bulb devices
from Devices.Bulbs.Shelly_Bulb import Shelly_Bulb
from Devices.Bulbs.Shelly_Bulb_Vintage import Shelly_Bulb_Vintage
from Devices.Bulbs.Shelly_Bulb_Duo import Shelly_Bulb_Duo

# Import the plug devices
from Devices.Plugs.Shelly_Plug import Shelly_Plug
from Devices.Plugs.Shelly_Plug_S import Shelly_Plug_S

# Import the add-on devices
from Devices.Addons.Shelly_Addon_DS1820 import Shelly_Addon_DS1820
from Devices.Addons.Shelly_Addon_DHT22 import Shelly_Addon_DHT22

from Queue import Queue

kCurDevVersion = 0  # current version of plugin devices

# Maps each device type to a python class for the device
deviceClasses = {
    # Relay devices
    "shelly-1": Shelly_1,
    "shelly-1pm": Shelly_1PM,
    "shelly-2-5-relay": Shelly_2_5_Relay,
    "shelly-4-pro": Shelly_4_Pro,
    "shelly-em-relay": Shelly_EM_Relay,

    # Sensor devices
    "shelly-ht": Shelly_HT,
    "shelly-flood": Shelly_Flood,
    "shelly-door-window": Shelly_Door_Window,
    "shelly-em-meter": Shelly_EM_Meter,
    "shelly-3em-meter": Shelly_3EM_Meter,

    # Bulb devices
    "shelly-bulb": Shelly_Bulb,
    "shelly-bulb-vintage": Shelly_Bulb_Vintage,
    "shelly-bulb-duo": Shelly_Bulb_Duo,

    # Plug devices
    "shelly-plug": Shelly_Plug,
    "shelly-plug-s": Shelly_Plug_S,

    # Add-on devices
    "shelly-addon-ds1820": Shelly_Addon_DS1820,
    "shelly-addon-dht22": Shelly_Addon_DHT22,

    "shelly-dimmer-sl": Shelly_Dimmer_SL
}


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
        #   devId: <Indigo device id>,
        #   anotherDevId: <Shelly object>
        # }
        # This is used to store devices that had unresolved depenedeneices
        # For example, a temperature addon being started before its host device
        self.dependents = {}

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
        """
        Called by Indigo to start the plugin.

        :return: None
        """

        if not self.mqttPlugin:
            self.logger.error(u"MQTT Connector plugin is required!!")
            exit(-1)
        indigo.server.subscribeToBroadcast(u"com.flyingdiver.indigoplugin.mqtt", u"com.flyingdiver.indigoplugin.mqtt-message_queued", "message_handler")

    def shutdown(self):
        """
        Called by Indigo to shutdown the plugin

        :return: None
        """

        self.logger.info(u"Stopped ShellyMQTT...")

    def runConcurrentThread(self):
        """
        Main work thread where messages are continually dequeued and processed.

        :return: None
        """

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
        """
        Handler for the closing of a configuration UI.

        :param valuesDict: The values in the config.
        :param userCancelled: True or false to indicate if the config was cancelled.
        :return: True or false to indicate if the config is valid.
        """

        if userCancelled is False:
            self.debug = valuesDict.get('debugMode', False)

        if self.debug is True:
            self.logger.info(u"Debugging on")
        else:
            self.logger.info(u"Debugging off")

    def createDeviceObject(self, device):
        """
        Helper function to generate a Shelly object from an indigo device

        :param device: The Indigo device object.
        :return: A Shelly device object.
        """

        deviceType = device.deviceTypeId
        deviceClass = deviceClasses[deviceType]
        if deviceClass:
            return deviceClass(device)
        else:
            self.logger.error(u"Unable to build a device with type \"{}\"".format(deviceType))

    def deviceStartComm(self, device):
        """
        Handles processes for starting a device. This will check dependencies, validate configurations,
        subscribe to topics, and add message handlers.

        :param device: The device that is starting
        :return: True or false to indicate if the device was started.
        """

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

        #
        # Get or generate a shelly device
        #
        shelly = self.createDeviceObject(device)
        if not shelly:
            # The device is not dependent on a device and was not able to be created...
            self.logger.error(u"\"{}\" has an unknown deviceTypeId of: \"{}\"!".format(device.name, device.deviceTypeId))
            return False

        #
        # If the device starting is an addon device, make sure the host has already been started
        # Save the device so that the host can trigger it to start later
        #
        if shelly.isAddon():
            # Ensure the temperature addon has a host
            if shelly.getHostDevice() is None:
                # If the host is missing, this device has been started before the host
                if device.id in self.dependents.keys():
                    # This device has already been attempted to be started, so it must not have a host defined
                    self.logger.error(u"{} is not properly setup! Check the device host.".format(device.name))
                    del self.dependents[device.id]
                    return False
                else:
                    # Could not get a host, but this is the first time the device is starting
                    # Add it to the known device list and stop attempting startup
                    # The host will attempt to start any of its addons
                    self.dependents[device.id] = shelly
                    self.logger.info(u"{} is queued to be started after the host starts".format(shelly.device.name))
                    return False

        self.logger.info(u"Starting \"%s\"...", device.name)

        #
        # Check that the device has a broker and an address
        #
        if shelly.getBrokerId() is None or shelly.getAddress() is None:
            # Ensure the device has a broker and address
            self.logger.error(u"brokerId: \"{}\" address: \"{}\"".format(shelly.getBrokerId(), shelly.getAddress()))
            self.logger.error(u"\"{}\" is not properly setup! Check the broker and topic root.".format(device.name))
            return False

        #
        # Add the device id to our internal list of devices
        #
        shelly.subscribe()
        self.addDeviceSubscriptions(shelly)
        self.shellyDevices[device.id] = shelly
        self.messageTypes.append(shelly.getMessageType())
        if shelly.getAnnounceMessageType():
            self.messageTypes.append(shelly.getAnnounceMessageType())

        #
        # Attempt to start any addon devices that this device hosts
        #
        for dependentId in self.dependents.keys():
            addon = self.dependents[dependentId]
            if addon.isAddon() and addon.getHostDevice() and addon.getHostDevice().device.id == shelly.device.id:
                # This addon is hosted by the device that has just been started, so it must have failed startup before
                del self.dependents[dependentId]
                self.deviceStartComm(indigo.devices[dependentId])

    def deviceStopComm(self, device):
        """
        Handles processes for a device that has been told to stop communication.
        Cleanup happens here. This includes removing subscriptions,
        removing listeners, and not tracking this device.

        :param device: The device that is stopping.
        :return: True or false to indicate if the device was stopped.
        """

        if device.id not in self.shellyDevices:
            return
        self.logger.info(u"Stopping \"%s\"...", device.name)

        shelly = self.shellyDevices[device.id]  # The shelly object for this device

        #
        # See if any add-ons are connected
        #
        for addonDev in self.shellyDevices.keys():
            addon_shelly = self.shellyDevices[addonDev]
            if addon_shelly.isAddon() and addon_shelly.getHostDevice().device.id == shelly.device.id:
                self.deviceStopComm(addon_shelly.device)

        #
        # Remove subscriptions and message handlers
        #
        self.removeDeviceSubscriptions(shelly)
        for message_type in shelly.getMessageTypes():
            self.messageTypes.remove(message_type)

        #
        # Attempt to unsubscribe from topics that are no longer being listened to
        #
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

            #
            # Actually remove the unneeded lists associated with the unsubscribed topics
            #
            for topic in topicsToRemove:
                # Band-aid for bug in MQTT-Connector (Issue #10 on MQTT-Connector GitHub)
                if self.pluginPrefs.get('connector-fix', False):
                    topic = topic[2:]
                del brokerSubscriptions[topic]

        del self.shellyDevices[device.id]

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

    def message_handler(self, message):
        """
        Handler to receive and queue messages coming from the mqtt plugin.

        :param message: The message object.
        :return: None
        """

        if message['message_type'] not in self.messageTypes:
            # None of the devices care about this message
            self.logger.debug(u"ignoring MQTT message of type \"%s\"", message["message_type"])
            return
        else:
            self.logger.debug(u"Queued MQTT message type {} from {}".format(message["message_type"], indigo.devices[int(message["brokerID"])].name))
            self.messageQueue.put(message)

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
                        self.logger.debug(u"        \"%s\" handling \"%s\" on \"%s\"", shelly.device.name, payload, topic)
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

    ###############################
    #     Getters for Devices     #
    ###############################

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

    def getAddonHostDevices(self, filter=None, valuesDict={}, typeId=None, targetId=None):
        """
        Gets a list of Shelly devices (1/1PM) that are capable of "hosting" an add-on sensor.

        :return: A list of devices which are capable to hosting add-ons.
        """

        shellies = self.getShellyDevices()
        hostable_models = ["shelly-1", "shelly-1pm"]
        hostable = []
        for dev in shellies:
            shelly = self.shellyDevices.get(dev[0])
            if shelly and shelly.device.deviceTypeId in hostable_models:
                hostable.append(dev)
        return hostable

    #################################
    #     Actions from the User     #
    #################################

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
        """
        Handler for discovering a targeted Shelly device. This will send an announce command to
        the selected Shelly device.

        :param pluginAction: The action data.
        :param device:
        :param callerWaitingForResult:
        :return: None
        """

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
                if indigo.devices[brokerId].enabled:
                    props = {
                        'topic': 'shellies/command',
                        'payload': 'announce',
                        'qos': 0,
                        'retain': 0,
                    }
                    self.mqttPlugin.executeAction("publish", deviceId=brokerId, props=props, waitUntilDone=False)
                    self.logger.info(u"published \"announce\" to \"shellies/command\" on broker \"%s\"", indigo.devices[brokerId].name)

    def updateShelly(self, valuesDict, typeId):
        """
        Handler for the Update Helper.
        This will send an update command to the selected shelly device.

        :param valuesDict: Data from the UI.
        :param typeId:
        :return: True or false depending on the validity of the submitted data.
        """

        if valuesDict['shelly-device-id'] == "":
            errors = indigo.Dict()
            errors['shelly-device-id'] = "You must select a device to update!"
            return False, valuesDict, errors
        else:
            shellyDeviceId = int(valuesDict['shelly-device-id'])
            shelly = self.shellyDevices[shellyDeviceId]
            shelly.sendUpdateFirmwareCommand()
            return True

    def timedOn(self, pluginAction, device, callerWaitingForResult):
        """
        Turns a configured device on for a specified duration before turning it back off.

        :param pluginAction: The action properties.
        :param device: N/A
        :param callerWaitingForResult: N/A
        :return: None
        """

        deviceId = int(pluginAction.props['device-id'])
        duration = int(pluginAction.props['duration'])
        indigo.device.turnOn(deviceId, delay=0, duration=duration)

    def timedOff(self, pluginAction, device, callerWaitingForResult):
        """
        Turns a configured device off for a specified duration before turning it back on.

        :param pluginAction: The action properties.
        :param device: N/A
        :param callerWaitingForResult: N/A
        :return: none
        """

        deviceId = int(pluginAction.props['device-id'])
        duration = int(pluginAction.props['duration'])
        indigo.device.turnOff(deviceId, delay=0, duration=duration)

    #####################
    #     Utilities     #
    #####################

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

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: True if the config is valid.
        """

        # Container for errors found and their reasons
        errors = indigo.Dict()

        if typeId == "shelly-1pm":
            pass
        elif typeId == "shelly-2.5":
            pass
        elif typeId == "shelly-ht":
            # Check for a valid temperature offset
            tempOffset = valuesDict.get('temp-offset')
            if tempOffset == "":
                valuesDict['temp-offset'] = 0
            else:
                try:
                    float(tempOffset)
                except ValueError:
                    errors['temp-offset'] = "Unable to convert this value to a float!"

            # Check for a valid humidity offset
            humidityOffset = valuesDict.get('humidity-offset')
            if humidityOffset == "":
                valuesDict['humidity-offset'] = 0
            else:
                try:
                    float(humidityOffset)
                except ValueError:
                    errors['humidity-offset'] = "Unable to convert this value to a float!"
        elif typeId == "shelly-flood":
            # Check for a valid temperature offset
            tempOffset = valuesDict.get('temp-offset')
            if tempOffset == "":
                valuesDict['temp-offset'] = 0
            else:
                try:
                    float(tempOffset)
                except ValueError:
                    errors['temp-offset'] = "Unable to convert this value to a float!"
        elif typeId == "shelly-door-window":
            pass
        elif typeId == "shelly-dimmer-sl":
            pass
        elif typeId == "shelly-addon-ds1820":
            # Check for a valid temperature offset
            tempOffset = valuesDict.get('temp-offset')
            if tempOffset == "":
                valuesDict['temp-offset'] = 0
            else:
                try:
                    float(tempOffset)
                except ValueError:
                    errors['temp-offset'] = "Unable to convert this value to a float!"
        elif typeId == "shelly-addon-dht22":
            # Check for a valid temperature offset
            tempOffset = valuesDict.get('temp-offset')
            if tempOffset == "":
                valuesDict['temp-offset'] = 0
            else:
                try:
                    float(tempOffset)
                except ValueError:
                    errors['temp-offset'] = "Unable to convert this value to a float!"

            # Check for a valid humidity offset
            humidityOffset = valuesDict.get('humidity-offset')
            if humidityOffset == "":
                valuesDict['humidity-offset'] = 0
            else:
                try:
                    float(humidityOffset)
                except ValueError:
                    errors['humidity-offset'] = "Unable to convert this value to a float!"
        elif typeId == "shelly-plug-s":
            pass

        if len(errors) == 0:
            # No errors were found, must be valid
            return True, valuesDict
        else:
            # Errors were found, return the data back and the errors
            return False, valuesDict, errors

    def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId):
        # self.shellyDevices[devId].device = indigo.devices[devId]
        # self.logger.info(indigo.devices[devId].pluginProps)
        pass

    def validateActionConfigUi(self, valuesDict, typeId, deviceId):
        """
        Validates an action config UI.

        :param valuesDict: The values in the UI.
        :param typeId:
        :param deviceId:
        :return: True or false based on the validity of the data.
        """

        errors = indigo.Dict()

        if typeId == "update-shelly":
            if valuesDict['shelly-device-id'] == "":
                errors['shelly-device-id'] = "You must select a device to update!"
        elif typeId == "discover-shelly":
            if valuesDict['shelly-device-id'] == "":
                errors['shelly-device-id'] = "You must select a device to discover!"
        elif typeId == "timed-on" or typeId == "timed-off":
            if valuesDict['device-id'] == "":
                errors['device-id'] = "You must select a device!"

            try:
                int(valuesDict['duration'])
            except ValueError:
                errors['duration'] = "Unable to convert this value to an integer!"

        if len(errors) == 0:
            return True
        else:
            return False, valuesDict, errors
