# coding=utf-8
import unittest
from unittest.mock import patch
import sys
import logging

from Devices.tests.mocking.IndigoDevice import IndigoDevice
from Devices.tests.mocking.IndigoServer import Indigo
from Devices.tests.mocking.IndigoAction import IndigoAction

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Relays.Shelly_Uni_Relay import Shelly_Uni_Relay


class Test_Shelly_Uni_Relay(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Uni_Relay(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-uni-relay"
        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)

    def test_getSubscriptions_no_address(self):
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        topics = [
            "shellies/announce",
            "shellies/shelly-uni-relay/online",
            "shellies/shelly-uni-relay/info",
            "shellies/shelly-uni-relay/relay/0",
            "shellies/shelly-uni-relay/ext_temperatures",
            "shellies/shelly-uni-relay/ext_humidities"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_relay_on(self):
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly-uni-relay/relay/0", "on")
        self.assertTrue(self.shelly.isOn())

    def test_handleMessage_relay_off(self):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.shelly.handleMessage("shellies/shelly-uni-relay/relay/0", "off")
        self.assertTrue(self.shelly.isOff())

    def test_handleMessage_announce(self):
        announcement = '{"id": "shelly-uni-relay", "mac": "aa:bb:cc:dd", "ip": "192.168.1.100", "fw_ver": "0.0.0", "new_fw": false}'
        self.shelly.handleMessage("shellies/announce", announcement)

        self.assertEqual("aa:bb:cc:dd", self.shelly.device.states['mac-address'])
        self.assertEqual("192.168.1.100", self.shelly.getIpAddress())
        self.assertEqual("0.0.0", self.shelly.getFirmware())
        self.assertFalse(self.shelly.updateAvailable())

    def test_handleMessage_online_true(self):
        self.shelly.device.states['online'] = False
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-uni-relay/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-uni-relay/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        turnOn = IndigoAction(indigo.kDeviceAction.TurnOn)
        self.shelly.handleAction(turnOn)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly-uni-relay/relay/0/command", "on")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_turn_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        turnOff = IndigoAction(indigo.kDeviceAction.TurnOff)
        self.shelly.handleAction(turnOff)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly-uni-relay/relay/0/command", "off")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_status_request(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-uni-relay/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_off_to_on(self, publish):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOn())
        publish.assert_called_with("shellies/shelly-uni-relay/relay/0/command", "on")

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_toggle_on_to_off(self, publish):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        toggle = IndigoAction(indigo.kDeviceAction.Toggle)
        self.shelly.handleAction(toggle)
        self.assertTrue(self.shelly.isOff())
        publish.assert_called_with("shellies/shelly-uni-relay/relay/0/command", "off")

    def test_validateConfigUI(self):
        values = {
            "broker-id": "12345",
            "address": "some/address",
            "message-type": "a-type",
            "announce-message-type-same-as-message-type": True
        }

        isValid, valuesDict, errors = Shelly_Uni_Relay.validateConfigUI(values, None, None)
        self.assertTrue(isValid)

    def test_validateConfigUI_announce_message_type(self):
        values = {
            "broker-id": "12345",
            "address": "some/address",
            "message-type": "a-type",
            "announce-message-type-same-as-message-type": False,
            "announce-message-type": "another-type"
        }

        isValid, valuesDict, errors = Shelly_Uni_Relay.validateConfigUI(values, None, None)
        self.assertTrue(isValid)

    def test_validateConfigUI_invalid(self):
        values = {
            "broker-id": "",
            "address": "",
            "message-type": "",
            "announce-message-type-same-as-message-type": False,
            "announce-message-type": ""
        }

        isValid, valuesDict, errors = Shelly_Uni_Relay.validateConfigUI(values, None, None)
        self.assertFalse(isValid)
        self.assertTrue("broker-id" in errors)
        self.assertTrue("address" in errors)
        self.assertTrue("message-type" in errors)
        self.assertTrue("announce-message-type" in errors)

    def test_handleMessage_info(self):
        payload = '{"adcs": [{"voltage": 12.13}]}'
        self.shelly.handleMessage("shellies/shelly-uni-relay/info", payload)
        self.assertEqual(12.13, self.device.states['voltage'])
