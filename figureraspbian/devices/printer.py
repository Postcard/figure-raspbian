# -*- coding: utf8 -*-

import subprocess
import os
from os.path import join
from io import BytesIO

import logging

from usb.core import USBError

from epson_printer import epsonprinter
from custom_printer import printers as customprinters
from custom_printer import utils as custom_printer_utils
from PIL import Image

import settings
from utils import timeit, get_usb_devices, add_margin, resize_preserve_ratio
from exceptions import OutOfPaperError, PrinterNotFoundError, PrinterModelNotRecognizedError
import constants


logger = logging.getLogger(__name__)


class Printer(object):
    """ Base class for all printers """

    def print_image(self, image):
        raise NotImplementedError()

    def print_image_from_file(self, file_path):
        with open(file_path, "rb") as image_file:
            self.print_image(image_file.read())

    def paper_present(self):
        raise NotImplemented()

    @staticmethod
    def factory():
        def _factory():
            """ factory method to create different types of printers based on the output of lsusb"""
            devices = get_usb_devices()
            # Try finding an EPSON printer
            generator = (device for device in devices if device['vendor_id'] == constants.EPSON_VENDOR_ID)
            epson_printer_device = next(generator, None)
            if epson_printer_device:
                product_id = epson_printer_device['product_id']
                if product_id == constants.TMT20_PRODUCT_ID:
                    return EpsonTMT20()
                if product_id == constants.TMT20II_PRODUCT_ID:
                    return EpsonTMT20II()
                else:
                    raise PrinterModelNotRecognizedError(epson_printer_device)
            generator = (device for device in devices if device['vendor_id'] == constants.CUSTOM_VENDOR_ID)
            custom_printer_device = next(generator, None)
            if custom_printer_device:
                product_id = custom_printer_device['product_id']
                if product_id == constants.VKP80III_PRODUCT_ID:
                    return VKP80III()
                else:
                    raise PrinterModelNotRecognizedError(custom_printer_device)
            raise PrinterNotFoundError()

        try:
            return _factory()
        except Exception as e:
            logger.error(e)


class EpsonPrinter(Printer):

    def __init__(self, *args, **kwargs):
        self.max_width = 576
        super(EpsonPrinter, self).__init__(*args, **kwargs)

    def configure(self):
        self.printer.set_print_speed(2)

    def image_to_raster(self, ticket):
        ticket_path = join(settings.RAMDISK_ROOT, 'ticket.png')
        ticket.save(ticket_path, "PNG", quality=100)
        # TODO make png2pos support passing base64 file argument
        speed_arg = '-s%s' % settings.PRINTER_SPEED
        args = ['png2pos', '-r', speed_arg, '-aC', ticket_path]
        my_env = os.environ.copy()
        my_env['PNG2POS_PRINTER_MAX_WIDTH'] = str(self.max_width)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, env=my_env)
        pos_data, err = p.communicate()
        if err:
            raise err
        return pos_data

    def prepare_image(self, image):
        im = Image.open(BytesIO(image))
        im = resize_preserve_ratio(im, new_width=self.max_width)
        if im.mode is not '1':
            im = im.convert('1')
        buf = BytesIO()
        im.save(buf, 'PNG')
        im = buf.getvalue()
        buf.close()
        return im

    @timeit
    def print_image(self, image):
        im = Image.open(BytesIO(image))
        raster_data = self.image_to_raster(im)
        try:
            self.printer.write(raster_data)
            self.printer.linefeed(settings.LINE_FEED_COUNT)
            self.printer.cut()
            _, h = im.size
            return h
        except USBError:
            # best guess is that we are out out of paper
            raise OutOfPaperError()

    def paper_present(self):
        # TODO make this work
        # return self.printer.paper_present()
        return True


class EpsonTMT20(EpsonPrinter):

    def __init__(self, *args, **kwargs):
        super(EpsonTMT20, self).__init__(*args, **kwargs)
        product_id = '0x%s' % constants.TMT20_PRODUCT_ID
        self.printer = epsonprinter.EpsonPrinter(int(product_id, 16))
        self.configure()


class EpsonTMT20II(EpsonPrinter):

    def __init__(self, *args, **kwargs):
        super(EpsonTMT20II, self).__init__(*args, **kwargs)
        product_id = '0x%s' % constants.TMT20II_PRODUCT_ID
        self.printer = epsonprinter.EpsonPrinter(int(product_id, 16))
        self.configure()


class VKP80III(Printer):

    def __init__(self, *args, **kwargs):
        super(VKP80III, self).__init__(*args, **kwargs)
        self.printer = customprinters.VKP80III()
        self.max_width = 640
        try:
            self.configure()
        except USBError:
            pass

    def configure(self):
        self.printer.set_print_speed(0)

    def image_to_raster(self, image):
        return custom_printer_utils.image_to_raster(image)

    def prepare_image(self, image):
        im = Image.open(BytesIO(image))
        if im.mode != '1':
            im = im.convert('1')
        horizontal_margin = int((self.max_width - im.size[0]) / 2)
        border = (horizontal_margin, 55, horizontal_margin, 0)
        im = add_margin(im, border)
        buf = BytesIO()
        im.save(buf, 'PNG')
        im = buf.getvalue()
        buf.close()
        return im

    @timeit
    def print_image(self, image):
        im = Image.open(BytesIO(image))
        im = im.rotate(180)
        with open('/figureraspbian/static/img.png', 'wb') as f:
            logger.info("Image written to static folder")
            buf = BytesIO()
            im.save(buf, 'PNG')
            f.write(buf.getvalue())
        raster_data = custom_printer_utils.image_to_raster(im)
        xH, xL = custom_printer_utils.to_base_256(self.max_width / 8)
        yH, yL = custom_printer_utils.to_base_256(im.size[1])
        try:
            self.printer.print_raster_image(0, xL, xH, yL, yH, raster_data)
            self.printer.present_paper(23, 1, 69, 0)
            (_, h) = im.size
            return h
        except USBError:
            raise OutOfPaperError()

    @timeit
    def paper_present(self):
        return self.printer.paper_present()
