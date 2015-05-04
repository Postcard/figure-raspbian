# -*- coding: utf8 -*-

import os
from datetime import datetime
import pytz
import time

from PIL import Image

from .. import settings
from . import light


try:
    import gphoto2 as gp
except ImportError:
    print("Could not import gphoto2")


class Camera(object):
    """ Camera interface """

    def capture(self):
        raise NotImplementedError


class DSLRCamera(Camera):
    """
    Digital Single Lens Reflex camera
    It uses gphoto2 to communicate with the digital camera:
    http://www.gphoto.org/proj/libgphoto2/
    Lists of supported cameras:
    http://www.gphoto.org/proj/libgphoto2/support.php
    """

    def __init__(self):
        self.context = gp.Context()
        self.camera = gp.Camera()
        self.light = light.LEDPanelLight()

    def capture(self, installation):
        self.camera.init(self.context)
        try:
            if settings.FLASH_ON:
                self.light.flash_on()
                # Let the time for the camera to adjust
                time.sleep(2)

            # Capture image
            error, filepath = gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, self.context)

            if settings.FLASH_ON:
                self.light.flash_off()

            # Create a CameraFile from the FilePath
            error, camerafile = gp.gp_camera_file_get(self.camera, filepath.folder, filepath.name, gp.GP_FILE_TYPE_NORMAL, self.context)
            # Create file path on the RaspberryPi
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            datetime.now(pytz.timezone(settings.TIMEZONE))
            basename = "{installation}_{now}.jpg".format(installation=installation, now=now)
            path = os.path.join(settings.SNAPSHOT_DIR, basename)
            # Save the file to the Raspberry Pi
            camerafile.save(path)
        finally:
            self.camera.exit(self.context)
        im = Image.open(path)
        if settings.CAMERA_TYPE == 'NIKON':
            w, h = im.size
            left = (w - h) / 2
            top = 0
            right = w - left
            bottom = h
            im = im.crop((left, top, right, bottom))
        elif settings.CAMERA_TYPE == 'CANON':
            im = im.rotate(90)
            w, h = im.size
            left = 0
            top = (h - w) / 2
            right = w
            bottom = h - top
            im = im.crop((left, top, right, bottom))
        else:
            raise Exception("Unknown camera type")
        im = im.resize((1024, 1024), Image.ANTIALIAS)
        im.save(path)
        return path


class DummyCamera(Camera):
    """ Dummy camera used for tests purposes. It prints a message to the console """

    def __init__(self):
        pass

    def capture(self):
        print "Capture snapshot"
        return os.path.join(settings.FIGURE_DIR, 'resources/2_20150331.jpg')


