# coding=utf-8
import unittest
from unittest import skip, expectedFailure
from mock import MagicMock
from mock import patch
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.MQTTConnector import MQTTConnector

sys.modules['indigo'] = MagicMock()
from Devices.Relays.Shelly_1PM import Shelly_1PM


class TestShelly(unittest.TestCase):

    def setUp(self):
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_1PM(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly1pm-test"
        self.device.updateStateOnServer("sw-input", False)
        self.device.updateStateOnServer("overpower", False)
        self.device.updateStateOnServer("longpush", False)
        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)
        self.device.updateStateOnServer("curEnergyLevel", 0)

    def test_getSubscriptions_no_address(self):
        """Test getting subscriptions with no address defined."""
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        """Test getting subscriptions with a defined address."""
        topics = [
            "shellies/announce",
            "shellies/shelly1pm-test/online",
            "shellies/shelly1pm-test/relay/0",
            "shellies/shelly1pm-test/input/0",
            "shellies/shelly1pm-test/longpush/0",
            "shellies/shelly1pm-test/relay/0/power",
            "shellies/shelly1pm-test/relay/0/energy",
            "shellies/shelly1pm-test/temperature",
            "shellies/shelly1pm-test/overtemperature"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_relay_on(self):
        """Test getting a relay on message."""
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly1pm-test/relay/0", "on")
        self.assertTrue(self.shelly.isOn())
        self.assertFalse(self.shelly.device.states['overpower'])

    def test_handleMessage_relay_off(self):
        """Test getting a relay off message."""
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.shelly.handleMessage("shellies/shelly1pm-test/relay/0", "off")
        self.assertTrue(self.shelly.isOff())
        self.assertFalse(self.shelly.device.states['overpower'])

    def test_handleMessage_relay_overpower(self):
        """Test getting a relay overpower message."""
        self.assertFalse(self.shelly.device.states['overpower'])
        self.shelly.handleMessage("shellies/shelly1pm-test/relay/0", "overpower")
        self.assertTrue(self.shelly.device.states['overpower'])

    def test_handleMessage_switch_on(self):
        """Test getting a switch on message."""
        self.assertFalse(self.shelly.device.states['sw-input'])
        self.shelly.handleMessage("shellies/shelly1pm-test/input/0", "1")
        self.assertTrue(self.shelly.device.states['sw-input'])

    def test_handleMessage_switch_off(self):
        """Test getting a switch off message."""
        self.shelly.device.states['sw-input'] = True
        self.assertTrue(self.shelly.device.states['sw-input'])
        self.shelly.handleMessage("shellies/shelly1pm-test/input/0", "0")
        self.assertFalse(self.shelly.device.states['sw-input'])

    def test_handleMessage_longpush_on(self):
        """Test getting a longpush on message."""
        self.assertFalse(self.shelly.device.states['longpush'])
        self.shelly.handleMessage("shellies/shelly1pm-test/longpush/0", "1")
        self.assertTrue(self.shelly.device.states['longpush'])

    def test_handleMessage_longpush_off(self):
        """Test getting a longpush off message."""
        self.shelly.device.states['longpush'] = True
        self.assertTrue(self.shelly.device.states['longpush'])
        self.shelly.handleMessage("shellies/shelly1pm-test/longpush/0", "0")
        self.assertFalse(self.shelly.device.states['longpush'])

    def test_handleMessage_power(self):
        self.shelly.handleMessage("shellies/shelly1pm-test/relay/0/power", "0")
        self.assertEqual("0", self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("0 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

        self.shelly.handleMessage("shellies/shelly1pm-test/relay/0/power", "101.123")
        self.assertEqual("101.123", self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("101.123 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

    @skip('ToDo')
    def test_handleMessage_energy(self):
        pass

    @skip('ToDo')
    def test_handleMessage_temperature(self):
        pass

    @skip('ToDo')
    def test_handleMessage_overtemperature(self):
        pass

    @skip('ToDo')
    def test_handleMessage_announce(self):
        pass

    @skip('ToDo')
    def test_handleMessage_online(self):
        pass

    @skip('ToDo')
    def test_handleAction_turn_on(self):
        pass

    @skip('ToDo')
    def test_handleAction_turn_off(self):
        pass

    @skip('ToDo')
    def test_handleAction_status_request(self):
        pass

    @skip('ToDo')
    def test_handleAction_toggle_off_to_on(self):
        pass

    @skip('ToDo')
    def test_handleAction_toggle_on_to_off(self):
        pass

    @skip('ToDo')
    def test_handleAction_reset_energy(self):
        pass

    @skip('ToDo')
    def test_handleAction_update_energy(self):
        pass
