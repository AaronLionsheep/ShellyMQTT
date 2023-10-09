# coding=utf-8
import indigo
import logging


class ShellyLogger:
    """
    A wrapper for the logger class.
    This is ued to mute info and debug logging when a device has been marked as muted.
    """

    def __init__(self, shelly):
        self.logger = logging.getLogger("Plugin.ShellyMQTT")
        self.shelly = shelly

    def __getattr__(self, method):
        def handler(*args, **kwargs):
            # Only allow the device to log if:
            # a) The device is not muted
            # or
            # b) The method is not in the list of logging methods that should be muted
            if not self.shelly.isMuted() or method not in self.shelly.getMutedLoggingMethods():
                getattr(self.logger, method)(*args, **kwargs)

        return handler
