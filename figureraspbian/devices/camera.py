# -*- coding: utf8 -*-

import os
import time

import gphoto2 as gp
from pifacedigitalio import PiFaceDigital

from figureraspbian import settings
from figureraspbian.utils import timeit, crop_to_square


EOS_1200D_CONFIG = {
    'capturetarget': 1,
    'focusmode': 3,
    'imageformat': 6,
    'aperture': settings.APERTURE,
    'shutterspeed': settings.SHUTTER_SPEED,
    'iso': settings.ISO}


class open_camera:
    """ context manager to control access to the camera resource """

    def __enter__(self):
        self.camera = gp.check_result(gp.gp_camera_new())
        self.context = gp.gp_context_new()
        gp.check_result(gp.gp_camera_init(self.camera, self.context))
        return self.camera, self.context

    def __exit__(self, *exc):
        gp.check_result(gp.gp_camera_exit(self.camera, self.context))


def Camera():
    """ Factory to create a camera """
    if settings.CAMERA_TRIGGER_TYPE == 'REMOTE_RELEASE_CONNECTOR':
        return RemoteReleaseConnectorDSLRCamera()
    return DSLRCamera()


class DSLRCamera(object):
    """
    Digital Single Lens Reflex camera
    It uses gphoto2 to communicate with the digital camera:
    http://www.gphoto.org/proj/libgphoto2/
    Lists of supported cameras:
    http://www.gphoto.org/proj/libgphoto2/support.php
    """

    def __init__(self):

        with open_camera() as (camera, context):
            gp.check_result(gp.gp_camera_init(camera, context))
            config = gp.check_result(gp.gp_camera_get_config(camera, context))
            for param, choice in EOS_1200D_CONFIG.iteritems():
                widget = gp.check_result(gp.gp_widget_get_child_by_name(config, param))
                value = gp.check_result(gp.gp_widget_get_choice(widget, choice))
                gp.gp_widget_set_value(widget, value)
            gp.gp_camera_set_config(camera, config, context)

            self._clear_space(camera, context)

    def _trigger(self, camera, context):
        return gp.check_result(gp.gp_camera_capture(camera, gp.GP_CAPTURE_IMAGE, context))


    @timeit
    def capture(self):
        with open_camera() as (camera, context):
            # Capture picture
            camera_path = self._trigger(camera, context)
            folder = camera_path.folder
            name = camera_path.name

            # Get picture file
            error, camera_file = gp.gp_camera_file_get(
                camera,
                folder,
                name,
                gp.GP_FILE_TYPE_NORMAL,
                context)

            file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

            return crop_to_square(file_data)

    def _clear_space(self, camera, context):
        files = self._list_files(camera, context)
        for f in files:
            self._delete_file(camera, context, f)

    def clear_space(self):
        """ Clear space on camera SD card """
        with open_camera() as (camera, context):
            self._clear_space(camera, context)

    def _delete_file(self, camera, context, path):
        folder, name = os.path.split(path)
        gp.check_result(gp.gp_camera_file_delete(camera, folder, name, context))

    def delete_file(self, path):
        """ Delete a file on the camera at a specific path """
        with open_camera() as (camera, context):
            self._delete_file(camera, context, path)

    def _list_files(self, camera, context, path='/'):
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
            result.extend(self._list_files(camera, context, os.path.join(path, name)))
        return result

    def list_files(self, path='/'):
        """ List all files on camera """
        with open_camera() as (camera, context):
            return self._list_files(camera, context, path)


class RemoteReleaseConnector:
    """
    Represents a remote release connector. http://www.doc-diy.net/photo/remote_pinout/
    In our case the cable is just a 2.5mm jack
    """

    def __init__(self, pin=settings.CAMERA_REMOTE_RELEASE_CONNECTOR_PIN):
        self.pifacedigital = PiFaceDigital()
        self.pin = pin

    def trigger(self):
        self.pifacedigital.relays[1].turn_on()
        time.sleep(0.1)
        self.pifacedigital.relays[1].turn_off()


class TimeoutWaitingForFileAdded(Exception):
    pass


class RemoteReleaseConnectorDSLRCamera(DSLRCamera):
    """
    Represents a camera that is triggered with a remote release connector
    """

    def __init__(self):
        super(RemoteReleaseConnectorDSLRCamera, self).__init__()
        self.remote_release_connector = RemoteReleaseConnector()

    def _trigger(self, camera, context):
        self.remote_release_connector.trigger()
        return self._wait_for_file_added(camera, context)

    def _wait_for_file_added(self, camera, context, timeout=10):
        timeout_after = time.time() + timeout
        while True:
            if time.time() > timeout_after:
                raise TimeoutWaitingForFileAdded()
            event_type, data = gp.check_result(gp.gp_camera_wait_for_event(camera, 1000, context))
            if event_type == gp.GP_EVENT_FILE_ADDED:
                camera_file_path = data
                return camera_file_path
            time.sleep(0.1)
