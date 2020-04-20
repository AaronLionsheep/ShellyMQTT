# coding=utf-8
import unittest
from unittest import skip, expectedFailure
from mock import MagicMock, call
from mock import patch
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.MQTTConnector import MQTTConnector
from mocking.ShellyPlugin import ShellyPlugin
import Devices


class TestShelly(unittest.TestCase):

    def setUp(self):
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Devices.Shelly.Shelly(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

    @patch('indigo.activePlugin')
    @patch('indigo.server.getPlugin')
    @patch('Devices.Shelly.Shelly.getSubscriptions', return_value=["test/one", "test/two"])
    def test_subscribe(self, getSubscriptions, getPlugin, activePlugin):
        """Test subscribing to a topic"""
        activePlugin.pluginPrefs.get.return_value = False
        getPlugin.return_value = MQTTConnector()

        self.device.pluginProps['broker-id'] = "12345"
        self.shelly.subscribe()

        subscriptions = [
            {'topic': "test/one", 'qos': 0},
            {'topic': "test/two", 'qos': 0}
        ]
        self.assertListEqual(subscriptions, getPlugin.return_value.getBrokerSubscriptions(12345))

    @patch('indigo.activePlugin')
    @patch('indigo.server.getPlugin')
    @patch('Devices.Shelly.Shelly.getSubscriptions', return_value=["test/one", "test/two"])
    def test_subscribe_with_connector_fix(self, getSubscriptions, getPlugin, activePlugin):
        """Test subscribing to a topic"""
        activePlugin.pluginPrefs.get.return_value = True
        getPlugin.return_value = MQTTConnector()

        self.device.pluginProps['broker-id'] = "12345"
        self.shelly.subscribe()

        subscriptions = [
            {'topic': "0:test/one", 'qos': 0},
            {'topic': "0:test/two", 'qos': 0}
        ]
        self.assertListEqual(subscriptions, getPlugin.return_value.getBrokerSubscriptions(12345))

    @patch('indigo.activePlugin')
    @patch('indigo.server.getPlugin')
    def test_publish(self, getPlugin, activePlugin):
        """Test publishing a payload to a topic"""
        activePlugin.pluginPrefs.get.return_value = False
        getPlugin.return_value = MQTTConnector()

        self.device.pluginProps['broker-id'] = "12345"
        self.shelly.publish("some/topic", {'the': 'payload'})

        expected = [
            {'topic': 'some/topic', 'retain': 0, 'qos': 0, 'payload': {'the': 'payload'}}
        ]
        self.assertListEqual(expected, getPlugin.return_value.getMessagesOut(12345))

    def test_getSubscriptions(self):
        self.assertEqual(0, len(self.shelly.getSubscriptions()))

    def test_getIpAddress(self):
        self.device.states['ip-address'] = "192.168.1.100"
        self.assertEqual("192.168.1.100", self.shelly.getIpAddress())

    def test_getAddress(self):
        self.device.pluginProps['address'] = "some/address"
        self.assertEqual("some/address", self.shelly.getAddress())

    def test_updateAvailable_has_update(self):
        self.device.states['has-firmware-update'] = True
        self.assertTrue(self.shelly.updateAvailable())

    def test_updateAvailable_no_update(self):
        self.device.states['has-firmware-update'] = False
        self.assertFalse(self.shelly.updateAvailable())

    def test_updateAvailable_no_info(self):
        self.assertFalse('has-firmware-update' in self.device.states.keys())
        self.assertFalse(self.shelly.updateAvailable())

    def test_getFirmware(self):
        self.device.states['firmware-version'] = "abc.123.d@qwerty"
        self.assertEqual("abc.123.d@qwerty", self.shelly.getFirmware())

    def test_getFirmware_no_info(self):
        self.assertFalse('firmware-version' in self.device.states.keys())
        self.assertIsNone(self.shelly.getFirmware())

    @patch('indigo.server.getPlugin', return_value=type('', (object,), {'isEnabled': lambda x: True})())
    def test_getMQTT_enabled(self, getPlugin):
        # getPlugin.return_value = type('', (object,), {'isEnabled': lambda x: True})()
        self.assertIsNotNone(self.shelly.getMQTT())
        getPlugin.assert_called_with("com.flyingdiver.indigoplugin.mqtt")

    @patch('indigo.server.getPlugin')
    def test_getMQTT_disabled(self, getPlugin):
        getPlugin.return_value = type('', (object,), {'isEnabled': lambda x: False})()
        self.assertIsNone(self.shelly.getMQTT())

    def test_getBrokerId_valid(self):
        self.device.pluginProps['broker-id'] = "12345"
        self.assertEquals(12345, self.shelly.getBrokerId())

    def test_getBrokerId_empty(self):
        self.assertIsNone(self.shelly.getBrokerId())

        self.device.pluginProps['broker-id'] = None
        self.assertIsNone(self.shelly.getBrokerId())

        self.device.pluginProps['broker-id'] = ""
        self.assertIsNone(self.shelly.getBrokerId())

    def test_getMessageType(self):
        self.device.pluginProps["message-type"] = "some-type"
        self.assertEquals("some-type", self.shelly.getMessageType())

    def test_getMessaegType_empty(self):
        self.assertEquals("", self.shelly.getMessageType())

    def test_getAnnounceMessageType_same(self):
        self.device.pluginProps['announce-message-type-same-as-message-type'] = True
        self.assertIsNone(self.shelly.getAnnounceMessageType())

    def test_getAnnounceMessageType_different(self):
        self.device.pluginProps['message-type'] = "some-type"
        self.device.pluginProps['announce-message-type'] = "some-other-type"
        self.device.pluginProps['announce-message-type-same-as-message-type'] = False
        self.assertEquals("some-type", self.shelly.getMessageType())
        self.assertEquals("some-other-type", self.shelly.getAnnounceMessageType())

    def test_getMessageTypes(self):
        self.device.pluginProps['message-type'] = "some-type"
        self.assertListEqual(["some-type"], self.shelly.getMessageTypes())

        self.device.pluginProps['announce-message-type'] = "some-other-type"
        self.device.pluginProps['announce-message-type-same-as-message-type'] = True
        self.assertListEqual(["some-type"], self.shelly.getMessageTypes())

        self.device.pluginProps['announce-message-type-same-as-message-type'] = False
        self.assertListEqual(["some-type", "some-other-type"], self.shelly.getMessageTypes())

        del self.device.pluginProps['message-type']
        self.assertListEqual(["some-other-type"], self.shelly.getMessageTypes())

    @patch('Devices.Shelly.Shelly.publish')
    def test_sendStatusRequestCommand(self, publish):
        self.shelly.device.pluginProps['address'] = "shellies/test-shelly"
        self.shelly.sendStatusRequestCommand()

        publish.assert_called_with("shellies/test-shelly/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_announce(self, publish):
        self.shelly.device.pluginProps['address'] = "shellies/test-shelly"
        self.shelly.announce()

        publish.assert_called_with("shellies/test-shelly/command", "announce")

    @patch('Devices.Shelly.Shelly.publish')
    def test_sendUpdateFirmwareCommand(self, publish):
        self.shelly.device.pluginProps['address'] = "shellies/test-shelly"
        self.shelly.sendUpdateFirmwareCommand()

        publish.assert_called_with("shellies/test-shelly/command", "update_fw")

    def test_setTemperature(self):
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.setTemperature(75)
        self.assertEqual(75, self.device.states['temperature']['value'])
        self.assertEqual("75.0 °F", self.device.states['temperature']['uiValue'])
        self.assertEquals(1, self.device.states['temperature']['decimalPlaces'])

    def test_setTemperature_custom(self):
        self.device.pluginProps['units'] = "C->F"
        self.device.pluginProps['offset'] = "1.2345"
        self.device.pluginProps['decimals'] = 3
        self.shelly.setTemperature(100, state="temp", unitsProps="units", decimalsProps="decimals", offsetProps="offset")
        self.assertEqual(213.2345, self.device.states['temp']['value'])
        self.assertEqual("213.234 °F", self.device.states['temp']['uiValue'])
        self.assertEquals(3, self.device.states['temp']['decimalPlaces'])

    def test_setTemperature_with_valid_offset(self):
        self.device.pluginProps['temp-units'] = "F"
        self.device.pluginProps['temp-offset'] = "1.25"
        self.shelly.setTemperature(75)
        self.assertEqual(76.25, self.device.states['temperature']['value'])
        self.assertEqual("76.2 °F", self.device.states['temperature']['uiValue'])
        self.assertEquals(1, self.device.states['temperature']['decimalPlaces'])

    def test_setTemperature_with_invalid_offset(self):
        self.device.pluginProps['temp-units'] = "F"
        self.device.pluginProps['temp-offset'] = "a"
        self.assertRaises(ValueError, self.shelly.setTemperature(75))

    def test_setTemperature_F(self):
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.setTemperature(50)
        self.assertEqual(50.0, self.device.states['temperature']['value'])
        self.assertEqual("50.0 °F", self.device.states['temperature']['uiValue'])
        self.assertEquals(1, self.device.states['temperature']['decimalPlaces'])

    def test_setTemperature_C_to_F(self):
        self.device.pluginProps['temp-units'] = "C->F"
        self.shelly.setTemperature(0)
        self.assertEqual(32.0, self.device.states['temperature']['value'])
        self.assertEqual("32.0 °F", self.device.states['temperature']['uiValue'])
        self.assertEquals(1, self.device.states['temperature']['decimalPlaces'])

    def test_setTemperature_C(self):
        self.device.pluginProps['temp-units'] = "C"
        self.shelly.setTemperature(10)
        self.assertEqual(10.0, self.device.states['temperature']['value'])
        self.assertEqual("10.0 °C", self.device.states['temperature']['uiValue'])
        self.assertEquals(1, self.device.states['temperature']['decimalPlaces'])

    def test_setTemperature_F_to_C(self):
        self.device.pluginProps['temp-units'] = "F->C"
        self.shelly.setTemperature(212)
        self.assertEqual(100.0, self.device.states['temperature']['value'])
        self.assertEqual("100.0 °C", self.device.states['temperature']['uiValue'])
        self.assertEquals(1, self.device.states['temperature']['decimalPlaces'])

    def test_convertCtoF(self):
        """Convert from celsius to fahrenheit"""
        self.assertEqual(32, self.shelly.convertCtoF(0))
        self.assertEqual(122, self.shelly.convertCtoF(50))
        self.assertEqual(77, self.shelly.convertCtoF(25))
        self.assertAlmostEqual(82.4, self.shelly.convertCtoF(28), 4)

    def test_convertFtoC(self):
        """Convert from fahrenheit to celsius"""
        self.assertEqual(0, self.shelly.convertFtoC(32))
        self.assertEqual(50, self.shelly.convertFtoC(122))
        self.assertEqual(25, self.shelly.convertFtoC(77))
        self.assertAlmostEqual(28, self.shelly.convertFtoC(82.4), 4)

    def test_pasrseAnnouncement_no_firmware_updated(self):
        """Parse an announcement message that indicates no firmware change"""
        self.device.pluginProps['address'] = "shellies/test-shelly"
        announcement = '{"id": "test-shelly", "mac": "aa:bb:cc:dd", "ip": "192.168.1.100", "fw_ver": "0.0.0", "new_fw": false}'

        self.shelly.parseAnnouncement(announcement)
        self.assertEqual("aa:bb:cc:dd", self.device.states['mac-address']['value'])
        self.assertEqual("192.168.1.100", self.device.states['ip-address']['value'])
        self.assertEqual("0.0.0", self.device.states['firmware-version']['value'])
        self.assertFalse(self.device.states['has-firmware-update']['value'])

    def test_parseAnnouncement_with_firmware_updated(self):
        """Parse an announcement message that indicates firmware has changed"""
        self.device.pluginProps['address'] = "shellies/test-shelly"
        announcement = '{"id": "test-shelly", "mac": "aa:bb:cc:dd:ff", "ip": "192.168.1.101", "fw_ver": "0.0.0", "new_fw": true}'

        self.shelly.parseAnnouncement(announcement)
        self.assertEqual("aa:bb:cc:dd:ff", self.device.states['mac-address']['value'])
        self.assertEqual("192.168.1.101", self.device.states['ip-address']['value'])
        self.assertEqual("0.0.0", self.device.states['firmware-version']['value'])
        self.assertTrue(self.device.states['has-firmware-update']['value'])

    def test_parseAnnouncement_invalid_device_data(self):
        """Parse an announcement message for the wrong device"""
        self.device.pluginProps['address'] = "shellies/test-shelly"
        announcement = '{"identifier": "test-shelly", "mac": "aa:bb:cc:dd", "ip": "192.168.1.100", "fw_ver": "0.0.0", "new_fw": false}'
        self.shelly.parseAnnouncement(announcement)
        self.assertDictEqual({}, self.device.states)

        announcement = '{"identifier": "test-shelly"}'
        self.shelly.parseAnnouncement(announcement)
        self.assertFalse('mac-address' in self.device.states.keys())
        self.assertFalse('ip-address' in self.device.states.keys())
        self.assertFalse('firmware-version' in self.device.states.keys())
        self.assertFalse('has-firmware-update' in self.device.states.keys())

    def test_parseAnnouncement_invalid_announcement_for_device(self):
        """Parse an invalid announcement message"""
        self.device.pluginProps['address'] = "shellies/test-shelly"
        self.device.updateStateOnServer('mac-address', '1')
        self.device.updateStateOnServer('ip-address', '2')
        self.device.updateStateOnServer('firmware-version', '3')
        self.device.updateStateOnServer('has-firmware-update', False)

        self.assertEqual("1", self.device.states['mac-address']['value'])
        self.assertEqual("2", self.device.states['ip-address']['value'])
        self.assertEqual("3", self.device.states['firmware-version']['value'])
        self.assertFalse(self.device.states['has-firmware-update']['value'])

        announcement = '{"id": "test-invalid-shelly", "mac": "aa:bb:cc:dd:ff", "ip": "192.168.1.101", "fw_ver": "0.0.0", "new_fw": true}'
        self.shelly.parseAnnouncement(announcement)
        self.assertEqual("1", self.device.states['mac-address']['value'])
        self.assertEqual("2", self.device.states['ip-address']['value'])
        self.assertEqual("3", self.device.states['firmware-version']['value'])
        self.assertFalse(self.device.states['has-firmware-update']['value'])

    @skip("Todo")
    def test_updateEnergy(self):
        """Test updating the energy"""
        pass

    @skip("Todo")
    def test_updateEnergy_after_reset(self):
        """Test updating energy after it has been reset"""
        pass

    @skip("Todo")
    def test_resetEnergy(self):
        """Test resetting the energy data"""
        pass

    def test_turnOn(self):
        """Test turning the device on in Indigo"""
        self.device.states['onOffState'] = False
        self.shelly.turnOn()
        self.assertTrue(self.device.states['onOffState']['value'])

    def test_turnOff(self):
        """Test turning the device off in Indigo"""
        self.device.states['onOffState'] = True
        self.shelly.turnOff()
        self.assertFalse(self.device.states['onOffState']['value'])

    def test_isOn(self):
        """Test determining if the device is on"""
        self.device.states['onOffState'] = True
        self.assertTrue(self.shelly.isOn())

        self.device.states['onOffState'] = False
        self.assertFalse(self.shelly.isOn())

    def test_isOff(self):
        """Test determining of the device is off"""
        self.device.states['onOffState'] = False
        self.assertTrue(self.shelly.isOff())

        self.device.states['onOffState'] = True
        self.assertFalse(self.shelly.isOff())

    def test_getChannel_default(self):
        """Test getting the default channel"""
        self.assertEqual(0, self.shelly.getChannel())

    def test_getChannel_custom(self):
        """Test getting a defined channel"""
        self.device.pluginProps['channel'] = 1
        self.assertEqual(1, self.shelly.getChannel())

    def test_isAddon(self):
        """Test determining of the device is an addon"""
        self.assertFalse(self.shelly.isAddon())

    @patch('indigo.kStateImageSel')
    def test_updateStateImage_on(self, image):
        """Test setting the state icon when the device is on"""
        self.device.states['onOffState'] = True
        self.shelly.updateStateImage()
        self.assertEqual(image.PowerOn, self.device.image)

    @patch('indigo.kStateImageSel')
    def test_updateStateImage_off(self, image):
        """Test setting the state icon when the device is off"""
        self.device.states['onOffState'] = False
        self.shelly.updateStateImage()
        self.assertEqual(image.PowerOff, self.device.image)

    def test_isMuted(self):
        """Test getting whether the device is set to be muted"""
        self.assertFalse(self.shelly.isMuted())
        self.device.pluginProps['muted'] = True
        self.assertTrue(self.shelly.isMuted())

    def test_getMutedLoggingMethods(self):
        """Test getting the log levels to mute when the device is muted"""
        self.assertListEqual(["debug", "info"], self.shelly.getMutedLoggingMethods())