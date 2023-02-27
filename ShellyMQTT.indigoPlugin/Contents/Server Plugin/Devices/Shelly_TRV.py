# coding=utf-8
import indigo
import json
from .Shelly import Shelly


class Shelly_TRV(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.HvacHeating)
        self.device.updateStateOnServer("hvacOperationMode", value=indigo.kHvacMode.Heat)
        self.device.updateStateOnServer("hvacHeaterIsOn", value=True)

        self.schedule_profile_names = []

    def getSubscriptions(self):
        """
        Default method to return a list of topics that the device subscribes to.

        :return: A list.
        """
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "shellies/announce",
                "{}/online".format(address),
                "{}/info".format(address),
                "{}/settings".format(address)
            ]

    def handleMessage(self, topic, payload):
        """
        This method is called when a message comes in and matches one of this devices subscriptions.

        :param topic: The topic of the message.
        :param payload: THe payload of the message.
        :return: None
        """
        if topic == "{}/info".format(self.getAddress()):
            payload = json.loads(payload)

            battery = payload.get("bat", {})
            charger = payload.get("charger", None)
            calibrated = payload.get("calibrated", None)
            thermostats = payload.get("thermostats", [])
            thermostat = thermostats[self.getChannel()] if len(thermostats) > self.getChannel() else {}

            self.updateBattery(battery)
            self.updateCharger(charger)
            self.updateCalibrated(calibrated)
            self.processThermostat(thermostat)
        elif topic == "{}/settings".format(self.getAddress()):
            payload = json.loads(payload)
            thermostats = payload.get("thermostats", [])
            thermostat = thermostats[self.getChannel()] if len(thermostats) > self.getChannel() else {}

            self.processThermostat(thermostat)
        else:
            Shelly.handleMessage(self, topic, payload)

    def updateBattery(self, battery):
        """
        Process the battery information from an info payload.

        :param battery: The battery state from the device.
        :return: None
        """
        level = battery.get("value", None)
        voltage = battery.get("voltage", None)

        if level is not None:
            self.updateBatteryLevel(level)
        if voltage is not None:
            self.device.updateStateOnServer(
                key="voltage",
                value=voltage,
                uiValue='{}V'.format(voltage)
            )

    def updateCharger(self, charger):
        """
        Process the charger information from an info payload.

        :param charger: The charger value from the device.
        :return: None
        """
        if isinstance(charger, bool):
            self.device.updateStateOnServer(
                key="charging",
                value=charger
            )

    def updateCalibrated(self, calibrated):
        """
        Process the calibrated information from an info payload.

        :param calibrated: The calibrated value from the device.
        :return: None
        """
        if isinstance(calibrated, bool):
            self.device.updateStateOnServer(
                key="calibrated",
                value=calibrated
            )

    def processThermostat(self, thermostat):
        """

        :param thermostat:
        :return:
        """
        target_temperature = thermostat.get("target_t", {}).get("value")
        sensor_temperature = thermostat.get("tmp", {}).get("value")
        boost_minutes = thermostat.get("boost_minutes", None)
        valve_position = thermostat.get("pos", None)
        schedule = thermostat.get("schedule", False)
        schedule_profile = thermostat.get("schedule_profile")
        self.schedule_profile_names = thermostat.get("schedule_profile_names", [])

        if target_temperature is not None:
            if self.device.pluginProps.get("temp-units", "C") == "F":
                target_temperature = round((target_temperature * 9 / 5) + 32)
            self.device.updateStateOnServer(key="setpointHeat", value=target_temperature)

        if sensor_temperature is not None:
            if self.device.pluginProps.get("temp-units", "C") == "F":
                sensor_temperature = round((sensor_temperature * 9 / 5) + 32)
            self.device.updateStateOnServer(key="temperatureInput1", value=sensor_temperature)

        if isinstance(boost_minutes, int):
            self.device.updateStateOnServer(
                key="boost-minutes",
                value=boost_minutes
            )

        if valve_position is not None:
            self.device.updateStateOnServer(
                key="valve-position",
                value=valve_position,
                uiValue="{}% open".format(valve_position)
            )

        if schedule:
            self.device.updateStateOnServer(key="schedule-profile", value=schedule_profile)
        else:
            self.device.updateStateOnServer(key="schedule-profile", value=None)

    def handleAction(self, action):
        """
        The method that gets called when an Indigo action takes place.

        :param action: The Indigo action.
        :return: None
        """
        if action.thermostatAction == indigo.kThermostatAction.SetHeatSetpoint:
            self.commandHeatSetpoint(action.actionValue)
        elif action.thermostatAction == indigo.kThermostatAction.DecreaseHeatSetpoint:
            target = self.device.states["setpointHeat"] - action.actionValue
            self.commandHeatSetpoint(target)
        elif action.thermostatAction == indigo.kThermostatAction.IncreaseHeatSetpoint:
            target = self.device.states["setpointHeat"] + action.actionValue
            self.commandHeatSetpoint(target)
        else:
            Shelly.handleAction(self, action)

    def handlePluginAction(self, action):
        """

        :param action:
        :return:
        """
        if action.pluginTypeId == "trv-start-boost":
            duration = action.props.get("duration")
            if duration:
                self.publish(
                    "{}/thermostat/{}/command/boost_minutes".format(
                        self.getAddress(),
                        self.getChannel()
                    ),
                    duration
                )
        elif action.pluginTypeId == "trv-stop-boost":
            self.publish(
                "{}/thermostat/{}/command/boost_minutes".format(
                    self.getAddress(),
                    self.getChannel()
                ),
                "0"
            )
        elif action.pluginTypeId == "trv-set-schedule-profile":
            schedule_profile = action.props.get("schedule-profile")
            enable_schedule = action.props.get("enable-schedule", False)
            self.publish(
                "{}/thermostat/{}/command/schedule_profile".format(
                    self.getAddress(),
                    self.getChannel()
                ),
                schedule_profile
            )

            self.publish(
                "{}/thermostat/{}/command/schedule".format(
                    self.getAddress(),
                    self.getChannel()
                ),
                "1" if enable_schedule else "0"
            )
        elif action.pluginTypeId == "trv-disable-schedule":
            self.publish(
                "{}/thermostat/{}/command/schedule".format(
                    self.getAddress(),
                    self.getChannel()
                ),
                "0"
            )

    def commandHeatSetpoint(self, value):
        """
        Command the device to change the heat setpoint.

        :param value: The value to set the setpoint to.
        :return:
        """
        if self.device.pluginProps['temp-units'] == "F":
            converted = (value - 32) * 5 / 9
            value = round(converted)

        self.publish("{}/thermostat/{}/command/target_t".format(self.getAddress(), self.getChannel()), str(value))

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
        is_valid = True
        # The Shelly  needs to ensure the user has selected a Broker device, supplied the address, and supplied the message type.
        # If the user has indicated that announcement messages are separate, then they need to supply that message type as well.

        # Validate the broker
        broker_id = valuesDict.get('broker-id', None)
        if not broker_id.strip():
            is_valid = False
            errors['broker-id'] = u"You must select the broker to which the Shelly is connected to."

        # Validate the address
        address = valuesDict.get('address', None)
        if not address.strip():
            is_valid = False
            errors['address'] = u"You must enter the MQTT topic root for the Shelly."

        # Validate the message type
        message_type = valuesDict.get('message-type', None)
        if not message_type.strip():
            is_valid = False
            errors['message-type'] = u"You must enter the message type that this Shelly will be associated with."

        # Validate the announcement message type
        has_same_announce_message_type = valuesDict.get('announce-message-type-same-as-message-type', True)
        if not has_same_announce_message_type:  # We would expect a supplied message type for announcement messages
            announce_message_type = valuesDict.get('announce-message-type', None)
            if not announce_message_type.strip():
                is_valid = False
                errors['announce-message-type'] = u"You must supply the message type that will be associated with the announce messages."

        return is_valid, valuesDict, errors

    def get_schedule_profiles(self):
        """
        Format the last known schedule profile names.
        """
        names = {
            1: None,
            2: None,
            3: None,
            4: None,
            5: None
        }

        for index, name in enumerate(self.schedule_profile_names):
            names[index + 1] = name

        return names
