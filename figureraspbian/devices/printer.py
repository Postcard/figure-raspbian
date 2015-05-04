# -*- coding: utf8 -*-

import re
import subprocess


try:
    from epson_printer import epsonprinter
except ImportError:
    print("Could not import epsonprinter")



class Printer(object):
    """ Printer interface """

    def print_ticket(self):
        raise NotImplementedError


DEVICE_RE = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<vendor_id>\w+):(?P<product_id>\w+)\s(?P<tag>.+)$", re.I)


def get_product_id(vendor_id):
    df = subprocess.check_output("lsusb", shell=True)
    # parse all usb devices
    devices = []
    for i in df.split('\n'):
        if i:
            info = DEVICE_RE.match(i)
            if info:
                dinfo = info.groupdict()
                dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
                devices.append(dinfo)

    # Try finding an Epson printer
    printer = next(device for device in devices if device['vendor_id'] == vendor_id)
    if not printer:
        raise Exception("No EPSON Printer detected")
    return printer['product_id']

# Identify Epson printers in usb devices
EPSON_VENDOR_ID = '04b8'

class EpsonPrinter(Printer):

    def __init__(self):
        vendor_id = '0x%s' % EPSON_VENDOR_ID
        product_id = '0x%s' % get_product_id(EPSON_VENDOR_ID)
        self.printer = epsonprinter.EpsonPrinter(int(vendor_id, 16), int(product_id, 16))
        self.printer.set_print_speed(4)

    def print_ticket(self, ticket):
        self.printer.print_image_from_file(ticket)
        self.printer.linefeed(4)
        self.printer.cut()


class DummyPrinter(Printer):

    def __init__(self):
        pass

    def print_ticket(self, ticket):
        print("Print ticket")