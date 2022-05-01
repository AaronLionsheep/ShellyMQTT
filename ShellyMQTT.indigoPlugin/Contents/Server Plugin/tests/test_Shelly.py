# coding=utf-8
import unittest
from mock import patch
import sys
import logging

from mocking.IndigoDevice import IndigoDevice
from mocking.IndigoServer import Indigo
from mocking.IndigoTrigger import IndigoTrigger

indigo = Indigo()
sys.modules['indigo'] = indigo
import Devices.Shelly


class Test_Shelly(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Devices.Shelly.Shelly(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['broker-id'] = "12345"
        self.device.pluginProps['address'] = "shellies/test-shelly"
        self.device.pluginProps['resetEnergyOffset'] = 0
        self.device.pluginProps['last-input-event-id'] = -1

    @patch('Devices.Shelly.Shelly.getSubscriptions', return_value=["test/one", "test/two"])
    def test_subscribe(self, getSubscriptions):
        """Test subscribing to a topic."""
        self.shelly.subscribe()

        subscriptions = [
            {'topic': "test/one", 'qos': 0},
            {'topic': "test/two", 'qos': 0}
        ]
        self.assertListEqual(subscriptions, self.shelly.getMQTT().getBrokerSubscriptions(12345))

    @patch('Devices.Shelly.Shelly.getSubscriptions', return_value=["test/one", "test/two"])
    def test_subscribe_with_connector_fix(self, getSubscriptions):
        """Test subscribing to a topic."""
        indigo.activePlugin.pluginPrefs['connector-fix'] = True

        self.shelly.subscribe()

        subscriptions = [
            {'topic': "0:test/one", 'qos': 0},
            {'topic': "0:test/two", 'qos': 0}
        ]
        self.assertListEqual(subscriptions, self.shelly.getMQTT().getBrokerSubscriptions(12345))

    def test_publish(self):
        """Test publishing a payload to a topic."""
        self.shelly.publish("some/topic", {'the': 'payload'})

        expected = [
            {'topic': 'some/topic', 'retain': 0, 'qos': 0, 'payload': {'the': 'payload'}}
        ]
        self.assertListEqual(expected, self.shelly.getMQTT().getMessagesOut(12345))

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

    def test_getMQTT_enabled(self):
        indigo.server.plugins["com.flyingdiver.indigoplugin.mqtt"].enabled = True
        self.assertIsNotNone(self.shelly.getMQTT())
        self.assertTrue(self.shelly.getMQTT().isEnabled())

    def test_getMQTT_disabled(self):
        indigo.server.plugins["com.flyingdiver.indigoplugin.mqtt"].enabled = False
        self.assertIsNone(self.shelly.getMQTT())

    def test_getBrokerId_valid(self):
        self.assertEquals(12345, self.shelly.getBrokerId())

    def test_getBrokerId_empty(self):
        self.device.pluginProps['broker-id'] = None
        self.assertIsNone(self.shelly.getBrokerId())

        self.device.pluginProps['broker-id'] = ""
        self.assertIsNone(self.shelly.getBrokerId())

    def test_getMessageType(self):
        self.device.pluginProps["message-type"] = "some-type"
        self.assertEquals("some-type", self.shelly.getMessageType())

    def test_getMessageType_empty(self):
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
        self.shelly.sendStatusRequestCommand()

        publish.assert_called_with("shellies/test-shelly/command", "update")

    @patch('Devices.Shelly.Shelly.publish')
    def test_announce(self, publish):
        self.shelly.announce()

        publish.assert_called_with("shellies/test-shelly/command", "announce")

    @patch('Devices.Shelly.Shelly.publish')
    def test_sendUpdateFirmwareCommand(self, publish):
        self.shelly.sendUpdateFirmwareCommand()

        publish.assert_called_with("shellies/test-shelly/command", "update_fw")

    def test_setTemperature(self):
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.setTemperature(75)
        self.assertEqual(75, self.device.states['temperature'])
        self.assertEqual("75.0 °F", self.device.states_meta['temperature']['uiValue'])
        self.assertEquals(1, self.device.states_meta['temperature']['decimalPlaces'])

    def test_setTemperature_custom(self):
        self.device.pluginProps['units'] = "C->F"
        self.device.pluginProps['offset'] = "1.2345"
        self.device.pluginProps['decimals'] = 3
        self.shelly.setTemperature(100, state="temp", unitsProps="units", decimalsProps="decimals", offsetProps="offset")
        self.assertEqual(213.2345, self.device.states['temp'])
        self.assertEqual("213.234 °F", self.device.states_meta['temp']['uiValue'])
        self.assertEquals(3, self.device.states_meta['temp']['decimalPlaces'])

    def test_setTemperature_with_valid_offset(self):
        self.device.pluginProps['temp-units'] = "F"
        self.device.pluginProps['temp-offset'] = "1.25"
        self.shelly.setTemperature(75)
        self.assertEqual(76.25, self.device.states['temperature'])
        self.assertEqual("76.2 °F", self.device.states_meta['temperature']['uiValue'])
        self.assertEquals(1, self.device.states_meta['temperature']['decimalPlaces'])

    def test_setTemperature_with_invalid_offset(self):
        self.device.pluginProps['temp-units'] = "F"
        self.device.pluginProps['temp-offset'] = "a"
        self.assertRaises(ValueError, self.shelly.setTemperature(75))

    def test_setTemperature_F(self):
        self.device.pluginProps['temp-units'] = "F"
        self.shelly.setTemperature(50)
        self.assertEqual(50.0, self.device.states['temperature'])
        self.assertEqual("50.0 °F", self.device.states_meta['temperature']['uiValue'])
        self.assertEquals(1, self.device.states_meta['temperature']['decimalPlaces'])

    def test_setTemperature_C_to_F(self):
        self.device.pluginProps['temp-units'] = "C->F"
        self.shelly.setTemperature(0)
        self.assertEqual(32.0, self.device.states['temperature'])
        self.assertEqual("32.0 °F", self.device.states_meta['temperature']['uiValue'])
        self.assertEquals(1, self.device.states_meta['temperature']['decimalPlaces'])

    def test_setTemperature_C(self):
        self.device.pluginProps['temp-units'] = "C"
        self.shelly.setTemperature(10)
        self.assertEqual(10.0, self.device.states['temperature'])
        self.assertEqual("10.0 °C", self.device.states_meta['temperature']['uiValue'])
        self.assertEquals(1, self.device.states_meta['temperature']['decimalPlaces'])

    def test_setTemperature_F_to_C(self):
        self.device.pluginProps['temp-units'] = "F->C"
        self.shelly.setTemperature(212)
        self.assertEqual(100.0, self.device.states['temperature'])
        self.assertEqual("100.0 °C", self.device.states_meta['temperature']['uiValue'])
        self.assertEquals(1, self.device.states_meta['temperature']['decimalPlaces'])

    def test_convertCtoF(self):
        """Convert from celsius to fahrenheit."""
        self.assertEqual(32, self.shelly.convertCtoF(0))
        self.assertEqual(122, self.shelly.convertCtoF(50))
        self.assertEqual(77, self.shelly.convertCtoF(25))
        self.assertAlmostEqual(82.4, self.shelly.convertCtoF(28), 4)

    def test_convertFtoC(self):
        """Convert from fahrenheit to celsius."""
        self.assertEqual(0, self.shelly.convertFtoC(32))
        self.assertEqual(50, self.shelly.convertFtoC(122))
        self.assertEqual(25, self.shelly.convertFtoC(77))
        self.assertAlmostEqual(28, self.shelly.convertFtoC(82.4), 4)

    def test_pasrseAnnouncement_no_firmware_updated(self):
        """Parse an announcement message that indicates no firmware change."""
        self.device.pluginProps['address'] = "shellies/test-shelly"
        announcement = '{"id": "test-shelly", "mac": "aa:bb:cc:dd", "ip": "192.168.1.100", "fw_ver": "0.0.0", "new_fw": false}'

        self.shelly.parseAnnouncement(announcement)
        self.assertEqual("aa:bb:cc:dd", self.device.states['mac-address'])
        self.assertEqual("192.168.1.100", self.device.states['ip-address'])
        self.assertEqual("0.0.0", self.device.states['firmware-version'])
        self.assertFalse(self.device.states['has-firmware-update'])

    def test_parseAnnouncement_with_firmware_updated(self):
        """Parse an announcement message that indicates firmware has changed."""
        self.device.pluginProps['address'] = "shellies/test-shelly"
        announcement = '{"id": "test-shelly", "mac": "aa:bb:cc:dd:ff", "ip": "192.168.1.101", "fw_ver": "0.0.0", "new_fw": true}'

        self.shelly.parseAnnouncement(announcement)
        self.assertEqual("aa:bb:cc:dd:ff", self.device.states['mac-address'])
        self.assertEqual("192.168.1.101", self.device.states['ip-address'])
        self.assertEqual("0.0.0", self.device.states['firmware-version'])
        self.assertTrue(self.device.states['has-firmware-update'])

    def test_parseAnnouncement_invalid_device_data(self):
        """Parse an announcement message for the wrong device."""
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
        """Parse an invalid announcement message."""
        self.device.pluginProps['address'] = "shellies/test-shelly"
        self.device.updateStateOnServer('mac-address', '1')
        self.device.updateStateOnServer('ip-address', '2')
        self.device.updateStateOnServer('firmware-version', '3')
        self.device.updateStateOnServer('has-firmware-update', False)

        self.assertEqual("1", self.device.states['mac-address'])
        self.assertEqual("2", self.device.states['ip-address'])
        self.assertEqual("3", self.device.states['firmware-version'])
        self.assertFalse(self.device.states['has-firmware-update'])

        announcement = '{"id": "test-invalid-shelly", "mac": "aa:bb:cc:dd:ff", "ip": "192.168.1.101", "fw_ver": "0.0.0", "new_fw": true}'
        self.shelly.parseAnnouncement(announcement)
        self.assertEqual("1", self.device.states['mac-address'])
        self.assertEqual("2", self.device.states['ip-address'])
        self.assertEqual("3", self.device.states['firmware-version'])
        self.assertFalse(self.device.states['has-firmware-update'])

    def test_updateEnergy_4_decimals(self):
        self.shelly.updateEnergy(50)
        self.assertAlmostEqual(0.0008, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("0.0008 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])
        self.assertEqual(4, self.shelly.device.states_meta['accumEnergyTotal']['decimalPlaces'])

    def test_updateEnergy_3_decimals(self):
        self.shelly.updateEnergy(5000)
        self.assertAlmostEqual(0.0833, self.shelly.device.states['accumEnergyTotal'], 3)
        self.assertEqual("0.083 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])
        self.assertEqual(4, self.shelly.device.states_meta['accumEnergyTotal']['decimalPlaces'])

    def test_updateEnergy_2_decimals(self):
        self.shelly.updateEnergy(500000)
        self.assertAlmostEqual(8.3333, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("8.33 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])
        self.assertEqual(4, self.shelly.device.states_meta['accumEnergyTotal']['decimalPlaces'])

    def test_updateEnergy_1_decimal(self):
        self.shelly.updateEnergy(5000000)
        self.assertAlmostEqual(83.3333, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("83.3 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])
        self.assertEqual(4, self.shelly.device.states_meta['accumEnergyTotal']['decimalPlaces'])

    def test_updateEnergy_after_reset(self):
        """Test updating energy after it has been reset."""
        self.shelly.updateEnergy(30)
        self.assertAlmostEqual(0.0005, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("0.0005 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])

        self.shelly.resetEnergy()
        self.assertAlmostEqual(0.0000, self.shelly.device.states['accumEnergyTotal'], 4)

        self.shelly.updateEnergy(60)
        self.assertAlmostEqual(0.0005, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("0.0005 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])

    def test_resetEnergy(self):
        """Test resetting the energy data."""
        self.shelly.updateEnergy(15)
        self.assertAlmostEqual(0.00025, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("0.0003 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])

        self.shelly.resetEnergy()
        self.assertAlmostEqual(0.0000, self.shelly.device.states['accumEnergyTotal'], 4)

    def test_turnOn(self):
        """Test turning the device on in Indigo."""
        self.device.states['onOffState'] = False
        self.shelly.turnOn()
        self.assertTrue(self.device.states['onOffState'])

    def test_turnOff(self):
        """Test turning the device off in Indigo."""
        self.device.states['onOffState'] = True
        self.shelly.turnOff()
        self.assertFalse(self.device.states['onOffState'])

    def test_isOn(self):
        """Test determining if the device is on."""
        self.device.states['onOffState'] = True
        self.assertTrue(self.shelly.isOn())

        self.device.states['onOffState'] = False
        self.assertFalse(self.shelly.isOn())

    def test_isOff(self):
        """Test determining of the device is off."""
        self.device.states['onOffState'] = False
        self.assertTrue(self.shelly.isOff())

        self.device.states['onOffState'] = True
        self.assertFalse(self.shelly.isOff())

    def test_getChannel_default(self):
        """Test getting the default channel."""
        self.assertEqual(0, self.shelly.getChannel())

    def test_getChannel_custom(self):
        """Test getting a defined channel."""
        self.device.pluginProps['channel'] = 1
        self.assertEqual(1, self.shelly.getChannel())

    def test_isAddon(self):
        """Test determining of the device is an addon."""
        self.assertFalse(self.shelly.isAddon())

    def test_updateStateImage_on(self):
        """Test setting the state icon when the device is on."""
        self.device.states['onOffState'] = True
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.PowerOn, self.device.image)

    def test_updateStateImage_off(self):
        """Test setting the state icon when the device is off."""
        self.device.states['onOffState'] = False
        self.shelly.updateStateImage()
        self.assertEqual(indigo.kStateImageSel.PowerOff, self.device.image)

    def test_isMuted(self):
        """Test getting whether the device is set to be muted."""
        self.assertFalse(self.shelly.isMuted())
        self.device.pluginProps['muted'] = True
        self.assertTrue(self.shelly.isMuted())

    def test_getMutedLoggingMethods(self):
        """Test getting the log levels to mute when the device is muted."""
        self.assertListEqual(["debug", "info"], self.shelly.getMutedLoggingMethods())

    def test_get_last_input_event_id(self):
        """Test getting the last input event id"""
        self.assertEqual(-1, self.shelly.getLastInputEventId())
        self.device.pluginProps['last-input-event-id'] = "5"
        self.assertEqual(5, self.shelly.getLastInputEventId())

    def test_get_last_input_event_id_default_to_negative_one(self):
        """Test getting the last input event id when there is no value"""
        del self.device.pluginProps['last-input-event-id']
        self.assertFalse('last-input-event-id' in self.device.pluginProps.keys())
        self.assertEqual(-1, self.shelly.getLastInputEventId())

    def test_process_input_event_invalid_event_type_returns_None(self):
        """Test processing an event message with an invalid event type"""
        message = '{"event": null, "event_cnt": 0}'

        self.assertIsNone(self.shelly.processInputEvent(message))

    def test_process_input_event_invalid_event_count_returns_None(self):
        """Test processing an event message with an invalid event count"""
        message = '{"event": "", "event_cnt": null}'

        self.assertIsNone(self.shelly.processInputEvent(message))

    def test_process_input_event_new_event_id_stored(self):
        """Test processing an event message stores the new event id"""
        message = '{"event": "S", "event_cnt": 1}'

        self.shelly.processInputEvent(message)
        self.assertEqual(1, self.shelly.getLastInputEventId())

    def test_process_input_event_duplicate_event_not_processed(self):
        """Test processing an event message that has been previously processed is not reprocessed"""
        message = '{"event": "S", "event_cnt": 1}'

        self.shelly.processInputEvent(message)
        self.assertEqual(1, self.shelly.getLastInputEventId())
        # Duplicate message processed...
        self.shelly.processInputEvent(message)
        self.assertEqual(1, self.shelly.getLastInputEventId())

    def test_process_input_event_trigger_executed(self):
        """Test processing an event message and a trigger was executed"""
        trigger_S = IndigoTrigger("input-event-s", {'device-id': self.device.id})
        trigger_S_other = IndigoTrigger("input-event-s", {'device-id': self.device.id + 1})
        trigger_L = IndigoTrigger("input-event-l", {'device-id': self.device.id})

        indigo.activePlugin.triggers['1'] = trigger_S
        indigo.activePlugin.triggers['2'] = trigger_L
        indigo.activePlugin.triggers['3'] = trigger_S_other

        message = '{"event": "S", "event_cnt": 1}'

        self.shelly.processInputEvent(message)
        self.assertTrue(trigger_S.executed)
        self.assertFalse(trigger_L.executed)
        self.assertFalse(trigger_S_other.executed)

    def test_process_temperature_status_normal_event_trigger_executed(self):
        """Test that a normal temperature status fires executes a trigger"""
        trigger = IndigoTrigger("abnormal-temperature-status-any", {})
        indigo.activePlugin.triggers['1'] = trigger

        self.shelly.processTemperatureStatus("Normal")
        self.assertFalse(trigger.executed)

    def test_process_temperature_status_abnormal_event_trigger_executed(self):
        """Test that an abnormal temperature status fires executes a trigger"""
        trigger = IndigoTrigger("abnormal-temperature-status-any", {})
        indigo.activePlugin.triggers['1'] = trigger

        self.shelly.processTemperatureStatus("High")
        self.assertTrue(trigger.executed)

    def test_process_temperature_sensors_creates_correct_list(self):
        """Test that the list of sensors is properly created"""
        payload = '{"0":{"hwID":"2885186e38190123","tC":20.5}, "1":{"hwID":"2885186e38190456","tC":21.5}, "2":{"hwID":"2885186e38190789","tC":22.5}}'
        self.shelly.processTemperatureSensors(payload)

        expected = [
            {"channel": 0, "id": "2885186e38190123"},
            {"channel": 1, "id": "2885186e38190456"},
            {"channel": 2, "id": "2885186e38190789"}
        ]
        self.assertItemsEqual(expected, self.shelly.temperature_sensors)

    def test_process_temperature_sensors_ignores_invalid_sensors(self):
        """Test that the list of sensors is properly created"""
        payload = '{"0":{"hwID":"2885186e38190123","tC":20.5}, "1":{"hwID":"000000000000000","tC":999}, "2":{"hwID":"2885186e38190789","tC":22.5}}'
        self.shelly.processTemperatureSensors(payload)

        expected = [
            {"channel": 0, "id": "2885186e38190123"},
            {"channel": 2, "id": "2885186e38190789"}
        ]
        self.assertItemsEqual(expected, self.shelly.temperature_sensors)

    def test_process_temperature_sensors_removes_old_sensors(self):
        """Test that old sensors are no longer included"""
        payload = '{"0":{"hwID":"2885186e38190123","tC":20.5}, "1":{"hwID":"2885186e38190456","tC":21.5}, "2":{"hwID":"2885186e38190789","tC":22.5}}'
        self.shelly.processTemperatureSensors(payload)
        payload = '{"0":{"hwID":"2885186e38190456","tC":20.5}, "1":{"hwID":"00000000000000","tC":999}, "2":{"hwID":"2885186e38190789","tC":22.5}}'
        self.shelly.processTemperatureSensors(payload)

        expected = [
            {"channel": 0, "id": "2885186e38190456"},
            {"channel": 2, "id": "2885186e38190789"}
        ]
        self.assertItemsEqual(expected, self.shelly.temperature_sensors)

    def test_process_humidity_sensors_creates_correct_list(self):
        """Test that the list of sensors is properly created"""
        payload = '{"0":{"hwID":"2885186e38190123","hum":20.5}, "1":{"hwID":"2885186e38190456","hum":21.5}}'
        self.shelly.processHumiditySensors(payload)

        expected = [
            {"channel": 0, "id": "2885186e38190123"},
            {"channel": 1, "id": "2885186e38190456"}
        ]
        self.assertItemsEqual(expected, self.shelly.humidity_sensors)

    def test_process_humidity_sensors_ignores_invalid_sensors(self):
        """Test that the list of sensors is properly created"""
        payload = '{"0":{"hwID":"2885186e38190123","hum":20.5}, "1":{"hwID":"000000000000000","hum":999}}'
        self.shelly.processHumiditySensors(payload)

        expected = [
            {"channel": 0, "id": "2885186e38190123"}
        ]
        self.assertItemsEqual(expected, self.shelly.humidity_sensors)

    def test_process_humidity_sensors_removes_old_sensors(self):
        """Test that old sensors are no longer included"""
        payload = '{"0":{"hwID":"2885186e38190123","hum":20.5}, "1":{"hwID":"2885186e38190456","hum":21.5}}'
        self.shelly.processHumiditySensors(payload)
        payload = '{"0":{"hwID":"2885186e38190456","hum":20.5}}'
        self.shelly.processHumiditySensors(payload)

        expected = [
            {"channel": 0, "id": "2885186e38190456"}
        ]
        self.assertItemsEqual(expected, self.shelly.humidity_sensors)

    def test_handleMessage_temperature_sensors(self):
        """Test that temperature sensor messages are processed"""
        topic = 'shellies/test-shelly/ext_temperatures'
        payload = '{"0":{"hwID":"2885186e38190123","tC":20.5}, "1":{"hwID":"2885186e38190456","tC":21.5}}'
        self.shelly.handleMessage(topic, payload)

        expected = [
            {"channel": 0, "id": "2885186e38190123"},
            {"channel": 1, "id": "2885186e38190456"}
        ]
        self.assertItemsEqual(expected, self.shelly.temperature_sensors)
    
    def test_handleMessage_humidity_sensors(self):
        """Test that humidity sensor messages are processed"""
        topic = 'shellies/test-shelly/ext_humidities'
        payload = '{"0":{"hwID":"2885186e38190456","hum":20.5}}'
        self.shelly.handleMessage(topic, payload)

        expected = [
            {"channel": 0, "id": "2885186e38190456"}
        ]
        self.assertItemsEqual(expected, self.shelly.humidity_sensors)

    def test_updateBatteryLevel(self):
        """Test updating the battery level sets the state."""
        self.shelly.updateBatteryLevel(52)

        self.assertEqual(52, self.shelly.device.states['batteryLevel'])
        self.assertEqual("52%", self.shelly.device.states_meta['batteryLevel']['uiValue'])

    def test_updateBatteryLevel_triggers_low_battery(self):
        """Test that a low battery level trigger is fired."""
        trigger_any = IndigoTrigger("low-battery-any", {})
        trigger_device = IndigoTrigger("low-battery-device", {'device-id': self.device.id})

        indigo.activePlugin.triggers['1'] = trigger_any
        indigo.activePlugin.triggers['2'] = trigger_device

        self.shelly.updateBatteryLevel(10)

        self.assertTrue(trigger_any.executed)
        self.assertTrue(trigger_device.executed)

    def test_updateBatteryLevel_only_triggers_on_change(self):
        """Test that a low battery level trigger only fires when the battery level changes."""

        trigger_any = IndigoTrigger("low-battery-any", {})
        trigger_device = IndigoTrigger("low-battery-device", {'device-id': self.device.id})

        indigo.activePlugin.triggers['1'] = trigger_any
        indigo.activePlugin.triggers['2'] = trigger_device

        self.shelly.updateBatteryLevel(10)
        self.shelly.updateBatteryLevel(10)

        self.assertEqual(trigger_any.execution_count, 1)
        self.assertEqual(trigger_device.execution_count, 1)
