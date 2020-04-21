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

    @skip('ToDo')
    def test_getSubscriptions_no_address(self):
        pass

    @skip('ToDo')
    def test_getSubscriptions(self):
        pass

    @skip('ToDo')
    def test_handleMessage_relay_on(self):
        pass

    @skip('ToDo')
    def test_handleMessage_relay_off(self):
        pass

    @skip('ToDo')
    def test_handleMessage_relay_overpower(self):
        pass

    @skip('ToDo')
    def test_handleMessage_switch_on(self):
        pass

    @skip('ToDo')
    def test_handleMessage_switch_off(self):
        pass

    @skip('ToDo')
    def test_handleMessage_longpress_on(self):
        pass

    @skip('ToDo')
    def test_handleMessage_longpress_off(self):
        pass

    @skip('ToDo')
    def test_handleMessage_power(self):
        pass

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
