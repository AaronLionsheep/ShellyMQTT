import indigo


def getBrokerDevices(plugin, filter="", valuesDict=None, typeId="", targetId=0):
    """
    Gets a list of available broker devices.

    :param plugin:
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


def getShellyDevices(plugin, filter="", valuesDict=None, typeId="", targetId=0):
    """
    Gets a list of available Shelly devices.

    :return: A list of shelly device tuples of the form (deviceId, name).
    """

    shellies = []
    if filter:
        types = [cat.strip() for cat in filter.split(",")]
        for dev_type in types:
            for dev in indigo.devices.iter(dev_type):
                shellies.append((dev.id, dev.name))
    else:
        for dev in indigo.devices.iter("self"):
            shellies.append((dev.id, dev.name))

    shellies.sort(key=lambda d: d[1])
    return shellies


def getDiscoveredDevices(plugin, filter=None, valuesDict={}, typeId=None, targetId=None):
    """
    Gets a list of discovered devices

    :return: A list of device tuples of the form (<broker-id>|<identifier>, displayName)
    """

    devices = []
    for brokerId in plugin.discoveredDevices:
        brokerName = indigo.devices[brokerId].name
        brokerDevices = plugin.discoveredDevices[brokerId]
        for identifier in brokerDevices:
            devices.append((u"{}|{}".format(brokerId, identifier), u"{} on {}".format(identifier, brokerName)))

    if len(devices) == 0:
        # No devices found, add a disabled option to indicate this
        devices.append((-1, u"%%disabled:No discovered devices%%"))

    return devices


def getTemplateDevices(plugin, filter=None, valuesDict={}, typeId=None, targetId=0):
    """
    Builds a list of devices that have been discovered or that are related to the device being created.

    :param plugin:
    :param filter: A comma separated list of device types
    :return: A list of device tuples of the form (<broker-id>|<identifier>, displayName)
    """

    # Build the discovered devices section
    discovered_devices = []
    for brokerId in plugin.discoveredDevices:
        brokerName = indigo.devices[brokerId].name
        brokerDevices = plugin.discoveredDevices[brokerId]
        for identifier in brokerDevices:
            discovered_devices.append((u"{}|shellies/{}".format(brokerId, identifier), u"{} on {}".format(identifier, brokerName)))

    # Build the related devices section
    related_devices = []
    types = [cat.strip() for cat in filter.split(",")]
    for dev_type in types:
        for device in indigo.devices.iter(dev_type):
            if device.id != targetId:  # We don't want the current device to be used as a template for itself
                brokerId = device.pluginProps.get('broker-id', None)
                address = device.pluginProps.get('address', None)
                message_type = device.pluginProps.get('message-type', None)
                related_devices.append((u"{}|{}|{}|{}".format(brokerId, address, message_type, device.name), u"{}".format(device.name)))

    # Join the device lists and build the menu
    devices = []
    devices.append((u"-1", u"%%disabled:Discovered Devices:%%"))
    if len(discovered_devices) == 0:
        devices.append((u"-1", u"%%disabled:No Discovered Devices%%"))
    else:
        devices.extend(discovered_devices)

    devices.append((u"-1", u"%%separator%%"))
    devices.append((u"-1", u"%%disabled:Related Devices:%%"))
    if len(related_devices) == 0:
        devices.append((u"-1", u"%%disabled:No Related Devices%%"))
    else:
        devices.extend(related_devices)

    return devices


def getUpdatableShellyDevices(plugin, filter=None, valuesDict={}, typeId=None, targetId=None):
    """
    Gets a list of shelly devices that can be updated.

    :return: A list of Indigo deviceId's corresponding to updatable shelly devices.
    """

    shellies = getShellyDevices()
    updatable = []
    for dev in shellies:
        device = indigo.devices[dev[0]]
        if device.states.get('has-firmware-update', False):
            updatable.append(dev)
    return updatable


def getAddonHostDevices(plugin, filter=None, valuesDict={}, typeId=None, targetId=None):
    """
    Gets a list of Shelly devices (1/1PM) that are capable of "hosting" an add-on sensor.

    :return: A list of devices which are capable to hosting add-ons.
    """

    hostable_model_categories = {  # Shelly models that can host an "addon"
        "ds1820": ["shelly-1", "shelly-1pm", "shelly-uni-relay", "shelly-uni-input"],
        "dht22": ["shelly-1", "shelly-1pm", "shelly-uni-relay", "shelly-uni-input"],
        "detached-switch": ["shelly-1", "shelly-1pm", "shelly-2-5-relay", "shelly-4-pro", "shelly-dimmer-sl"]
    }

    hostable_models = set()
    if filter:
        categories = [cat.strip() for cat in filter.split(",")]
        for category in categories:
            models = hostable_model_categories.get(category, None)
            if models:
                for model in models:
                    hostable_models.add(model)

    shellies = getShellyDevices()
    hostable = []
    for dev in shellies:
        shelly = plugin.shellyDevices.get(dev[0])
        if shelly and shelly.device.deviceTypeId in hostable_models:
            hostable.append(dev)
    return hostable