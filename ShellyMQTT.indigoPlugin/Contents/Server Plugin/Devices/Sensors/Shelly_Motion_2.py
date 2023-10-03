# coding=utf-8
import indigo
import json
from ..Shelly import Shelly


class Shelly_Motion_2(Shelly):
    """
    The Shelly Motion is battery-operated motion sensor.
    """

    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        """
        Default method to return a list of topics that the device subscribes to.

        :return: A list of topics.
        """

        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "shellies/announce",
                "{}/online".format(address),
                "{}/info".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """

        if topic == "{}/info".format(self.getAddress()):
            """
            The payload will json in the form:
            
            {
                "wifi_sta":{
                    "connected":true,
                    "ssid":"Lionsheep",
                    "ip":"192.168.100.76",
                    "rssi":-57
                },
                "cloud":{
                    "enabled":false,
                    "connected":false
                },
                "mqtt":{
                    "connected":true
                },
                "time":"14:09",
                "unixtime":1661018974,
                "serial":0,
                "has_update":false,
                "mac":"84FD2772A492",
                "cfg_changed_cnt":0,
                "actions_stats":{
                    "skipped":0
                },
                "sleep_time":0,
                "lux":{
                    "value":128,
                    "illumination":"twilight",
                    "is_valid":true
                },
                "tmp":{
                    "value":79.0,
                    "units":"F",
                    "is_valid":true
                },
                "sensor":{
                    "vibration":false,
                    "motion":false,
                    "timestamp":1661018914,
                    "active":true,
                    "is_valid":true
                },
                "bat":{
                    "value":91,
                    "voltage":3.792
                },
                "charger":false,
                "update":{
                    "status":"unknown",
                    "has_update":false,
                    "new_version":"20220811-152232/v2.1.8@5afc928c",
                    "old_version":"20220811-152232/v2.1.8@5afc928c",
                    "beta_version":null
                },
                "ram_total":97280,
                "ram_free":22408,
                "fs_size":65536,
                "fs_free":59504,
                "uptime":211075,
                "fw_info":{
                    "device":"shellymotion2-84FD2772A492",
                    "fw":"20220811-152232/v2.1.8@5afc928c"
                },
                "ps_mode":0,
                "dbg_flags":0
            }
            """
            try:
                payload = json.loads(payload)

                if payload.get("lux", {}).get("is_valid", False):
                    lux = payload.get("lux", {}).get("value", None)
                    illumination = payload.get("lux", {}).get("illumination", None)
                    self.device.updateStateOnServer(key='lux', value=lux)
                    self.device.updateStateOnServer(key='illumination', value=illumination)

                if payload.get("tmp", {}).get("is_valid", False):
                    temperature = payload.get("tmp", {}).get("value", None)
                    units = payload.get("tmp", {}).get("units", None)
                    self.device.updateStateOnServer(key='temperature', value=temperature,
                                                    uiValue="{} °{}".format(temperature, units))

                if payload.get("sensor", {}).get("is_valid", False):
                    vibration = payload.get("sensor", {}).get("vibration", False)
                    motion = payload.get("sensor", {}).get("motion", False)
                    self.device.updateStateOnServer(key='vibration', value=vibration)
                    self.device.updateStateOnServer(key='onOffState', value=motion)
                    self.updateStateImage()

                if payload.get("bat", None):
                    level = payload.get("bat", {}).get("value", None)
                    voltage = payload.get("bat", {}).get("voltage", None)
                    self.updateBatteryLevel(level)
                    self.device.updateStateOnServer(key='voltage', value=voltage,
                                                    uiValue="{}V".format(voltage))

            except ValueError:
                self.logger.error(u"Problem parsing JSON: {}".format(payload))
        else:
            Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """

        Shelly.handleAction(self, action)

    def updateStateImage(self):
        """
        Sets the state image based on device states.

        :return: None
        """

        if self.device.states.get('onOffState', False):
            self.device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
        else:
            self.device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)

    @staticmethod
    def validateConfigUI(valuesDict, typeId, devId):
        """
        Validates a device config.

        :param valuesDict: The values in the Config UI.
        :param typeId: the device type as specified in the type attribute.
        :param devId: The id of the device (0 if a new device).
        :return: Tuple of the form (valid, valuesDict, errors)
        """

        errors = indigo.Dict()
        isValid = True
        # The Shelly 1 needs to ensure the user has selected a Broker device, supplied the address, and supplied the message type.
        # If the user has indicated that announcement messages are separate, then they need to supply that message type as well.

        # Validate the broker
        brokerId = valuesDict.get('broker-id', None)
        if not brokerId.strip():
            isValid = False
            errors['broker-id'] = u"You must select the broker to which the Shelly is connected to."

        # Validate the address
        address = valuesDict.get('address', None)
        if not address.strip():
            isValid = False
            errors['address'] = u"You must enter the MQTT topic root for the Shelly."

        # Validate the message type
        messageType = valuesDict.get('message-type', None)
        if not messageType.strip():
            isValid = False
            errors['message-type'] = u"You must enter the message type that this Shelly will be associated with."

        # Validate the announcement message type
        hasSameAnnounceMessageType = valuesDict.get('announce-message-type-same-as-message-type', True)
        if not hasSameAnnounceMessageType:  # We would expect a supplied message type for announcement messages
            announceMessageType = valuesDict.get('announce-message-type', None)
            if not announceMessageType.strip():
                isValid = False
                errors['announce-message-type'] = u"You must supply the message type that will be associated with the announce messages."

        return isValid, valuesDict, errors
