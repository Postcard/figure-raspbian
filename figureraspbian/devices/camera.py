# -*- coding: utf8 -*-

import os
import io

from PIL import Image
try:
    import gphoto2 as gp
except ImportError:
    print "Could not import gphoto2"

from ..utils import timeit


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
        # Clear camera space
        self.clear_space()

    @timeit
    def capture(self):

        try:
            context = gp.gp_context_new()
            gp.check_result(gp.gp_camera_init(self.camera, context))
            # Capture image
            camera_path = gp.check_result(gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, context))
            folder = camera_path.folder
            name = camera_path.name

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
            return snapshot

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