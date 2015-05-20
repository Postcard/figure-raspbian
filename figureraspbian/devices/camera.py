# -*- coding: utf8 -*-

import os
from datetime import datetime
import pytz
import time
import io

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
                time.sleep(1)

            # Capture image
            error, filepath = gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, self.context)
            folder, name = os.path.split(filepath)

            if settings.FLASH_ON:
                self.light.flash_off()

            # Get date
            error, info = gp.gp_camera_file_get_info(
                self.camera,
                folder,
                name,
                self.context)
            date = datetime.fromtimestamp(info.file.mtime)
            timezone = pytz.timezone(settings.TIMEZONE)
            timezone.localize(date)

            # Get snapshot file
            error, camera_file = gp.gp_camera_file_get(
                self.camera,
                folder,
                name,
                gp.GP_FILE_TYPE_NORMAL,
                self.context)

            error, file_data = gp.gp_file_get_data_and_size(camera_file)

            # Crop and rotate snapshot
            snapshot = Image.open(io.BytesIO(file_data))
            w, h = snapshot.size
            left = (w - h) / 2
            top = 0
            right = w - left
            bottom = h
            snapshot = snapshot.crop((left, top, right, bottom))
            if settings.CAMERA_TYPE == 'CANON':
                snapshot = snapshot.rotate(90)

            # resize in place using the fastest algorithm, ie NEAREST
            small = snapshot.resize((512, 512))

            # Create file path on the RaspberryPi
            basename = "{installation}_{date}.jpg".format(installation=installation, date=date.strftime('%Y%m%d%H%M%S'))
            path = os.path.join(settings.MEDIA_ROOT, 'snapshots', basename)

            small.save(path)

            return path, snapshot, date

        finally:
            del camera_file, file_data
            self.camera.exit(self.context)


class DummyCamera(Camera):
    """ Dummy camera used for tests purposes. It prints a message to the console """

    def __init__(self):
        pass

    def capture(self):
        print "Capture snapshot"
        return os.path.join(settings.FIGURE_DIR, 'resources/2_20150331.jpg')


