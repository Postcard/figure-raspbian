

class FigureError(Exception):
    """ Base class for all exceptions in figure raspbian"""


class PrinterNotFoundError(FigureError):

    def __init__(self):
        super(PrinterNotFoundError, self).__init__("Printer not found in usb devices list")


class PrinterModelNotRecognizedError(FigureError):
    """ Error raised when no compatible printer was found in the list of usb devices """

    def __init__(self, device):
        msg = "Unknown model %s (product id %s)" % (device['tag'], device['product_id'])
        super(PrinterModelNotRecognizedError, self).__init__(msg)


class DevicesBusy(FigureError):
    """ Error raised when trying to access devices that are locked by another thread """


class OutOfPaperError(FigureError):
    """ Error raised when the photobooth runs out of paper """


class InvalidIOInterfaceError(FigureError):
    """ Error raised when the IO interface specified is not valid """


class TimeoutWaitingForFileAdded(FigureError):
    """ Error raised when no picture is received from the camera after a certain amount of time """
