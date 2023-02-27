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
from Devices.Addons.Shelly_Addon_Detached_Switch import Shelly_Addon_Detached_Switch
from Devices.Relays.Shelly_1 import Shelly_1


class Test_Shelly_Addon_Detached_Switch(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.host_device = IndigoDevice(id=111111, name="Host Device")
        self.host_shelly = Shelly_1(self.host_device)

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Addon_Detached_Switch(self.device)

        indigo.activePlugin.shellyDevices[self.host_shelly.device.id] = self.host_shelly
        indigo.activePlugin.shellyDevices[self.shelly.device.id] = self.shelly

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.host_device.pluginProps['address'] = "shellies/shelly-addon-test"

        self.device.pluginProps['host-id'] = "111111"
        self.device.pluginProps['invert'] = False
        self.device.states['onOffState'] = False

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/shelly-addon-test/online",
            "shellies/shelly-addon-test/input/0"
        ]

        self.assertListEqual(subscriptions, self.shelly.getSubscriptions())

    def test_isAddon(self):
        self.assertTrue(self.shelly.isAddon())

    def test_updateStateImage_on(self):
        self.device.states['onOffState'] = True
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOn, self.device.image)

    def test_updateStateImage_off(self):
        self.device.states['onOffState'] = False
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOff, self.device.image)

    def test_handleMessage_input_on(self):
        self.shelly.handleMessage("shellies/shelly-addon-test/input/0", "1")
        self.assertTrue(self.shelly.device.states['onOffState'])

    def test_handleMessage_input_off(self):
        self.shelly.handleMessage("shellies/shelly-addon-test/input/0", "0")
        self.assertFalse(self.shelly.device.states['onOffState'])

    def test_handleMessage_input_on_invert(self):
        self.shelly.device.pluginProps['invert'] = True
        self.shelly.handleMessage("shellies/shelly-addon-test/input/0", "1")
        self.assertFalse(self.shelly.device.states['onOffState'])

    def test_handleMessage_input_off_invert(self):
        self.shelly.device.pluginProps['invert'] = True
        self.shelly.handleMessage("shellies/shelly-addon-test/input/0", "0")
        self.assertTrue(self.shelly.device.states['onOffState'])

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

    def test_validateConfigUI(self):
        values = {
            "host-id": "12345"
        }

        isValid, valuesDict, errors = Shelly_Addon_Detached_Switch.validateConfigUI(values, None, None)
        self.assertTrue(isValid)

    def test_validateConfigUI_invalid(self):
        values = {
            "host-id": ""
        }

        isValid, valuesDict, errors = Shelly_Addon_Detached_Switch.validateConfigUI(values, None, None)
        self.assertFalse(isValid)
        self.assertTrue("host-id" in errors)
