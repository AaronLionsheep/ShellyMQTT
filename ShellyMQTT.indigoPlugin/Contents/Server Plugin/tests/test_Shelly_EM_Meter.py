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
from Devices.Sensors.Shelly_EM_Meter import Shelly_EM_Meter


class Test_Shelly_EM_Meter(unittest.TestCase):

    def setUp(self):
        indigo.__init__()
        self.device = IndigoDevice(id=123456, name="New Device")
        self.shelly = Shelly_EM_Meter(self.device)
        logging.getLogger('Plugin.ShellyMQTT').addHandler(logging.NullHandler())

        self.device.pluginProps['address'] = "shellies/shelly-em-meter-test"

        self.device.updateStateOnServer("ip-address", None)
        self.device.updateStateOnServer("mac-address", None)
        self.device.updateStateOnServer("online", False)
        self.device.updateStateOnServer("curEnergyLevel", 0)
        self.device.updateStateOnServer("accumEnergyTotal", 0)
        self.device.updateStateOnServer("power", 0)

    def test_getSubscriptions_no_address(self):
        """Test getting subscriptions with no address defined."""
        self.device.pluginProps['address'] = None
        self.assertListEqual([], self.shelly.getSubscriptions())

    def test_getSubscriptions(self):
        """Test getting subscriptions with a defined address."""
        topics = [
            "shellies/announce",
            "shellies/shelly-em-meter-test/online",
            "shellies/shelly-em-meter-test/emeter/0/energy",
            "shellies/shelly-em-meter-test/emeter/0/returned_energy",
            "shellies/shelly-em-meter-test/emeter/0/power",
            "shellies/shelly-em-meter-test/emeter/0/reactive_power",
            "shellies/shelly-em-meter-test/emeter/0/voltage"
        ]
        self.assertListEqual(topics, self.shelly.getSubscriptions())

    def test_handleMessage_power(self):
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/power", "0")
        self.assertEqual(0, self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("0.00 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/power", "101.123")
        self.assertEqual(101.123, self.shelly.device.states['curEnergyLevel'])
        self.assertEqual("101.12 W", self.shelly.device.states_meta['curEnergyLevel']['uiValue'])

    def test_handleMessage_power_invalid(self):
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/power", "Aa"))

    def test_handleMessage_reactive_power(self):
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/reactive_power", "0")
        self.assertEqual(0, self.shelly.device.states['power-reactive'])
        self.assertEqual("0.00 W", self.shelly.device.states_meta['power-reactive']['uiValue'])

        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/reactive_power", "50.632")
        self.assertEqual(50.632, self.shelly.device.states['power-reactive'])
        self.assertEqual("50.63 W", self.shelly.device.states_meta['power-reactive']['uiValue'])

    def test_handleMessage_reactive_power_invalid(self):
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/reactive_power", "Aa"))

    def test_handleMessage_energy(self):
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/energy", "0")
        self.assertAlmostEqual(0.0000, self.shelly.device.states['energy-consumed'], 4)

        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/energy", "50")
        self.assertAlmostEqual(0.0008, self.shelly.device.states['energy-consumed'], 4)

    def test_handleMessage_energy_invalid(self):
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/energy", "Aa"))

    def test_handleMessage_returned_energy(self):
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/returned_energy", "0")
        self.assertAlmostEqual(0.0000, self.shelly.device.states['energy-returned'], 4)

        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/returned_energy", "50")
        self.assertAlmostEqual(0.0008, self.shelly.device.states['energy-returned'], 4)

    def test_handleMessage_returned_energy_invalid(self):
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/returned_energy", "Aa"))

    def test_handleMessage_voltage(self):
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/voltage", "120.12")
        self.assertAlmostEqual(120.12, self.shelly.device.states['voltage'], 2)
        self.assertEqual("120.1 V", self.shelly.device.states_meta['voltage']['uiValue'])

        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/voltage", "122.87")
        self.assertAlmostEqual(122.87, self.shelly.device.states['voltage'], 2)
        self.assertEqual("122.9 V", self.shelly.device.states_meta['voltage']['uiValue'])

    def test_handleMessage_voltage_invalid(self):
        self.assertRaises(ValueError, self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/voltage", "Aa"))

    def test_handleMessage_announce(self):
        announcement = '{"id": "shelly-em-meter-test", "mac": "aa:bb:cc:ee", "ip": "192.168.1.101", "fw_ver": "0.1.0", "new_fw": false}'
        self.shelly.handleMessage("shellies/announce", announcement)

        self.assertEqual("aa:bb:cc:ee", self.shelly.device.states['mac-address'])
        self.assertEqual("192.168.1.101", self.shelly.getIpAddress())
        self.assertEqual("0.1.0", self.shelly.getFirmware())
        self.assertFalse(self.shelly.updateAvailable())

    def test_handleMessage_online_true(self):
        self.assertFalse(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-em-meter-test/online", "true")
        self.assertTrue(self.shelly.device.states['online'])

    def test_handleMessage_online_false(self):
        self.shelly.device.states['online'] = True
        self.assertTrue(self.shelly.device.states['online'])
        self.shelly.handleMessage("shellies/shelly-em-meter-test/online", "false")
        self.assertFalse(self.shelly.device.states['online'])

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_status_request(self, publish):
        statusRequest = IndigoAction(indigo.kDeviceAction.RequestStatus)
        self.shelly.handleAction(statusRequest)
        publish.assert_called_with("shellies/shelly-em-meter-test/command", "update")

    def test_handleAction_reset_energy(self):
        self.shelly.updateEnergy(30)
        self.assertAlmostEqual(0.0005, self.shelly.device.states['accumEnergyTotal'], 4)
        resetEnergy = IndigoAction(indigo.kUniversalAction.EnergyReset)
        self.shelly.handleAction(resetEnergy)
        self.assertAlmostEqual(0.0000, self.shelly.device.states['accumEnergyTotal'], 4)

    @patch('Devices.Shelly.Shelly.publish')
    def test_handleAction_update_energy(self, publish):
        updateEnergy = IndigoAction(indigo.kUniversalAction.EnergyUpdate)
        self.shelly.handleAction(updateEnergy)
        publish.assert_called_with("shellies/shelly-em-meter-test/command", "update")

    def test_updateEnergy_net_positive(self):
        self.shelly.device.pluginProps['energy-display'] = "net"
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/returned_energy", "20")
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/energy", "50")
        # net of 30 consumed
        self.assertAlmostEqual(0.0005, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("0.0005 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])

    def test_updateEnergy_net_negative(self):
        self.shelly.device.pluginProps['energy-display'] = "net"
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/returned_energy", "50")
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/energy", "20")
        # net of 30 returned
        self.assertAlmostEqual(-0.0005, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("-0.0005 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])

    def test_updateEnergy_consumed(self):
        self.shelly.device.pluginProps['energy-display'] = "consumed"
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/returned_energy", "50")
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/energy", "20")
        # 50 returned, 20 consumed
        self.assertAlmostEqual(0.0003, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("0.0003 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])

    def test_updateEnergy_returned(self):
        self.shelly.device.pluginProps['energy-display'] = "returned"
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/returned_energy", "50")
        self.shelly.handleMessage("shellies/shelly-em-meter-test/emeter/0/energy", "20")
        # 50 returned, 20 consumed
        self.assertAlmostEqual(-0.0008, self.shelly.device.states['accumEnergyTotal'], 4)
        self.assertEqual("-0.0008 kWh", self.shelly.device.states_meta['accumEnergyTotal']['uiValue'])

    def test_buildEnergyUIValue_4_decimals(self):
        self.assertEqual("0.0080 kWh", self.shelly.buildEnergyUIValue(0.008))

    def test_buildEnergyUIValue_3_decimals(self):
        self.assertEqual("0.123 kWh", self.shelly.buildEnergyUIValue(0.1234))

    def test_buildEnergyUIValue_2_decimals(self):
        self.assertEqual("1.28 kWh", self.shelly.buildEnergyUIValue(1.28344))

    def test_buildEnergyUIValue_1_decimal(self):
        self.assertEqual("12.2 kWh", self.shelly.buildEnergyUIValue(12.23982))

    def test_updateStateImage_on(self):
        self.shelly.device.states['online'] = True
        self.shelly.updateStateImage()
        self.assertEquals(indigo.kStateImageSel.EnergyMeterOn, self.shelly.device.image)

    def test_updateStateImage_off(self):
        self.shelly.device.states['online'] = False
        self.shelly.updateStateImage()
        self.assertEquals(indigo.kStateImageSel.EnergyMeterOff, self.shelly.device.image)
