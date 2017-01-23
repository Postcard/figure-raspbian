# -*- coding: utf8 -*-

from figureraspbian.devices.printer import Printer
from figureraspbian.devices.camera import Camera


class TestPrinter:

    def test_print_image(self):
        printer = Printer.factory()
        printer.print_image_from_file('./test_ticket.png')


class TestCamera:

    def test_focus(self):
        camera = Camera()
        camera.focus()
