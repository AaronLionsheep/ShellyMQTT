# coding=utf-8
import unittest
import sys
import logging

from Devices.tests.mocking.IndigoDevice import IndigoDevice
from Devices.tests.mocking.IndigoServer import Indigo

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Sensors.Shelly_Motion import Shelly_Motion


class Test_Shelly_Motion(unittest.TestCase):

    def setUp(self):
        indigo.__init__()

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Motion(self.device)

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-motion-test"

        self.device.updateStateOnServer("vibration", "")
        self.device.updateStateOnServer("lux", "")
        self.device.updateStateOnServer("active", "")
        self.device.updateStateOnServer("onOffState", "")
        self.device.updateStateOnServer("batteryLevel", 0)

    def test_getSubscriptions(self):
        subscriptions = [
            "shellies/announce",
            "shellies/shelly-motion-test/online",
            "shellies/shelly-motion-test/status"
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
        self.shelly.handleMessage("shellies/shelly-motion-test/online", "true")
        self.assertTrue(self.device.states['online'])

    def test_handleMessage_online_false(self):
        self.device.states['online'] = True
        self.shelly.handleMessage("shellies/shelly-motion-test/online", "false")
        self.assertFalse(self.device.states['online'])

    def test_handleMessage_motion_detected(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"motion": true}')
        self.assertTrue(self.device.states['onOffState'])

    def test_handleMessage_motion_undetected(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"motion": false}')
        self.assertFalse(self.device.states['onOffState'])

    def test_handleMessage_active_true(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"active": true}')
        self.assertTrue(self.device.states['active'])

    def test_handleMessage_active_false(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"active": false}')
        self.assertFalse(self.device.states['active'])

    def test_handleMessage_vibration_true(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"vibration": true}')
        self.assertTrue(self.device.states['vibration'])

    def test_handleMessage_vibration_false(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"vibration": false}')
        self.assertFalse(self.device.states['vibration'])

    def test_handleMessage_lux(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"lux": 88}')
        self.assertEqual(88, self.device.states['lux'])

    def test_handleMessage_battery_level(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"bat": 68}')
        self.assertEqual(68, self.device.states['batteryLevel'])

    def test_handleMessage_invalid_json(self):
        self.shelly.handleMessage("shellies/shelly-motion-test/status", '{"bat": 6]')

