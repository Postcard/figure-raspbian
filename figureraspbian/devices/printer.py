# -*- coding: utf8 -*-

import re
import subprocess

from usb.core import USBError

from figureraspbian import settings
from figureraspbian.utils import timeit
from figureraspbian.exceptions import OutOfPaperError

from epson_printer import epsonprinter


DEVICE_RE = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<vendor_id>\w+):(?P<product_id>\w+)\s(?P<tag>.+)$", re.I)

# Identify Epson printers in usb devices
EPSON_VENDOR_ID = '04b8'

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


class EpsonPrinter(object):

    def __init__(self):
        vendor_id = '0x%s' % EPSON_VENDOR_ID
        product_id = '0x%s' % get_product_id(EPSON_VENDOR_ID)
        self.printer = epsonprinter.EpsonPrinter(int(vendor_id, 16), int(product_id, 16))
        self.printer.set_print_speed(2)

    @timeit
    def print_ticket(self, ticket_data):
        try:
            self.printer.write(ticket_data)
            self.printer.linefeed(settings.LINE_FEED_COUNT)
            self.printer.cut()
        except USBError:
            # best guess is that we are out out of paper
            raise OutOfPaperError()
