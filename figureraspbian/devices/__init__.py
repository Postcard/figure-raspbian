# -*- coding: utf8 -*-

from . import camera, printer
from .. import settings

if settings.ENVIRONMENT is 'development':
    CAMERA = camera.DummyCamera()
    PRINTER = printer.DummyPrinter()
else:
    CAMERA = camera.DSLRCamera()
    PRINTER = printer.EpsonPrinter()