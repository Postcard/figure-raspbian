

class FigureError(Exception):
    """ Base class for all exceptions in figure raspbian"""


class DevicesBusy(FigureError):
    """ Error raised when trying to access devices that are locked by another thread """


class OutOfPaperError(FigureError):
    """ Error raised when the photobooth runs out of paper """
