from MQTTConnector import MQTTConnector
from IndigoPlugin import ShellyPlugin


class Indigo:

    def __init__(self):
        self.server = IndigoServer()
        self.kStateImageSel = StateImages()
        self.kDeviceAction = DeviceActions()
        self.kUniversalAction = UniversalActions()
        self.kThermostatAction = ThermostatActions()
        self.kHvacMode = HVACMode()
        self.activePlugin = ShellyPlugin()
        self.device = IndigoDevice()
        self.trigger = TriggerExecutor()

    def Dict(self):
        return {}


class IndigoServer:

    def __init__(self):
        self.plugins = {
            "com.flyingdiver.indigoplugin.mqtt": MQTTConnector()
        }

    def getPlugin(self, identifier):
        return self.plugins.get(identifier, None)


class IndigoDevice:

    def turnOn(self, deviceId):
        pass

    def turnOff(self, deviceId):
        pass


class StateImages:

    def __init__(self):
        self.PowerOn = "PowerOn"
        self.PowerOff = "PowerOff"
        self.DimmerOn = "DimmerOn"
        self.DimmerOff = "DimmerOff"
        self.TemperatureSensor = "TemperatureSensor"
        self.TemperatureSensorOn = "TemperatureSensorOn"
        self.MotionSensorTripped = "MotionSensorTripped"
        self.MotionSensor = "MotionSensor"
        self.SensorTripped = "SensorTripped"
        self.SensorOn = "SensorOn"
        self.SensorOff = "SensorOff"
        self.DoorSensorOpened = "DoorSensorOpened"
        self.DoorSensorClosed = "DoorSensorClosed"
        self.WindowSensorOpened = "WindowSensorOpened"
        self.WindowSensorClosed = "WindowSensorClosed"
        self.EnergyMeterOn = "EnergyMeterOn"
        self.EnergyMeterOff = "EnergyMeterOff"
        self.HvacHeating = "HvacHeating"


class HVACMode:

    def __init__(self):
        self.Cool = "Cool"
        self.HeatCool = "HeatCool"
        self.Heat = "Heat"
        self.Off = "Off"
        self.ProgramHeatCool = "ProgramHeatCool"
        self.ProgramCool = "ProgramCool"
        self.ProgramHeat = "ProgramHeat"


class DeviceActions:

    def __init__(self):
        self.TurnOn = "TurnOn"
        self.TurnOff = "TurnOff"
        self.Toggle = "Toggle"
        self.RequestStatus = "RequestStatus"
        self.SetBrightness = "SetBrightness"
        self.BrightenBy = "BrightenBy"
        self.DimBy = "DimBy"
        self.SetColorLevels = "SetColorLevels"


class UniversalActions:

    def __init__(self):
        self.EnergyReset = "EnergyReset"
        self.EnergyUpdate = "EnergyUpdate"


class ThermostatActions:

    def __init__(self):
        self.DecreaseCoolSetpoint = "DecreaseCoolSetpoint"
        self.DecreaseHeatSetpoint = "DecreaseHeatSetpoint"
        self.IncreaseCoolSetpoint = "IncreaseCoolSetpoint"
        self.IncreaseHeatSetpoint = "IncreaseHeatSetpoint"
        self.SetCoolSetpoint = "SetCoolSetpoint"
        self.SetFanMode = "SetFanMode"
        self.SetHeatSetpoint = "SetHeatSetpoint"
        self.SetHvacMode = "SetHvacMode"
        self.RequestStatusAll = "RequestStatusAll"
        self.RequestMode = "RequestMode"
        self.RequestEquipmentState = "RequestEquipmentState"
        self.RequestTemperatures = "RequestTemperatures"
        self.RequestHumidities = "RequestHumidities"
        self.RequestDeadbands = "RequestDeadbands"
        self.RequestSetpoints = "RequestSetpoints"


class TriggerExecutor:

    def __init__(self):
        pass

    @staticmethod
    def execute(trigger):
        trigger.executed = True
        trigger.execution_count += 1
