# -*- coding: utf8 -*-

import os
import time
from contextlib import contextmanager

import gphoto2 as gp

from .. import settings
from ..utils import timeit, crop_to_square
from .remote_release_connector import RemoteReleaseConnector
from ..exceptions import TimeoutWaitingForFileAdded

EOS_1200D_CONFIG = {
    'reviewtime': 0,
    'capturetarget': 1,
    'imageformat': 6,
    'imageformatsd': 6,
    'picturestyle': 1,
    'eosremoterelease': 0,
    'whitebalance': settings.WHITE_BALANCE,
    'aperture': settings.APERTURE,
    'shutterspeed': settings.SHUTTER_SPEED,
    'iso': settings.ISO
}


@contextmanager
def open_camera():
    """ context manager to control access to the camera resource """
    camera = gp.check_result(gp.gp_camera_new())
    context = gp.gp_context_new()
    gp.check_result(gp.gp_camera_init(camera, context))
    yield camera, context
    gp.check_result(gp.gp_camera_exit(camera, context))


class Camera(object):
    """
    Represents a digital camera that can be controlled with libgphoto2
    http://www.gphoto.org/proj/libgphoto2/
    Lists of supported cameras:
    http://www.gphoto.org/proj/libgphoto2/support.php
    """

    def __init__(self, *args, **kwargs):

        with open_camera() as (camera, context):
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

    def focus_further(self, steps, camera, config, context):
        for i in range(0, steps):
            self.change_focus(1, camera, config, context)

    def focus_nearer(self, steps, camera, config, context):
        for i in range(0, steps):
            self.change_focus(0, camera, config, context)

    def change_focus(self, direction, camera, config, context):
        """
        :param direction: 1 further, 0 nearer
        """
        widget = gp.check_result(gp.gp_widget_get_child_by_name(config, 'manualfocusdrive'))
        value = gp.check_result(gp.gp_widget_get_choice(widget, 6 if direction else 2))
        gp.gp_widget_set_value(widget, value)
        gp.gp_camera_set_config(camera, config, context)
        value = gp.check_result(gp.gp_widget_get_choice(widget, 3))
        gp.gp_widget_set_value(widget, value)
        gp.gp_camera_set_config(camera, config, context)

    def focus(self):
        """ Adjust the focus """
        with open_camera() as (camera, context):
            config = gp.check_result(gp.gp_camera_get_config(camera, context))
            widget = gp.check_result(gp.gp_widget_get_child_by_name(config, 'viewfinder'))
            gp.gp_widget_set_value(widget, 1)
            gp.gp_camera_set_config(camera, config, context)
            time.sleep(0.5)
            # focus is relative so we need to focus the furthest possible before adjusting
            self.focus_further(80, camera, config, context)
            self.focus_nearer(settings.CAMERA_FOCUS_STEPS, camera, config, context)
            gp.gp_widget_set_value(widget, 1)
            gp.gp_camera_set_config(camera, config, context)


    @classmethod
    def factory(cls, *args, **kwargs):
        if settings.CAMERA_TRIGGER_TYPE == 'GPHOTO2':
            return cls(*args, **kwargs)
        elif settings.CAMERA_TRIGGER_TYPE == 'REMOTE_RELEASE_CONNECTOR':
            return RemoteReleaseConnector(*args, **kwargs)


class RemoteReleaseConnectorCamera(Camera):
    """
    Represents a camera that is triggered with a remote release connector
    """

    def __init__(self, *args, **kwargs):
        super(RemoteReleaseConnectorCamera, self).__init__(*args, **kwargs)
        self.remote_release_connector = RemoteReleaseConnector.factory(settings.REMOTE_RELEASE_CONNECTOR_PIN)

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
            time.sleep(0.0001)
