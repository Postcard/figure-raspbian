# -*- coding: utf8 -*-

import os
from datetime import datetime
import pytz
import io

from PIL import Image
import gphoto2 as gp
from hashids import Hashids

from .. import settings


hashids = Hashids(salt='Titi Vicky Benni')


class Camera(object):
    """ Camera interface """

    def capture(self):
        raise NotImplementedError


EOS_1200D_CONFIG = {
    'capturetarget': 1,
    'focusmode': 3,
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
        self.camera = gp.check_result(gp.gp_camera_new())

        # Camera specific configuration
        if settings.CAMERA_MODEL == 'CANON_1200D':
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

    def capture(self, installation):

        try:
            context = gp.gp_context_new()
            gp.check_result(gp.gp_camera_init(self.camera, context))
            # Capture image
            camera_path = gp.check_result(gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, context))
            folder = camera_path.folder
            name = camera_path.name

            date = datetime.now(pytz.timezone(settings.TIMEZONE))

            # Get snapshot file
            error, camera_file = gp.gp_camera_file_get(
                self.camera,
                folder,
                name,
                gp.GP_FILE_TYPE_NORMAL,
                context)

            file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

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

            unique_id = "{installation}{date}".format(installation=installation, date=date.strftime('%Y%m%d%H%M%S'))
            basename = "Figure_%s.jpg" % hashids.encode(int(unique_id))
            raspberry_path = os.path.join(settings.MEDIA_ROOT, 'snapshots', basename)

            small.save(raspberry_path)

            return raspberry_path, snapshot, date, camera_path

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


class DummyCamera(Camera):
    """ Dummy camera used for tests purposes. It prints a message to the console """

    def __init__(self):
        pass

    def capture(self):
        print "Capture snapshot"
        return os.path.join(settings.FIGURE_DIR, 'resources/2_20150331.jpg')


