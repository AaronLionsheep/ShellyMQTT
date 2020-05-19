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
from Devices.Relays.Shelly_4_Pro import Shelly_4_Pro


class Test_Shelly_4_Pro(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_4_Pro(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly4pro-test"
        self.device.pluginProps['int-temp-units'] = "C->F"
        self.device.pluginProps['channel'] = 0

        self.device.updateStateOnServer("sw-input", False)
        self.device.updateStateOnServer("overpower", False)
        self.device.updateStateOnServer("overtemperature", False)
        self.device.updateStateOnServer("longpush", False)
        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)
        self.device.updateStateOnServer("curEnergyLevel", 0)

    def test_getSubscriptions_no_address(self):
        """Test getting subscriptions with no address defined."""
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions_channel_1(self):
        """Test getting subscriptions with a defined address on channel 1."""
        topics = [
            "shellies/announce",
            "shellies/shelly4pro-test/online",
            "shellies/shelly4pro-test/relay/0",
            "shellies/shelly4pro-test/input/0",
            "shellies/shelly4pro-test/relay/0/power",
            "shellies/shelly4pro-test/relay/0/energy"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_getSubscriptions_channel_2(self):
        """Test getting subscriptions with a defined address on channel 2."""
        self.device.pluginProps['channel'] = 1
        topics = [
            "shellies/announce",
            "shellies/shelly4pro-test/online",
            "shellies/shelly4pro-test/relay/1",
            "shellies/shelly4pro-test/input/1",
            "shellies/shelly4pro-test/relay/1/power",
            "shellies/shelly4pro-test/relay/1/energy"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_getSubscriptions_channel_3(self):
        """Test getting subscriptions with a defined address on channel 2."""
        self.device.pluginProps['channel'] = 2
        topics = [
            "shellies/announce",
            "shellies/shelly4pro-test/online",
            "shellies/shelly4pro-test/relay/2",
            "shellies/shelly4pro-test/input/2",
            "shellies/shelly4pro-test/relay/2/power",
            "shellies/shelly4pro-test/relay/2/energy"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_getSubscriptions_channel_4(self):
        """Test getting subscriptions with a defined address on channel 2."""
        self.device.pluginProps['channel'] = 3
        topics = [
            "shellies/announce",
            "shellies/shelly4pro-test/online",
            "shellies/shelly4pro-test/relay/3",
            "shellies/shelly4pro-test/input/3",
            "shellies/shelly4pro-test/relay/3/power",
            "shellies/shelly4pro-test/relay/3/energy"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_channel_1(self):
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0", "on")
        self.assertTrue(self.shelly.isOn())

    def test_channel_2(self):
        self.device.pluginProps['channel'] = 1
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/1", "on")
        self.assertTrue(self.shelly.isOn())

    def test_channel_3(self):
        self.device.pluginProps['channel'] = 2
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/2", "on")
        self.assertTrue(self.shelly.isOn())

    def test_channel_4(self):
        self.device.pluginProps['channel'] = 3
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/3", "on")
        self.assertTrue(self.shelly.isOn())

    def test_handleMessage_relay_on(self):
        """Test getting a relay on message."""
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0", "on")
        self.assertTrue(self.shelly.isOn())
        self.assertFalse(self.shelly.device.states['overpower'])

    def test_handleMessage_relay_off(self):
        """Test getting a relay off message."""
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0", "off")
        self.assertTrue(self.shelly.isOff())
        self.assertFalse(self.shelly.device.states['overpower'])

    def test_handleMessage_relay_overpower(self):
        """Test getting a relay overpower message."""
        self.assertFalse(self.shelly.device.states['overpower'])
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0", "overpower")
        self.assertTrue(self.shelly.device.states['overpower'])

    def test_handleMessage_switch_on(self):
        """Test getting a switch on message."""
        self.assertFalse(self.shelly.device.states['sw-input'])
        self.shelly.handleMessage("shellies/shelly4pro-test/input/0", "1")
        self.assertTrue(self.shelly.device.states['sw-input'])

    def test_handleMessage_switch_off(self):
        """Test getting a switch off message."""
        self.shelly.device.states['sw-input'] = True
        self.assertTrue(self.shelly.device.states['sw-input'])
        self.shelly.handleMessage("shellies/shelly4pro-test/input/0", "0")
        self.assertFalse(self.shelly.device.states['sw-input'])

    def test_handleMessage_power(self):
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0/power", "0")
        self.assertEqual("0", self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("0 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0/power", "101.123")
        self.assertEqual("101.123", self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("101.123 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

    def test_handleMessage_energy(self):
        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0/energy", "0")
        self.assertAlmostEqual(0.0000, self.shelly.device.states['accumEnergyTotal'], 4)

        self.shelly.handleMessage("shellies/shelly4pro-test/relay/0/energy", "50")
        self.assertAlmostEqual(0.0008, self.shelly.device.states['accumEnergyTotal'], 4)

    def test_handleMessage_announce(self):
        announcement = '{"id": "shelly4pro-test", "mac": "aa:bb:cc:ee", "ip": "192.168.1.101", "fw_ver": "0.1.0", "new_fw": false}'
        self.shelly.handleMessage("shellies/announce", announcement)

        self.assertEqual("aa:bb:cc:ee", self.shelly.device.states['mac-address'])
        self.assertEqual("192.168.1.101", self.shelly.getIpAddress())
        self.assertEqual("0.1.0", self.shelly.getFirmware())
        self.assertFalse(self.shelly.updateAvailable())

    def test_handleMessage_online_true(self):
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly4pro-test/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly4pro-test/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        turnOn = IndigoAction(indigo.kDeviceAction.TurnOn)
        self.shelly.handleAction(turnOn)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly4pro-test/relay/0/command", "on")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        turnOff = IndigoAction(indigo.kDeviceAction.TurnOff)
        self.shelly.handleAction(turnOff)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly4pro-test/relay/0/command", "off")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_status_request(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly4pro-test/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_off_to_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly4pro-test/relay/0/command", "on")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_on_to_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly4pro-test/relay/0/command", "off")

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
        publish.assert_called_with("shellies/shelly4pro-test/command", "update")

