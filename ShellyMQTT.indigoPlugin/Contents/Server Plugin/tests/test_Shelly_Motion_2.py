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
from Devices.Sensors.Shelly_Motion_2 import Shelly_Motion_2


class Test_Shelly_Motion(unittest.TestCase):

    def setUp(self):
        indigo.__init__()

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Motion_2(self.device)

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-motion-2-test"

        self.device.updateStateOnServer("vibration", "")
        self.device.updateStateOnServer("lux", "")
        self.device.updateStateOnServer("active", "")
        self.device.updateStateOnServer("onOffState", "")
        self.device.updateStateOnServer("batteryLevel", 0)
        self.device.updateStateOnServer("voltage", 0)

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/announce",
            "shellies/shelly-motion-2-test/online",
            "shellies/shelly-motion-2-test/info"
        ]
        self.assertListEqual(subscriptions, self.shelly.getSubscriptions())

    def test_updateStateImage_on_motion(self):
        self.device.states['onOffState'] = True
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.MotionSensorTripped, self.device.image)

    def test_updateStateImage_on_inactivity(self):
        self.device.states['onOffState'] = False
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.MotionSensor, self.device.image)

    def test_handleMessage_online_true(self):
        self.device.states['online'] = False
        self.shelly.handleMessage("shellies/shelly-motion-2-test/online", "true")
        self.assertTrue(self.device.states['online'])

    def test_handleMessage_online_false(self):
        self.device.states['online'] = True
        self.shelly.handleMessage("shellies/shelly-motion-2-test/online", "false")
        self.assertFalse(self.device.states['online'])

    def test_handleMessage_motion_detected(self):
        self.device.states['onOffState'] = False
        self.shelly.handleMessage("shellies/shelly-motion-2-test/info", '{"sensor": {"motion": true, "is_valid": true}}')
        self.assertTrue(self.device.states['onOffState'])

    def test_handleMessage_motion_undetected(self):
        self.device.states['onOffState'] = True
        self.shelly.handleMessage("shellies/shelly-motion-2-test/info", '{"sensor": {"motion": false, "is_valid": true}}')
        self.assertFalse(self.device.states['onOffState'])

    def test_handleMessage_vibration_true(self):
        self.device.states['vibration'] = False
        self.shelly.handleMessage("shellies/shelly-motion-2-test/info", '{"sensor": {"vibration": true, "is_valid": true}}')
        self.assertTrue(self.device.states['vibration'])

    def test_handleMessage_vibration_false(self):
        self.device.states['vibration'] = True
        self.shelly.handleMessage("shellies/shelly-motion-2-test/info", '{"sensor": {"vibration": false, "is_valid": true}}')
        self.assertFalse(self.device.states['vibration'])

    def test_handleMessage_lux_valid(self):
        self.shelly.handleMessage("shellies/shelly-motion-2-test/info", '{"lux": {"value": 88, "is_valid": true}}')
        self.assertEqual(88, self.device.states['lux'])

    def test_handleMessage_battery(self):
        self.shelly.handleMessage("shellies/shelly-motion-2-test/info", '{"bat": {"value": 68, "voltage": 3.112}}')
        self.assertEqual(68, self.device.states['batteryLevel'])
        self.assertEqual(3.112, self.device.states['voltage'])

    def test_handleMessage_invalid_json(self):
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-motion-2-test/info", '{"bat": 6]'))

