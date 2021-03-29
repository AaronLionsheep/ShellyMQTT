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
from Devices.Sensors.Shelly_Uni_Input import Shelly_Uni_Input


class Test_Shelly_Uni_Input(unittest.TestCase):

    def setUp(self):
        indigo.__init__()

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Uni_Input(self.device)

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-uni-input"
        self.device.pluginProps['invert'] = False
        self.device.pluginProps['last-input-event-id'] = -1
        self.device.states['onOffState'] = False
        self.device.states['voltage'] = 0

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/announce",
            "shellies/shelly-uni-input/online",
            "shellies/shelly-uni-input/info",
            "shellies/shelly-uni-input/input/0",
            "shellies/shelly-uni-input/input_event/0",
            "shellies/shelly-uni-input/ext_temperatures",
            "shellies/shelly-uni-input/ext_humidities"
        ]

        self.assertListEqual(subscriptions, self.shelly.getSubscriptions())

    def test_updateStateImage_on(self):
        self.device.states['onOffState'] = True
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOn, self.device.image)

    def test_updateStateImage_off(self):
        self.device.states['onOffState'] = False
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOff, self.device.image)

    def test_handleMessage_input_on(self):
        self.shelly.handleMessage("shellies/shelly-uni-input/input/0", "1")
        self.assertTrue(self.shelly.device.states['onOffState'])

    def test_handleMessage_input_off(self):
        self.shelly.handleMessage("shellies/shelly-uni-input/input/0", "0")
        self.assertFalse(self.shelly.device.states['onOffState'])

    def test_handleMessage_input_on_invert(self):
        self.shelly.device.pluginProps['invert'] = True
        self.shelly.handleMessage("shellies/shelly-uni-input/input/0", "1")
        self.assertFalse(self.shelly.device.states['onOffState'])

    def test_handleMessage_input_off_invert(self):
        self.shelly.device.pluginProps['invert'] = True
        self.shelly.handleMessage("shellies/shelly-uni-input/input/0", "0")
        self.assertTrue(self.shelly.device.states['onOffState'])

    def test_handleMessage_online_true(self):
        self.device.states['online'] = False
        self.shelly.handleMessage("shellies/shelly-uni-input/online", "true")
        self.assertTrue(self.device.states['online'])

    def test_handleMessage_online_false(self):
        self.device.states['online'] = True
        self.shelly.handleMessage("shellies/shelly-uni-input/online", "false")
        self.assertFalse(self.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_sendStatusRequestCommand(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-uni-input/command", "update")

    @patch('Devices.Shelly.Shelly.processInputEvent')
    def test_input_event_is_processed(self, processInputEvent):
        """Test that an input_event message is processed"""
        self.shelly.handleMessage("shellies/shelly-uni-input/input_event/0", '{"event": "S", "event_cnt": 1}')
        processInputEvent.assert_called_with('{"event": "S", "event_cnt": 1}')

    def test_handleMessage_info(self):
        payload = '{"adcs": [{"voltage": 12.13}]}'
        self.shelly.handleMessage("shellies/shelly-uni-input/info", payload)
        self.assertEqual(12.13, self.device.states['voltage'])
