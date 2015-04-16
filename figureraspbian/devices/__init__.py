# -*- coding: utf8 -*-

from . import camera, output, printer
from .. import settings

if settings.ENVIRONMENT is 'development':
    CAMERA = camera.DummyCamera()
    OUTPUT = output.DummyOutput()
    PRINTER = printer.DummyPrinter()
else:
    CAMERA = camera.DSLRCamera()
    OUTPUT = output.PiFaceOutput()
    PRINTER = printer.EpsonPrinter()