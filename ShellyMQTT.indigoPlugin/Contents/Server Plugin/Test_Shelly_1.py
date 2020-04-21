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
from Devices.Relays.Shelly_1 import Shelly_1


class indigo:

    def __init__(self):
        pass

    class kDeviceAction:

        def __init__(self):
            pass

        class TurnOn:
            def __init__(self):
                pass

        class TurnOff:
            def __init__(self):
                pass


class Action:

    def __init__(self):
        self.deviceAction = None


class TestShelly(unittest.TestCase):

    def setUp(self):
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_1(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly1-test"
        self.device.updateStateOnServer("sw-input", False)
        self.device.updateStateOnServer("longpush", False)
        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)

    def test_getSubscriptions_no_address(self):
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        topics = [
            "shellies/announce",
            "shellies/shelly1-test/online",
            "shellies/shelly1-test/relay/0",
            "shellies/shelly1-test/input/0",
            "shellies/shelly1-test/longpush/0"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_relay_on(self):
        self.assertTrue(self.shelly.isOff())
        self.shelly.handleMessage("shellies/shelly1-test/relay/0", "on")
        self.assertTrue(self.shelly.isOn())

    def test_handleMessage_relay_off(self):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.shelly.handleMessage("shellies/shelly1-test/relay/0", "off")
        self.assertTrue(self.shelly.isOff())

    def test_handleMessage_switch_on(self):
        self.assertFalse(self.shelly.device.states['sw-input'])
        self.shelly.handleMessage("shellies/shelly1-test/input/0", "1")
        self.assertTrue(self.shelly.device.states['sw-input'])

    def test_handleMessage_switch_off(self):
        self.shelly.device.states['sw-input'] = True
        self.assertTrue(self.shelly.device.states['sw-input'])
        self.shelly.handleMessage("shellies/shelly1-test/input/0", "0")
        self.assertFalse(self.shelly.device.states['sw-input'])

    def test_handleMessage_longpush_on(self):
        self.assertFalse(self.shelly.device.states['longpush'])
        self.shelly.handleMessage("shellies/shelly1-test/longpush/0", "1")
        self.assertTrue(self.shelly.device.states['longpush'])

    def test_handleMessage_longpush_off(self):
        self.shelly.device.states['longpush'] = True
        self.assertTrue(self.shelly.device.states['longpush'])
        self.shelly.handleMessage("shellies/shelly1-test/longpush/0", "0")
        self.assertFalse(self.shelly.device.states['longpush'])

    def test_handleMessage_announce(self):
        announcement = '{"id": "shelly1-test", "mac": "aa:bb:cc:dd", "ip": "192.168.1.100", "fw_ver": "0.0.0", "new_fw": false}'
        self.shelly.handleMessage("shellies/announce", announcement)

        self.assertEqual("aa:bb:cc:dd", self.shelly.device.states['mac-address'])
        self.assertEqual("192.168.1.100", self.shelly.getIpAddress())
        self.assertEqual("0.0.0", self.shelly.getFirmware())
        self.assertFalse(self.shelly.updateAvailable())

    def test_handleMessage_online_true(self):
        self.shelly.device.states['online'] = False
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly1-test/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly1-test/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    @skip('Need a way to test kDeviceAction\'s')
    def test_handleAction_turn_on(self):
        self.shelly.turnOff()
        self.assertTrue(self.shelly.isOff())
        action = Action()
        action.deviceAction = indigo.kDeviceAction.TurnOn
        self.shelly.handleAction(action)
        self.assertTrue(self.shelly.isOn())

    @skip('Need a way to test kDeviceAction\'s')
    def test_handleAction_turn_off(self):
        self.shelly.turnOn()
        self.assertTrue(self.shelly.isOn())
        self.shelly.handleMessage("shellies/shelly1-test/relay/0", "0")
        self.assertTrue(self.shelly.isOff())

    @skip('Need a way to test kDeviceAction\'s')
    def test_handleAction_status_request(self):
        pass

    @skip('Need a way to test kDeviceAction\'s')
    def test_handleAction_toggle_off_to_on(self):
        pass

    @skip('Need a way to test kDeviceAction\'s')
    def test_handleAction_toggle_on_to_off(self):
        pass
