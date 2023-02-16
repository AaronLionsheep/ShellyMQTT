# coding=utf-8
import unittest
from mock import patch
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.IndigoServer import Indigo
from mocking.ThermostatAction import ThermostatAction
from mocking.PluginAction import PluginAction

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Shelly_TRV import Shelly_TRV


class Test_Shelly_TRV(unittest.TestCase):

    def setUp(self):
        indigo.__init__()

        self.device = IndigoDevice(id=123456, name="New Device")
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/trv"

        self.device.updateStateOnServer("batteryLevel", None)
        self.device.updateStateOnServer("voltage", None)
        self.device.updateStateOnServer("charging", None)
        self.device.updateStateOnServer("calibrated", None)
        self.device.updateStateOnServer("setpointHeat", None)
        self.device.updateStateOnServer("temperatureInput1", None)
        self.device.updateStateOnServer("boost-minutes", None)
        self.device.updateStateOnServer("valve-position", None)
        self.device.updateStateOnServer("hvacOperationMode", None)
        self.device.updateStateOnServer("schedule-profile", None)

        self.shelly = Shelly_TRV(self.device)

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/announce",
            "shellies/trv/online",
            "shellies/trv/info"
        ]
        self.assertListEqual(subscriptions, self.shelly.getSubscriptions())

    def test_handleMessage_online_true(self):
        self.device.states['online'] = False
        self.shelly.handleMessage("shellies/trv/online", "true")
        self.assertTrue(self.device.states['online'])

    def test_handleMessage_online_false(self):
        self.device.states['online'] = True
        self.shelly.handleMessage("shellies/trv/online", "false")
        self.assertFalse(self.device.states['online'])

    def test_handleMessage_battery(self):
        self.shelly.handleMessage("shellies/trv/info", '{"bat": {"value": 68, "voltage": 3.112}}')
        self.assertEqual(68, self.device.states['batteryLevel'])
        self.assertEqual(3.112, self.device.states['voltage'])
        self.assertEqual("3.112V", self.device.states_meta['voltage']['uiValue'])

    def test_handleMessage_battery_invalid_payload(self):
        self.shelly.handleMessage("shellies/trv/info", '{"bat": {}}')

    def test_handleMessage_charger_false(self):
        self.shelly.handleMessage("shellies/trv/info", '{"charger": false}')
        self.assertEqual(False, self.device.states['charging'])

    def test_handleMessage_charger_true(self):
        self.shelly.handleMessage("shellies/trv/info", '{"charger": true}')
        self.assertEqual(True, self.device.states['charging'])

    def test_handleMessage_calibrated_false(self):
        self.shelly.handleMessage("shellies/trv/info", '{"calibrated": false}')
        self.assertEqual(False, self.device.states['calibrated'])

    def test_handleMessage_calibrated_true(self):
        self.shelly.handleMessage("shellies/trv/info", '{"calibrated": true}')
        self.assertEqual(True, self.device.states['calibrated'])

    def test_handleMessage_updates_target_temperature_c(self):
        self.device.pluginProps['temp-units'] = "C"
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"target_t": {"value": 31.0}}]}')
        self.assertEqual(31.0, self.device.states['setpointHeat'])

    def test_handleMessage_updates_target_temperature_f(self):
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"target_t": {"value": 24.44}}]}')
        self.assertEqual(76.0, self.device.states['setpointHeat'])

    def test_handleMessage_updates_sensor_temperature_c(self):
        self.device.pluginProps['temp-units'] = "C"
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"tmp": {"value": 31.0}}]}')
        self.assertEqual(31.0, self.device.states['temperatureInput1'])

    def test_handleMessage_updates_sensor_temperature_f(self):
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"tmp": {"value": 24.44}}]}')
        self.assertEqual(76.0, self.device.states['temperatureInput1'])

    def test_handleMessage_updates_boost_minutes(self):
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"boost_minutes": 2}]}')
        self.assertEqual(2, self.device.states['boost-minutes'])

    def test_handleMessage_updates_position(self):
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"pos": 23}]}')
        self.assertEqual(23, self.device.states['valve-position'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_SetHeatSetpoint_c(self, publish):
        self.device.pluginProps['temp-units'] = "C"
        self.shelly.handleAction(ThermostatAction(indigo.kThermostatAction.SetHeatSetpoint, 26))
        publish.assert_called_with("shellies/trv/thermostat/0/command/target_t", "26")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_SetHeatSetpoint_f(self, publish):
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.handleAction(ThermostatAction(indigo.kThermostatAction.SetHeatSetpoint, 76))
        publish.assert_called_with("shellies/trv/thermostat/0/command/target_t", "24")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_DecreaseHeatSetpoint_c(self, publish):
        self.device.states['setpointHeat'] = 25
        self.device.pluginProps['temp-units'] = "C"
        self.shelly.handleAction(ThermostatAction(indigo.kThermostatAction.DecreaseHeatSetpoint, 1))
        publish.assert_called_with("shellies/trv/thermostat/0/command/target_t", "24")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_DecreaseHeatSetpoint_f(self, publish):
        self.device.states['setpointHeat'] = 75
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.handleAction(ThermostatAction(indigo.kThermostatAction.DecreaseHeatSetpoint, 1))
        publish.assert_called_with("shellies/trv/thermostat/0/command/target_t", "23")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_IncreaseHeatSetpoint_c(self, publish):
        self.device.states['setpointHeat'] = 24
        self.device.pluginProps['temp-units'] = "C"
        self.shelly.handleAction(ThermostatAction(indigo.kThermostatAction.IncreaseHeatSetpoint, 1))
        publish.assert_called_with("shellies/trv/thermostat/0/command/target_t", "25")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_IncreaseHeatSetpoint_f(self, publish):
        self.device.states['setpointHeat'] = 75
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.handleAction(ThermostatAction(indigo.kThermostatAction.IncreaseHeatSetpoint, 1))
        publish.assert_called_with("shellies/trv/thermostat/0/command/target_t", "24")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handlePluginAction_start_boost(self, publish):
        start_boost = PluginAction("trv-start-boost")
        start_boost.props = {"duration": "10"}
        self.shelly.handlePluginAction(start_boost)
        publish.assert_called_with("shellies/trv/thermostat/0/command/boost_minutes", "10")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handlePluginAction_stop_boost(self, publish):
        stop_boost = PluginAction("trv-stop-boost")
        self.shelly.handlePluginAction(stop_boost)
        publish.assert_called_with("shellies/trv/thermostat/0/command/boost_minutes", "0")

    def test_trv_is_in_heat_operation_mode(self):
        self.assertEqual(indigo.kHvacMode.Heat, self.device.states['hvacOperationMode'])

    def test_trv_sets_schedule_profile(self):
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"schedule": true, "schedule_profile": 1}]}')
        self.assertEqual(1, self.device.states['schedule-profile'])

    def test_trv_clears_schedule_profile(self):
        self.device.states['schedule-profile'] = 1
        self.shelly.handleMessage("shellies/trv/info", '{"thermostats": [{"schedule": false, "schedule_profile": 1}]}')
        self.assertEqual(None, self.device.states['schedule-profile'])
