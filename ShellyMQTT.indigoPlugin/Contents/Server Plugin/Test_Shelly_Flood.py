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
from Devices.Sensors.Shelly_Flood import Shelly_Flood


class Test_Shelly_Flood(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Flood(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-flood-test"
        self.device.pluginProps['temp-units'] = "C->F"
        self.device.pluginProps['temp-offset'] = "2"
        self.device.pluginProps['temp-decimals'] = "1"

        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)
        self.device.updateStateOnServer("temperature", 0)
        self.device.updateStateOnServer("onOffState", False)
        self.device.updateStateOnServer("batteryLevel", False)

    def test_getSubscriptions_no_address(self):
        """Test getting subscriptions with no address defined."""
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        """Test getting subscriptions with a defined address."""
        topics = [
            "shellies/announce",
            "shellies/shelly-flood-test/online",
            "shellies/shelly-flood-test/sensor/temperature",
            "shellies/shelly-flood-test/sensor/flood",
            "shellies/shelly-flood-test/sensor/battery"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_online_true(self):
        self.shelly.device.states['online'] = False
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-flood-test/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-flood-test/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    def test_handleMessage_temperature(self):
        self.shelly.handleMessage("shellies/shelly-flood-test/sensor/temperature", "43")
        self.assertAlmostEqual(111.4, self.shelly.device.states['temperature'])
        self.assertEqual("111.4 °F", self.shelly.device.states_meta['temperature']['uiValue'])

    def test_handleMessage_flood_dry(self):
        self.shelly.handleMessage("shellies/shelly-flood-test/sensor/flood", "false")
        self.assertFalse(self.shelly.device.states['onOffState'])
        self.assertEqual("dry", self.shelly.device.states_meta['onOffState']['uiValue'])

    def test_handleMessage_flood_wet(self):
        self.shelly.handleMessage("shellies/shelly-flood-test/sensor/flood", "true")
        self.assertTrue(self.shelly.device.states['onOffState'])
        self.assertEqual("wet", self.shelly.device.states_meta['onOffState']['uiValue'])

    def test_handleMessage_battery(self):
        self.shelly.handleMessage("shellies/shelly-flood-test/sensor/battery", "94")
        self.assertEqual("94", self.shelly.device.states['batteryLevel'])

    def test_update_state_image_on(self):
        self.shelly.device.states['onOffState'] = True
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorTripped, self.shelly.device.image)

    def test_update_state_image_off(self):
        self.shelly.device.states['onOffState'] = False
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.SensorOff, self.shelly.device.image)
