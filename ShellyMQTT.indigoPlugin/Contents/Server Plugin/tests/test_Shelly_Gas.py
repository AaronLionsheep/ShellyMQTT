# coding=utf-8
import unittest
from mock import patch
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.IndigoServer import Indigo
from mocking.IndigoAction import IndigoAction
from mocking.PluginAction import PluginAction

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Sensors.Shelly_Gas import Shelly_Gas


class Test_Shelly_Button1(unittest.TestCase):

    def setUp(self):
        indigo.__init__()

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Gas(self.device)

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-gas-test"

        self.device.updateStateOnServer("sensor-status", "")
        self.device.updateStateOnServer("gas-detected", "")
        self.device.updateStateOnServer("self-test", "")
        self.device.updateStateOnServer("sensorValue", "")

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/announce",
            "shellies/shelly-gas-test/online",
            "shellies/shelly-gas-test/sensor/operation",
            "shellies/shelly-gas-test/sensor/gas",
            "shellies/shelly-gas-test/sensor/self_test",
            "shellies/shelly-gas-test/sensor/concentration"
        ]
        self.assertListEqual(subscriptions, self.shelly.getSubscriptions())

    def test_updateStateImage_on_mild(self):
        self.device.states['gas-detected'] = "mild"
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorTripped, self.device.image)

    def test_updateStateImage_on_heavy(self):
        self.device.states['gas-detected'] = "heavy"
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorTripped, self.device.image)

    def test_updateStateImage_off(self):
        self.device.states['gas-detected'] = ""
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOn, self.device.image)

    def test_handleMessage_online_true(self):
        self.device.states['online'] = False
        self.shelly.handleMessage("shellies/shelly-gas-test/online", "true")
        self.assertTrue(self.device.states['online'])

    def test_handleMessage_online_false(self):
        self.device.states['online'] = True
        self.shelly.handleMessage("shellies/shelly-gas-test/online", "false")
        self.assertFalse(self.device.states['online'])

    def test_handleMessage_operation(self):
        self.shelly.handleMessage("shellies/shelly-gas-test/sensor/operation", "normal")
        self.assertEqual("normal", self.device.states['sensor-status'])

    def test_handleMessage_gas(self):
        self.shelly.handleMessage("shellies/shelly-gas-test/sensor/gas", "mild")
        self.assertEqual("mild", self.device.states['gas-detected'])

    def test_handleMessage_self_test(self):
        self.shelly.handleMessage("shellies/shelly-gas-test/sensor/self_test", "completed")
        self.assertEqual("completed", self.device.states['self-test'])

    def test_handleMessage_concentration(self):
        self.shelly.handleMessage("shellies/shelly-gas-test/sensor/concentration", "102")
        self.assertEqual(102, self.device.states['sensorValue'])
        self.assertEqual("102 ppm", self.device.states_meta['sensorValue']['uiValue'])

    def test_handleMessage_concentration_string(self):
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-gas-test/sensor/concentration", "102a"))

    @patch('Devices.Shelly.Shelly.publish')
    def test_sendStatusRequestCommand(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-gas-test/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handlePluginAction_self_test(self, publish):
        self_test = PluginAction("gas-self-test")
        self.shelly.handlePluginAction(self_test)
        publish.assert_called_with("shellies/shelly-gas-test/sensor/start_self_test", "start")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handlePluginAction_mute_alarm(self, publish):
        mute = PluginAction("gas-mute-alarm")
        self.shelly.handlePluginAction(mute)
        publish.assert_called_with("shellies/shelly-gas-test/sensor/mute", "mute")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handlePluginAction_unmute_alarm(self, publish):
        unmute = PluginAction("gas-unmute-alarm")
        self.shelly.handlePluginAction(unmute)
        publish.assert_called_with("shellies/shelly-gas-test/sensor/unmute", "unmute")
