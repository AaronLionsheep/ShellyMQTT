import indigo
from Shelly import Shelly


class Shelly_1(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []
        else:
            return [
                "shellies/announce",
                "{}/online".format(address),
                "{}/relay/{}".format(address, self.getChannel()),
                "{}/input/{}".format(address, self.getChannel()),
                "{}/longpush/{}".format(address, self.getChannel())
            ]

    def handleMessage(self, topic, payload):
        if topic == "{}/relay/{}".format(self.getAddress(), self.getChannel()):
            if payload == "on":
                self.turnOn()
            elif payload == "off":
                self.turnOff()
        elif topic == "{}/input/{}".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer(key="sw-input", value=(payload == '1'))
        elif topic == "{}/longpush/{}".format(self.getAddress(), self.getChannel()):
            self.device.updateStateOnServer(key="longpush", value=(payload == '1'))
        else:
            Shelly.handleMessage(self, topic, payload)

    def handleAction(self, action):
        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            self.turnOn()
            self.publish("{}/relay/{}/command".format(self.getAddress(), self.getChannel()), "on")
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            self.turnOff()
            self.publish("{}/relay/{}/command".format(self.getAddress(), self.getChannel()), "off")
        elif action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.sendStatusRequestCommand()
