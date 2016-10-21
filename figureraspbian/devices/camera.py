# -*- coding: utf8 -*-

import os
import io
import time

from PIL import Image
import gphoto2 as gp
import piexif
from pifacedigitalio import PiFaceDigital

from figureraspbian import settings
from figureraspbian.utils import timeit


EOS_1200D_CONFIG = {
    'capturetarget': 1,
    'focusmode': 3,
    'imageformat': 6,
    'aperture': settings.APERTURE,
    'shutterspeed': settings.SHUTTER_SPEED,
    'iso': settings.ISO}


class RemoteReleaseConnector:
    """
    Represents a remote release connector. http://www.doc-diy.net/photo/remote_pinout/
    In our case the cable is just a 2.5mm jack
    """

    def __init__(self, pin=0):
        self.pifacedigital = PiFaceDigital()
        self.pin = pin

    def trigger(self):
        self.pifacedigital.output_pins[0].turn_on()


class DSLRCamera:
    """
    Digital Single Lens Reflex camera
    It uses gphoto2 to communicate with the digital camera:
    http://www.gphoto.org/proj/libgphoto2/
    Lists of supported cameras:
    http://www.gphoto.org/proj/libgphoto2/support.php
    """

    def __init__(self):
        self.camera = gp.check_result(gp.gp_camera_new())

        try:
            context = gp.gp_context_new()
            gp.check_result(gp.gp_camera_init(self.camera, context))
            config = gp.check_result(gp.gp_camera_get_config(self.camera, context))
            for param, choice in EOS_1200D_CONFIG.iteritems():
                widget = gp.check_result(gp.gp_widget_get_child_by_name(config, param))
                value = gp.check_result(gp.gp_widget_get_choice(widget, choice))
                gp.gp_widget_set_value(widget, value)
            gp.gp_camera_set_config(self.camera, config, context)
        finally:
            gp.check_result(gp.gp_camera_exit(self.camera, context))

        # Clear camera space
        self.clear_space()

        if settings.CAMERA_TRIGGER_TYPE == 'REMOTE_RELEASE_CONNECTOR':
            self.remote_release_connector = RemoteReleaseConnector(pin=settings.REMOTE_RELEASE_CONNECTOR_PIN)


    @timeit
    def capture(self):
        if settings.CAMERA_TRIGGER_TYPE == 'REMOTE_RELEASE_CONNECTOR':
            return self.capture_remote_release_connector()
        else:
            return self.capture_tethered()

    def capture_remote_release_connector(self):
        """ Use a remote release cable to trigger the camera. Download the picture with gphoto2 """
        if not self.remote_release_connector:
            pass

        try:
            self.remote_release_connector.trigger()
            time.sleep(1)
            context = gp.gp_context_new()
            gp.check_result(gp.gp_camera_init(self.camera, context))
            files = self.list_files(self.camera, context)
            files.sort()
            files.reverse()

            picture_path = files[0]
            folder = os.path.dirname(picture_path)
            name = os.path.basename(picture_path)

            # Get picture file
            error, camera_file = gp.gp_camera_file_get(
                self.camera,
                folder,
                name,
                gp.GP_FILE_TYPE_NORMAL,
                context)

            file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

            # Crop picture to be a square
            picture = Image.open(io.BytesIO(file_data))
            exif_dict = piexif.load(picture.info["exif"])
            w, h = picture.size
            left = (w - h) / 2
            top = 0
            right = w - left
            bottom = h
            picture = picture.crop((left, top, right, bottom))
            w, h = picture.size
            exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = w
            exif_bytes = piexif.dump(exif_dict)
            return picture, exif_bytes

        finally:
            if 'camera_file' in locals():
                del camera_file
            if 'file_data' in locals():
                del file_data
            gp.check_result(gp.gp_camera_exit(self.camera, context))

    def capture_tethered(self):
        """ Use gphoto2 to capture and download the picture """

        try:
            context = gp.gp_context_new()
            gp.check_result(gp.gp_camera_init(self.camera, context))
            # Capture picture
            camera_path = gp.check_result(gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, context))
            folder = camera_path.folder
            name = camera_path.name

            # Get picture file
            error, camera_file = gp.gp_camera_file_get(
                self.camera,
                folder,
                name,
                gp.GP_FILE_TYPE_NORMAL,
                context)

            file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

            # Crop picture to be a square
            picture = Image.open(io.BytesIO(file_data))
            exif_dict = piexif.load(picture.info["exif"])
            w, h = picture.size
            left = (w - h) / 2
            top = 0
            right = w - left
            bottom = h
            picture = picture.crop((left, top, right, bottom))
            w, h = picture.size
            exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = w
            exif_bytes = piexif.dump(exif_dict)
            return picture, exif_bytes

        finally:
            if 'camera_file' in locals():
                del camera_file
            if 'file_data' in locals():
                del file_data
            gp.check_result(gp.gp_camera_exit(self.camera, context))

    def clear_space(self):
        """ Clear space on camera SD card """
        try:
            context = gp.gp_context_new()
            gp.check_result(gp.gp_camera_init(self.camera, context))
            files = self.list_files(self.camera, context)
            for f in files:
                self.delete_file(self.camera, context, f)
        finally:
            gp.check_result(gp.gp_camera_exit(self.camera, context))

    def delete_file(self, camera, context, path):
        """ Delete a file on the camera at a specific path """
        folder, name = os.path.split(path)
        gp.check_result(gp.gp_camera_file_delete(camera, folder, name, context))

    def list_files(self, camera, context, path='/'):
        """ List all files on camera """
        result = []
        # get files
        for name, value in gp.check_result(
                gp.gp_camera_folder_list_files(camera, path, context)):
            result.append(os.path.join(path, name))
        # read folders
        folders = []
        for name, value in gp.check_result(
                gp.gp_camera_folder_list_folders(camera, path, context)):
            folders.append(name)
        # recurse over subfolders
        for name in folders:
            result.extend(self.list_files(camera, context, os.path.join(path, name)))
        return result

