# -*- coding: utf8 -*-

from . import camera, output, printer, light
from .. import settings

if settings.ENVIRONMENT is 'development':
    CAMERA = camera.DummyCamera()
    OUTPUT = output.DummyOutput()
    PRINTER = printer.DummyPrinter()
    LIGHT = light.DummyLight()
else:
    CAMERA = camera.DSLRCamera()
    OUTPUT = output.PiFaceOutput()
    PRINTER = printer.EpsonPrinter()
    LIGHT = light.LEDPanelLight()