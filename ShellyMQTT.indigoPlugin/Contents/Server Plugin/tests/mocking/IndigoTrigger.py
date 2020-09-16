class IndigoTrigger:

    def __init__(self, pluginTypeId, pluginProps={}):
        self.pluginTypeId = pluginTypeId
        self.pluginProps = pluginProps
        self.executed = False

