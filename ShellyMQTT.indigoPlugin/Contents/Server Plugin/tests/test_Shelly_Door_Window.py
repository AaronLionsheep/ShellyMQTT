# coding=utf-8
import unittest
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.IndigoServer import Indigo

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Sensors.Shelly_Door_Window import Shelly_Door_Window


class Test_Shelly_Door_Window(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Door_Window(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-dw-test"
        self.device.pluginProps['useCase'] = "door"

        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)
        self.device.updateStateOnServer("temperature", 0)
        self.device.updateStateOnServer("status", False)
        self.device.updateStateOnServer("vibration", False)
        self.device.updateStateOnServer("lux", 0)
        self.device.updateStateOnServer("tilt", 0)
        self.device.updateStateOnServer("batteryLevel", 0)

    def test_getSubscriptions_no_address(self):
        """Test getting subscriptions with no address defined."""
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        """Test getting subscriptions with a defined address."""
        topics = [
            "shellies/announce",
            "shellies/shelly-dw-test/online",
            "shellies/shelly-dw-test/sensor/state",
            "shellies/shelly-dw-test/sensor/lux",
            "shellies/shelly-dw-test/sensor/tilt",
            "shellies/shelly-dw-test/sensor/vibration",
            "shellies/shelly-dw-test/sensor/battery"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_online_true(self):
        self.shelly.device.states['online'] = False
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-dw-test/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-dw-test/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    def test_handleMessage_state_open(self):
        self.shelly.device.states['status'] = "closed"
        self.shelly.handleMessage("shellies/shelly-dw-test/sensor/state", "open")
        self.assertEqual("open", self.shelly.device.states['status'])

    def test_handleMessage_state_closed(self):
        self.shelly.device.states['status'] = "open"
        self.shelly.handleMessage("shellies/shelly-dw-test/sensor/state", "closed")
        self.assertEqual("closed", self.shelly.device.states['status'])

    def test_handleMessage_lux(self):
        self.shelly.handleMessage("shellies/shelly-dw-test/sensor/lux", "55")
        self.assertEqual("55", self.shelly.device.states['lux'])

    def test_handleMessage_tilt(self):
        self.shelly.handleMessage("shellies/shelly-dw-test/sensor/tilt", "60")
        self.assertEqual("60", self.shelly.device.states['tilt'])
        self.assertEqual("60°", self.shelly.device.states_meta['tilt']['uiValue'])

    def test_handleMessage_vibration(self):
        self.assertFalse(self.shelly.device.states['vibration'])

        self.shelly.handleMessage("shellies/shelly-dw-test/sensor/vibration", "1")
        self.assertTrue(self.shelly.device.states['vibration'])

        self.shelly.handleMessage("shellies/shelly-dw-test/sensor/vibration", "0")
        self.assertFalse(self.shelly.device.states['vibration'])

    def test_handleMessage_battery(self):
        self.shelly.handleMessage("shellies/shelly-dw-test/sensor/battery", "94")
        self.assertEqual("94", self.shelly.device.states['batteryLevel'])

    def test_update_state_image_door_open(self):
        self.device.pluginProps['useCase'] = "door"
        self.shelly.device.states['status'] = "open"
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.DoorSensorOpened, self.shelly.device.image)

    def test_update_state_image_door_close(self):
        self.device.pluginProps['useCase'] = "door"
        self.shelly.device.states['status'] = "closed"
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.DoorSensorClosed, self.shelly.device.image)

    def test_update_state_image_window_open(self):
        self.device.pluginProps['useCase'] = "window"
        self.shelly.device.states['status'] = "open"
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.WindowSensorOpened, self.shelly.device.image)

    def test_update_state_image_window_close(self):
        self.device.pluginProps['useCase'] = "window"
        self.shelly.device.states['status'] = "closed"
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.WindowSensorClosed, self.shelly.device.image)
