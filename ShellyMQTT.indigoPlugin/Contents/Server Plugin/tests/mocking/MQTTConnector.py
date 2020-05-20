class MQTTConnector:

    def __init__(self):
        self.subscriptions = {}
        self.messages_in = {}
        self.messages_out = {}
        self.enabled = True

    def isEnabled(self):
        return self.enabled

    def executeAction(self, action, deviceId=None, props={}, waitUntilDone=False):
        if action == "add_subscription":
            if deviceId not in self.subscriptions.keys():
                self.subscriptions[deviceId] = []

            self.subscriptions[deviceId].append(props)
        elif action == "publish":
            if deviceId not in self.messages_out.keys():
                self.messages_out[deviceId] = []

            self.messages_out[deviceId].append(props)

    def getBrokerSubscriptions(self, deviceId):
        return self.subscriptions.get(deviceId, [])

    def getMessagesOut(self, deviceId):
        return self.messages_out.get(deviceId, [])
