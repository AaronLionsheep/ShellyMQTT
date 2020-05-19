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
from Devices.Bulbs.Shelly_Bulb_Vintage import Shelly_Bulb_Vintage


class Test_Shelly_Bulb_Vintage(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Bulb_Vintage(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-bulb-vintage-test"

        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)
        self.device.updateStateOnServer("curEnergyLevel", 0)
        self.device.updateStateOnServer("brightnessLevel", 0)
        self.device.updateStateOnServer("overload", False)

    def test_getSubscriptions_no_address(self):
        """Test getting subscriptions with no address defined."""
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        """Test getting subscriptions with a defined address."""
        topics = [
            "shellies/announce",
            "shellies/shelly-bulb-vintage-test/online",
            "shellies/shelly-bulb-vintage-test/light/0/status",
            "shellies/shelly-bulb-vintage-test/light/0/power",
            "shellies/shelly-bulb-vintage-test/light/0/energy"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_status_invalid(self):
        """Test getting invalid status data."""
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/light/0/status", '{"ison": true, "mo'))

    def test_handleMessage_light_on(self):
        """Test getting a light on message."""
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/light/0/status", '{"ison": true, "brightness": 100}')
        self.assertTrue(self.shelly.isOn())
        self.assertFalse(self.shelly.device.states['overload'])

    def test_handleMessage_light_off(self):
        """Test getting a light off message."""
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/light/0/status", '{"ison": false, "brightness": 100}')
        self.assertTrue(self.shelly.isOff())
        self.assertFalse(self.shelly.device.states['overload'])

    def test_handleMessage_power(self):
        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/relay/0/power", "0")
        self.assertEqual("0", self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("0 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/relay/0/power", "101.123")
        self.assertEqual("101.123", self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("101.123 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

    def test_handleMessage_energy(self):
        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/relay/0/energy", "0")
        self.assertAlmostEqual(0.0000, self.shelly.device.states['accumEnergyTotal'], 4)

        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/relay/0/energy", "50")
        self.assertAlmostEqual(0.0008, self.shelly.device.states['accumEnergyTotal'], 4)

    def test_handleMessage_announce(self):
        announcement = '{"id": "shelly-bulb-vintage-test", "mac": "aa:bb:cc:ee", "ip": "192.168.1.101", "fw_ver": "0.1.0", "new_fw": false}'
        self.shelly.handleMessage("shellies/announce", announcement)

        self.assertEqual("aa:bb:cc:ee", self.shelly.device.states['mac-address'])
        self.assertEqual("192.168.1.101", self.shelly.getIpAddress())
        self.assertEqual("0.1.0", self.shelly.getFirmware())
        self.assertFalse(self.shelly.updateAvailable())

    def test_handleMessage_online_true(self):
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-bulb-vintage-test/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        turnOn = IndigoAction(indigo.kDeviceAction.TurnOn)
        self.shelly.handleAction(turnOn)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 100}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        turnOff = IndigoAction(indigo.kDeviceAction.TurnOff)
        self.shelly.handleAction(turnOff)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "off", "brightness": 0}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_status_request(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_off_to_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 100}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_on_to_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "off", "brightness": 0}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_reset_energy(self, publish):
        self.shelly.updateEnergy(30)
        self.assertAlmostEqual(0.0005, self.shelly.device.states['accumEnergyTotal'], 4)
        resetEnergy = IndigoAction(indigo.kUniversalAction.EnergyReset)
        self.shelly.handleAction(resetEnergy)
        self.assertAlmostEqual(0.0000, self.shelly.device.states['accumEnergyTotal'], 4)

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_update_energy(self, publish):
        updateEnergy = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(updateEnergy)
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_setBrightness(self, publish):
        self.assertEqual(0, self.shelly.device.states['brightnessLevel'])
        setBrightness = IndigoAction(indigo.kDeviceAction.SetBrightness, actionValue=50)

        self.shelly.handleAction(setBrightness)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(50, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 50}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_brightenBy(self, publish):
        self.assertEqual(0, self.shelly.device.states['brightnessLevel'])
        brightenBy = IndigoAction(indigo.kDeviceAction.BrightenBy, actionValue=25)

        self.shelly.handleAction(brightenBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(25, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 25}')

        self.shelly.handleAction(brightenBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(50, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 50}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_brightenBy_more_than_100(self, publish):
        self.shelly.device.updateStateOnServer('brightnessLevel', 90)
        brightenBy = IndigoAction(indigo.kDeviceAction.BrightenBy, actionValue=25)

        self.shelly.handleAction(brightenBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(100, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 100}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_dimBy(self, publish):
        self.shelly.device.updateStateOnServer('brightnessLevel', 100)
        dimBy = IndigoAction(indigo.kDeviceAction.DimBy, actionValue=25)

        self.shelly.handleAction(dimBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(75, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 75}')

        self.shelly.handleAction(dimBy)
        self.assertTrue(self.shelly.isOn())
        self.assertEqual(50, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "on", "brightness": 50}')

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_dimBy_less_than_0(self, publish):
        self.shelly.device.updateStateOnServer('brightnessLevel', 10)
        dimBy = IndigoAction(indigo.kDeviceAction.DimBy, actionValue=25)

        self.shelly.handleAction(dimBy)
        self.assertTrue(self.shelly.isOff())
        self.assertEqual(0, self.shelly.device.states['brightnessLevel'])
        publish.assert_called_with("shellies/shelly-bulb-vintage-test/light/0/set", '{"turn": "off", "brightness": 0}')

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
        self.assertEqual(indigo.kStateImageSel.DimmerOn, self.shelly.device.image)

    def test_update_state_image_off(self):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        self.assertEqual(indigo.kStateImageSel.DimmerOff, self.shelly.device.image)
