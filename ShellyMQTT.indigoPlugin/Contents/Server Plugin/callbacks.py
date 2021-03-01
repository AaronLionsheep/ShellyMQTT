import indigo
import os

"""
Methods defined in this file are all used as callback methods in the user interface.
Indigo expects these to be located in plugin.py, however there is logic in plugin.py
which handles calling these methods. The UI adds a prefix of "cb_" to the method name,
which causes plugin.py to search for them here.

For example:

<Action id="discover-shellies">
    <Name>Discover All Shellies</Name>
    <CallbackMethod>cb_discoverShellies</CallbackMethod>
</Action>

The method defined in this file called "discoverShellies" will actually be called.
"""


def discoverShelly(plugin, pluginAction, device, callerWaitingForResult):
    """
    Handler for discovering a targeted Shelly device. This will send an announce command to
    the selected Shelly device.

    :param plugin:
    :param pluginAction: The action data.
    :param device:
    :param callerWaitingForResult:
    :return: None
    """

    shellyDevId = int(pluginAction.props['shelly-device-id'])
    shelly = plugin.shellyDevices[shellyDevId]
    if shelly:
        shelly.announce()


def discoverShellies(plugin, pluginAction=None, device=None, callerWaitingForResult=False):
    """
    Sends a discovery message to all currently used brokers.

    :return: None
    """

    if not plugin.mqttPlugin.isEnabled():
        plugin.logger.error(u"MQTT plugin must be enabled!")
        return None
    else:
        if plugin.pluginPrefs.get('all-brokers-subscribe-to-announce', True):
            # Have all shellies on all broker devices send announcements
            brokerIds = map(lambda b: b[0], plugin.getBrokerDevices())
        else:
            # We need to get the user-specified brokers from the plugin config
            brokerIds = plugin.pluginPrefs.get('brokers-subscribing-to-announce', [])

        for brokerId in brokerIds:
            brokerId = int(brokerId)
            if indigo.devices[brokerId].enabled:
                props = {
                    'topic': 'shellies/command',
                    'payload': 'announce',
                    'qos': 0,
                    'retain': 0,
                }
                plugin.mqttPlugin.executeAction("publish", deviceId=brokerId, props=props, waitUntilDone=False)
                plugin.logger.debug(u"published \"announce\" to \"shellies/command\" on broker \"%s\"", indigo.devices[brokerId].name)


def updateShelly(plugin, valuesDict, typeId):
    """
    Handler for the Update Helper.
    This will send an update command to the selected shelly device.

    :param plugin:
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
        shelly = plugin.shellyDevices[shellyDeviceId]
        shelly.sendUpdateFirmwareCommand()
        return True


def menuChanged(plugin, valuesDict, typeId):
    """
    Dummy function used to update a ConfigUI dynamic menu

    :return: the values currently in the ConfigUI
    """

    return valuesDict


def timedOn(plugin, pluginAction, device, callerWaitingForResult):
    """
    Turns a configured device on for a specified duration before turning it back off.

    :param plugin:
    :param pluginAction: The action properties.
    :param device: N/A
    :param callerWaitingForResult: N/A
    :return: None
    """

    deviceId = int(pluginAction.props['device-id'])
    duration = int(pluginAction.props['duration'])
    indigo.device.turnOn(deviceId, delay=0, duration=duration)


def timedOff(plugin, pluginAction, device, callerWaitingForResult):
    """
    Turns a configured device off for a specified duration before turning it back on.

    :param plugin:
    :param pluginAction: The action properties.
    :param device: N/A
    :param callerWaitingForResult: N/A
    :return: none
    """

    deviceId = int(pluginAction.props['device-id'])
    duration = int(pluginAction.props['duration'])
    indigo.device.turnOff(deviceId, delay=0, duration=duration)


def printDiscoveredShellies(plugin, pluginAction=None, device=None, callerWaitingForResult=False):
    """
    Print out all discovered shellies connected to each broker

    :param plugin:
    :param pluginAction:
    :param device:
    :param callerWaitingForResult:
    :return: None
    """

    if len(plugin.discoveredDevices.keys()) == 0:
        plugin.logger.info(u"No announcement messages have been parsed yet. Run \"Discover Shellies\" to update device info.")
        return

    for brokerId in plugin.discoveredDevices.keys():
        broker = indigo.devices[int(brokerId)]
        if len(plugin.discoveredDevices[brokerId].keys()) == 0:
            plugin.logger.info(u"No newly discovered devices on \"{}\"!".format(broker.name))
        else:
            plugin.logger.info(u"Newly discovered devices on \"{}\"".format(broker.name))
            for identifier in plugin.discoveredDevices[brokerId].keys():
                ip = plugin.discoveredDevices[brokerId][identifier].get('ip', '')
                plugin.logger.info(u"    {:25} ({})".format(identifier, ip))


def printShellyDevicesOverview(plugin, pluginAction=None, device=None, callerWaitingForResult=False):
    """
    Print out all shellies connected to each broker

    :param plugin:
    :param pluginAction:
    :param device:
    :param callerWaitingForResult:
    :return: None
    """

    overview = {}
    # {
    #     broker1Id: [shelly1, shelly2],
    #     broker2Id: [shelly3, shelly4]
    # }

    # Gather our devices
    for shelly in plugin.shellyDevices.values():
        brokerId = shelly.getBrokerId()
        if brokerId not in overview.keys():
            overview[brokerId] = []

        overview[brokerId].append(shelly)

    # Output
    nameLength = 40
    ipLength = 15
    addressLength = 40
    updateLength = 16
    firmwareLength = 35
    row = u"{no: >2} | {name: <{nameWidth}}|{ip: ^{ipWidth}}| {address: <{addressWidth}}| {host: ^{nameWidth}}|{update: ^{updateWidth}}|{firmware: ^{firmwareWidth}}| {no: <2}"

    def logDividerRow():
        plugin.logger.info(
            u"   +{5:-^{0}s}+{5:-<{1}s}+{5:-<{2}s}+{5:-<{0}s}+{5:-<{3}s}+{5:-<{4}s}+".format(nameLength + 3, ipLength + 2, addressLength + 3, updateLength + 2,
                                                                                             firmwareLength + 2, ""))

    def logRow(name, ip, address, host, update, firmware, no=""):
        plugin.logger.info(
            row.format(no=no, name=name, nameWidth=nameLength + 2, ip=ip, ipWidth=ipLength + 2, address=address, addressWidth=addressLength + 2, host=host,
                       update=update, updateWidth=updateLength + 2, firmware=firmware, firmwareWidth=firmwareLength + 2))

    for brokerId in overview.keys():
        plugin.logger.info(u"Shelly devices connected to {} ({})".format(indigo.devices[brokerId].name, len(overview[brokerId])))
        logDividerRow()
        logRow(name="Name", ip="IP Address", address="MQTT Address", host="Host Device", update="Update Available", firmware="Current Firmware")
        logDividerRow()

        shellies = sorted(overview[brokerId], key=lambda s: s.device.name)
        no = 1
        for shelly in shellies:
            if not shelly.isAddon():
                logRow(no=str(no), name=shelly.device.name, ip=shelly.getIpAddress(), address=shelly.getAddress(), host="N/A",
                       update="Yes" if shelly.updateAvailable() else "No", firmware=shelly.getFirmware())
            else:
                logRow(no=str(no), name=shelly.device.name, ip=shelly.getIpAddress(), address="", host=shelly.getHostDevice().device.name, update="", firmware="")
            no += 1

        logDividerRow()


def logBuildCode(plugin, pluginAction=None, device=None, callerWaitingForResult=False):
    build_code_file = open("{}/build_code.txt".format(os.getcwd()))
    plugin.logger.info(u"Build code: {}".format(build_code_file.read()))
    build_code_file.close()


def dispatchEventToDevice(plugin, pluginAction, device, callerWaitingForResult):
    deviceId = int(pluginAction.props['device-id'])
    if not deviceId:
        return

    shelly = plugin.shellyDevices[deviceId]
    if not shelly:
        return

    shelly.handlePluginAction(pluginAction)
