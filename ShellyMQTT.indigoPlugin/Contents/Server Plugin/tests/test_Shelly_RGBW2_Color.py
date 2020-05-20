# coding=utf-8
import unittest
from mock import patch
import sys
import logging
import json

from mocking.IndigoDevice import IndigoDevice
from mocking.IndigoServer import Indigo
from mocking.IndigoAction import IndigoAction

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.RGBW2.Shelly_RGBW2_Color import Shelly_RGBW2_Color


class Test_Shelly_RGBW2_Color(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_RGBW2_Color(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-rgbw2-color-test"
        self.device.pluginProps['int-temp-units'] = "C->F"

        self.device.updateStateOnServer("overpower", False)
        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)
        self.device.updateStateOnServer("curEnergyLevel", 0)
        self.device.updateStateOnServer("brightnessLevel", 0)
        self.device.updateStateOnServer("whiteLevel", 100)
        self.device.updateStateOnServer("whiteTemperature", 2700)
        self.device.updateStateOnServer("redLevel", 0)
        self.device.updateStateOnServer("greenLevel", 0)
        self.device.updateStateOnServer("blueLevel", 0)

    def test_getSubscriptions_no_address(self):
        """Test getting subscriptions with no address defined."""
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        """Test getting subscriptions with a defined address."""
        topics = [
            "shellies/announce",
            "shellies/shelly-rgbw2-color-test/online",
            "shellies/shelly-rgbw2-color-test/color/0/status"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_status_invalid(self):
        """Test getting invalid status data."""
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/color/0/status", '{"ison": true, "mo'))

    def test_handleMessage_invalid_mode(self):
        """Test getting a message for the wrong mode."""
        self.assertFalse(self.shelly.isOn())
        payload = {
            "ison": True,
            "mode": "white",
            "brightness": 100,
            "power": 25,
            "overpower": False
        }
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/color/0/status", json.dumps(payload))
        self.assertFalse(self.shelly.isOn())

    def test_handleMessage_light_on(self):
        """Test getting a light on message."""
        self.assertTrue(self.shelly.isOff())
        payload = {
            "ison": True,
            "mode": "color",
            "red": 51,
            "green": 52,
            "blue": 53,
            "brightness": 100,
            "gain": 100,
            "power": 25,
            "overpower": False
        }
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/color/0/status", json.dumps(payload))
        self.assertTrue(self.shelly.isOn())
        self.assertFalse(self.shelly.device.states['overpower'])
        self.assertEqual(51, self.shelly.device.states['redLevel'])
        self.assertEqual(52, self.shelly.device.states['greenLevel'])
        self.assertEqual(53, self.shelly.device.states['blueLevel'])

    def test_handleMessage_light_off(self):
        """Test getting a light off message."""
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        payload = {
            "ison": False,
            "mode": "color",
            "red": 51,
            "green": 52,
            "blue": 53,
            "brightness": 0,
            "gain": 100,
            "power": 25,
            "overpower": False
        }
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/color/0/status", json.dumps(payload))
        self.assertTrue(self.shelly.isOff())
        self.assertFalse(self.shelly.device.states['overpower'])

    def test_handleMessage_overpower(self):
        """Test getting a relay overpower message."""
        self.assertFalse(self.shelly.device.states['overpower'])
        payload = {
            "ison": False,
            "mode": "color",
            "red": 50,
            "green": 50,
            "blue": 50,
            "brightness": 100,
            "gain": 100,
            "power": 25,
            "overpower": True
        }
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/color/0/status", json.dumps(payload))
        self.assertTrue(self.shelly.device.states['overpower'])

    def test_handleMessage_power(self):
        payload = {
            "ison": False,
            "mode": "color",
            "red": 51,
            "green": 52,
            "blue": 53,
            "brightness": 100,
            "gain": 100,
            "power": 0,
            "overpower": False
        }
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/color/0/status", json.dumps(payload))
        self.assertEqual(0, self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("0 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

        payload = {
            "ison": True,
            "mode": "color",
            "red": 51,
            "green": 52,
            "blue": 53,
            "brightness": 100,
            "gain": 100,
            "power": 101.123,
            "overpower": False
        }
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/color/0/status", json.dumps(payload))
        self.assertEqual(101.123, self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("101.123 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

    def test_handleMessage_announce(self):
        announcement = '{"id": "shelly-rgbw2-color-test", "mac": "aa:bb:cc:ee", "ip": "192.168.1.101", "fw_ver": "0.1.0", "new_fw": false}'
        self.shelly.handleMessage("shellies/announce", announcement)

        self.assertEqual("aa:bb:cc:ee", self.shelly.device.states['mac-address'])
        self.assertEqual("192.168.1.101", self.shelly.getIpAddress())
        self.assertEqual("0.1.0", self.shelly.getFirmware())
        self.assertFalse(self.shelly.updateAvailable())

    def test_handleMessage_online_true(self):
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-rgbw2-color-test/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        turnOn = IndigoAction(indigo.kDeviceAction.TurnOn)
        self.shelly.handleAction(turnOn)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 100}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        turnOff = IndigoAction(indigo.kDeviceAction.TurnOff)
        self.shelly.handleAction(turnOff)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "off", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 0}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_status_request(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_off_to_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 100}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_on_to_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "off", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 0}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_setBrightness(self, publish):
        self.assertEqual(0, self.shelly.device.states['brightnessLevel'])
        setBrightness = IndigoAction(indigo.kDeviceAction.SetBrightness, actionValue=50)

        self.shelly.handleAction(setBrightness)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(50, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 50}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_brightenBy(self, publish):
        self.assertEqual(0, self.shelly.device.states['brightnessLevel'])
        brightenBy = IndigoAction(indigo.kDeviceAction.BrightenBy, actionValue=25)

        self.shelly.handleAction(brightenBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(25, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 25}))

        self.shelly.handleAction(brightenBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(50, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 50}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_brightenBy_more_than_100(self, publish):
        self.shelly.device.updateStateOnServer('brightnessLevel', 90)
        brightenBy = IndigoAction(indigo.kDeviceAction.BrightenBy, actionValue=25)

        self.shelly.handleAction(brightenBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(100, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 100}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_dimBy(self, publish):
        self.shelly.device.updateStateOnServer('brightnessLevel', 100)
        dimBy = IndigoAction(indigo.kDeviceAction.DimBy, actionValue=25)

        self.shelly.handleAction(dimBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(75, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 75}))

        self.shelly.handleAction(dimBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(50, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "on", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 50}))

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_dimBy_less_than_0(self, publish):
        self.shelly.device.updateStateOnServer('brightnessLevel', 10)
        dimBy = IndigoAction(indigo.kDeviceAction.DimBy, actionValue=25)

        self.shelly.handleAction(dimBy)
        self.assertTrue(self.shelly.isOff())
        self.assertEqual(0, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-rgbw2-color-test/color/0/set", json.dumps({"turn": "off", "mode": "color", "white": 100, "red": 0, "green": 0, "blue": 0, "gain": 0}))

    def test_apply_brightness_off(self):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.shelly.applyBrightness(0)
        self.assertTrue(self.shelly.isOff())
        self.assertEqual(0, self.shelly.device.brightness)

    def test_apply_brightness_on(self):
        self.assertTrue(self.shelly.isOff())

        self.shelly.applyBrightness(50)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(50, self.shelly.device.brightness)

        self.shelly.applyBrightness(100)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(100, self.shelly.device.brightness)

    def test_update_state_image_on(self):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(indigo.kStateImageSel.PowerOn, self.shelly.device.image)

    def test_update_state_image_off(self):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        self.assertEqual(indigo.kStateImageSel.PowerOff, self.shelly.device.image)