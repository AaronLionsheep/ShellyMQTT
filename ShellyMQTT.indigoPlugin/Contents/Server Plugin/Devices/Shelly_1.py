import indigo
from Shelly import Shelly


class Shelly_1(Shelly):
    def __init__(self, device):
        Shelly.__init__(self, device)

    def getSubscriptions(self):
        address = self.getAddress()
        if address is None:
            return []

        return [
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
            if payload == '0':
                self.device.updateStateOnServer(key="sw-input", value=False)
            elif payload == '1':
                self.device.updateStateOnServer(key="sw-input", value=True)
        elif topic == "{}/longpush/{}".format(self.getAddress(), self.getChannel()):
            if payload == '0':
                self.device.updateStateOnServer(key="longpush", value=False)
            elif payload == '1':
                self.device.updateStateOnServer(key="longpush", value=True)

    def handleAction(self, action):
        if action == indigo.kDeviceAction.TurnOn:
            self.turnOn()
            self.publish("{}/relay/{}/command".format(self.getAddress(), self.getChannel()), "on")
        elif action == indigo.kDeviceAction.TurnOff:
            self.turnOff()
            self.publish("{}/relay/{}/command".format(self.getAddress(), self.getChannel()), "off")

    def turnOn(self):
        self.device.updateStateOnServer(key='onOffState', value=True)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.PowerOn)

    def turnOff(self):
        self.device.updateStateOnServer(key='onOffState', value=False)
        self.device.updateStateImageOnServer(indigo.kStateImageSel.PowerOff)

    def getChannel(self):
        return self.device.pluginProps.get('channel', 0)
