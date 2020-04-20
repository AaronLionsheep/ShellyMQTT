class IndigoDevice:

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.states = {}
        self.pluginProps = {}
        self.image = None

    def updateStateOnServer(self, key, value, uiValue=None, decimalPlaces=0):
        self.states[key] = {'value': value, 'uiValue': uiValue, 'decimalPlaces': decimalPlaces}

    def replacePluginPropsOnServer(self, pluginProps):
        self.pluginProps = pluginProps

    def updateStateImageOnServer(self, image):
        self.image = image