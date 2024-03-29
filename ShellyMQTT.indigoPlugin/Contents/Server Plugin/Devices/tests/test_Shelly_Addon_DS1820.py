# coding=utf-8
import unittest
from unittest.mock import patch
import sys
import logging

from Devices.tests.mocking.IndigoDevice import IndigoDevice
from Devices.tests.mocking.IndigoServer import Indigo
from Devices.tests.mocking.IndigoAction import IndigoAction

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Addons.Shelly_Addon_DS1820 import Shelly_Addon_DS1820
from Devices.Relays.Shelly_1 import Shelly_1


class Test_Shelly_Addon_DS1820(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.host_device = IndigoDevice(id=111111, name="Host Device")
        self.host_shelly = Shelly_1(self.host_device)

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Addon_DS1820(self.device)

        indigo.activePlugin.shellyDevices[self.host_shelly.device.id] = self.host_shelly
        indigo.activePlugin.shellyDevices[self.shelly.device.id] = self.shelly

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.host_device.pluginProps['address'] = "shellies/shelly-addon-test"

        self.device.pluginProps['host-id'] = "111111"
        self.device.pluginProps['probe-number'] = 0
        self.device.pluginProps['temp-units'] = "C->F"
        self.device.pluginProps['temp-offset'] = "2"
        self.device.pluginProps['temp-decimals'] = "1"
        self.device.states['temperature'] = 0

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/shelly-addon-test/online",
            "shellies/shelly-addon-test/ext_temperature/0",
            "shellies/shelly-addon-test/ext_temperatures"
        ]

        self.assertListEqual(subscriptions, self.shelly.getSubscriptions())

    def test_isAddon(self):
        self.assertTrue(self.shelly.isAddon())

    def test_getProbeNumber(self):
        self.assertEqual(0, self.shelly.getProbeNumber())
        self.device.pluginProps['probe-number'] = 1
        self.assertEqual(1, self.shelly.getProbeNumber())

    def test_updateStateImage_on(self):
        self.device.states['online'] = True
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.TemperatureSensorOn, self.device.image)

    def test_updateStateImage_off(self):
        self.device.states['online'] = False
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.TemperatureSensor, self.device.image)

    def test_handleMessage_temperature(self):
        self.shelly.handleMessage("shellies/shelly-addon-test/ext_temperature/0", "50")
        self.assertEqual(124, self.shelly.device.states['temperature'])
        self.assertEqual("124.0 °F", self.shelly.device.states_meta['temperature']['uiValue'])

    def test_handleMessage_temperature_invalid(self):
        self.shelly.handleMessage("shellies/shelly-addon-test/ext_temperature/0", "A")

    def test_handleMessage_temperature_hwid(self):
        self.device.pluginProps['probe-number'] = "2885186e38190456"
        payload = '{"0":{"hwID":"2885186e38190123","tC":20.5}, "1":{"hwID":"2885186e38190456","tC":50}}'
        self.shelly.handleMessage("shellies/shelly-addon-test/ext_temperatures", payload)
        self.assertEqual(124, self.shelly.device.states['temperature'])
        self.assertEqual("124.0 °F", self.shelly.device.states_meta['temperature']['uiValue'])

    def test_handleMessage_online_true(self):
        self.device.states['online'] = False
        self.shelly.handleMessage("shellies/shelly-addon-test/online", "true")
        self.assertTrue(self.device.states['online'])

    def test_handleMessage_online_false(self):
        self.device.states['online'] = True
        self.shelly.handleMessage("shellies/shelly-addon-test/online", "false")
        self.assertFalse(self.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_sendStatusRequestCommand(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-addon-test/command", "update")

    def test_status_field(self):
        self.shelly.handleMessage("shellies/shelly-addon-test/ext_temperature/0", "50")
        self.assertEqual("124.0°F", self.shelly.device.states['status'])

    def test_validateConfigUI(self):
        values = {
            "host-id": "12345",
            "temp-offset": ""
        }

        isValid, valuesDict, errors = Shelly_Addon_DS1820.validateConfigUI(values, None, None)
        self.assertTrue(isValid)

    def test_validateConfigUI_temp_offset(self):
        values = {
            "host-id": "12345",
            "temp-offset": "5"
        }

        isValid, valuesDict, errors = Shelly_Addon_DS1820.validateConfigUI(values, None, None)
        self.assertTrue(isValid)

    def test_validateConfigUI_invalid(self):
        values = {
            "host-id": "",
            "temp-offset": "a"
        }

        isValid, valuesDict, errors = Shelly_Addon_DS1820.validateConfigUI(values, None, None)
        self.assertFalse(isValid)
        self.assertTrue("host-id" in errors)
        self.assertTrue("temp-offset" in errors)
