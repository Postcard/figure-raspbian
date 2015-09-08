# -*- coding: utf8 -*-

import os
from datetime import datetime
import pytz
import time
import io

from PIL import Image

from .. import settings


try:
    import gphoto2 as gp
except ImportError:
    print("Could not import gphoto2")


class Camera(object):
    """ Camera interface """

    def capture(self):
        raise NotImplementedError


EOS_1200D_CONFIG = {
    'capturetarget': 1,
    'focusmode': 3,
    'autopoweroff': 0,
    'imageformat': 6,
    'aperture': settings.APERTURE,
    'shutterspeed': settings.SHUTTER_SPEED,
    'iso': settings.ISO}


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

        # Camera specific configuration
        if settings.CAMERA_MODEL == 'CANON_1200D':
            try:
                self.camera.init(self.context)
                error, config = gp.gp_camera_get_config(self.camera, self.context)
                for param, choice in EOS_1200D_CONFIG.iteritems():
                    error, widget = gp.gp_widget_get_child_by_name(config, param)
                    error, value = gp.gp_widget_get_choice(widget, choice)
                    gp.gp_widget_set_value(widget, value)
                gp.gp_camera_set_config(self.camera, config, self.context)
            finally:
                self.camera.exit(self.context)

    def capture(self, installation):
        self.camera.init(self.context)
        try:
            if settings.FLASH_ON:
                self.light.flash_on()
                # Let the time for the camera to adjust
                time.sleep(1)

            # Capture image
            error, camera_path = gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, self.context)
            folder = camera_path.folder
            name = camera_path.name

            if settings.FLASH_ON:
                self.light.flash_off()

            date = datetime.now(pytz.timezone(settings.TIMEZONE))

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
            if settings.ROTATE:
                snapshot = snapshot.rotate(90)

            # resize in place using the fastest algorithm, ie NEAREST
            small = snapshot.resize((512, 512))

            # Create file path on the RaspberryPi
            basename = "{installation}_{date}.jpg".format(installation=installation, date=date.strftime('%Y%m%d%H%M%S'))
            raspberry_path = os.path.join(settings.MEDIA_ROOT, 'snapshots', basename)

            small.save(raspberry_path)

            return raspberry_path, snapshot, date, camera_path

        finally:
            if 'camera_file' in locals():
                del camera_file
            if 'file_data' in locals():
                del file_data
            self.camera.exit(self.context)

    def delete(self, path):
        self.camera.init(self.context)
        try:
            folder = path.folder
            name = path.name
            gp.gp_camera_file_delete(self.camera, folder, name, self.context)
        finally:
            self.camera.exit(self.context)



class DummyCamera(Camera):
    """ Dummy camera used for tests purposes. It prints a message to the console """

    def __init__(self):
        pass

    def capture(self):
        print "Capture snapshot"
        return os.path.join(settings.FIGURE_DIR, 'resources/2_20150331.jpg')


