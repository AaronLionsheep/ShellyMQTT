# coding=utf-8
import unittest
from mock import patch
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.IndigoServer import Indigo
from mocking.IndigoAction import IndigoAction

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Sensors.Shelly_Button1 import Shelly_Button1


class Test_Shelly_Addon_Detached_Switch(unittest.TestCase):

    def setUp(self):
        indigo.__init__()

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Button1(self.device)

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-button1-test"
        self.device.pluginProps['last-input-event-id'] = -1
        self.device.states['onOffState'] = False

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/announce",
            "shellies/shelly-button1-test/online",
            "shellies/shelly-button1-test/sensor/battery",
            "shellies/shelly-button1-test/input_event/0"
        ]
        self.assertListEqual(subscriptions, self.shelly.getSubscriptions())

    def test_handleMessage_battery(self):
        self.shelly.handleMessage("shellies/shelly-button1-test/sensor/battery", "98")
        self.assertEqual("98", self.device.states['batteryLevel'])

    @unittest.skip("Removed")
    def test_updateStateImage_on(self):
        self.device.states['onOffState'] = True
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOn, self.device.image)

    @unittest.skip("Removed")
    def test_updateStateImage_off(self):
        self.device.states['onOffState'] = False
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOff, self.device.image)

    def test_handleMessage_online_true(self):
        self.device.states['online'] = False
        self.shelly.handleMessage("shellies/shelly-button1-test/online", "true")
        self.assertTrue(self.device.states['online'])

    def test_handleMessage_online_false(self):
        self.device.states['online'] = True
        self.shelly.handleMessage("shellies/shelly-button1-test/online", "false")
        self.assertFalse(self.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_sendStatusRequestCommand(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-button1-test/command", "update")

    @patch('Devices.Shelly.Shelly.processInputEvent')
    def test_input_event_is_processed(self, processInputEvent):
        """Test that an input_event message is processed"""
        self.shelly.handleMessage("shellies/shelly-button1-test/input_event/0", '{"event": "S", "event_cnt": 1}')
        processInputEvent.assert_called_with('{"event": "S", "event_cnt": 1}')
