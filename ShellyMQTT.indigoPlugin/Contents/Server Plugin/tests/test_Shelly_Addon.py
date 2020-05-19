# coding=utf-8
import unittest
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.IndigoServer import Indigo

indigo = Indigo()
sys.modules['indigo'] = indigo
from Devices.Addons.Shelly_Addon import Shelly_Addon
from Devices.Relays.Shelly_1 import Shelly_1


class Test_Shelly_Addon(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.host_device = IndigoDevice(id=111111, name="Host Device")
        self.host_shelly = Shelly_1(self.host_device)

        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_Addon(self.device)

        indigo.activePlugin.shellyDevices[self.host_shelly.device.id] = self.host_shelly
        indigo.activePlugin.shellyDevices[self.shelly.device.id] = self.shelly

        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.host_device.pluginProps['address'] = "shellies/shelly-addon-test"
        self.host_device.pluginProps['broker-id'] = "12345"
        self.host_device.states['ip-address'] = "192.168.1.80"
        self.host_device.pluginProps['message-type'] = "shellies"

        self.device.pluginProps['host-id'] = "111111"

    def test_getHostDevice_none(self):
        self.device.pluginProps['host-id'] = None
        self.assertIsNone(self.shelly.getHostDevice())

    def test_getHostDevice(self):
        self.assertEqual(self.host_shelly, self.shelly.getHostDevice())

    def test_getBrokerId_no_host(self):
        self.device.pluginProps['host-id'] = None
        self.assertIsNone(self.shelly.getBrokerId())

    def test_getBrokerId(self):
        self.assertEqual(12345, self.shelly.getBrokerId())

    def test_getIpAddress_no_host(self):
        self.device.pluginProps['host-id'] = None
        self.assertIsNone(self.shelly.getIpAddress())

    def test_getIpAddress(self):
        self.assertEqual("192.168.1.80", self.shelly.getIpAddress())

    def test_getMessageType_no_host(self):
        self.device.pluginProps['host-id'] = None
        self.assertIsNone(self.shelly.getMessageType())

    def test_getMessageType(self):
        self.assertEqual("shellies", self.shelly.getMessageType())

    def test_isAddon(self):
        self.assertTrue(self.shelly.isAddon())


