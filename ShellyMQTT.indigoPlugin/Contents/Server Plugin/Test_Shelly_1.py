# coding=utf-8
import unittest
from unittest import skip, expectedFailure
from mock import MagicMock
from mock import patch
import sys
import logging

sys.modules['indigo'] = MagicMock()
from mocking.IndigoDevice import IndigoDevice
from Devices.Relays.Shelly_1 import Shelly_1


class TestShelly(unittest.TestCase):

    def setUp(self):
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_1(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

    def test_test(self):
        self.assertEqual("New Device", self.shelly.device.name)