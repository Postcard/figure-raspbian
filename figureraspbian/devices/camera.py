import os
from PIL import Image
from datetime import datetime
from .. import settings

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
        self.camera.init(self.context)
        try:
            # set to black and white
            error, widget = gp.gp_camera_get_config(self.camera, self.context)
            error, child = gp.gp_widget_get_child_by_name(widget, 'picturestyle')
            gp.gp_widget_set_value(child, '5')
            gp.gp_camera_set_config(self.camera, widget, self.context)
        finally:
            self.camera.exit(self.context)


    def capture(self):
        self.camera.init(self.context)
        try:
            # Capture image
            error, filepath = gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, self.context)
            # Create a CameraFile from the FilePath
            error, camerafile = gp.gp_camera_file_get(self.camera, filepath.folder, filepath.name, gp.GP_FILE_TYPE_NORMAL, self.context)
            # Create file path on the RaspberryPi
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            basename = "{scenario}_{now}.jpg".format(event=settings.SCENARIO, now=now)
            path = os.path.join(settings.SNAPSHOT_DIR, basename)
            # Save the file to the Raspberry Pi
            camerafile.save(path)
            # Delete the file
            gp.gp_camera_file_delete(self.camera, filepath.folder, filepath.name, self.context)
        finally:
            self.camera.exit(self.context)
        im = Image.open(path)
        im = im.rotate(90)
        w, h = im.size
        left = 0
        top = (h - w) / 2
        right = w
        bottom = h - top
        im = im.crop((left, top, right, bottom))
        im.save("/mnt/{basename}".format(basename=basename))
        im.save(path)
        return path



class DummyCamera(Camera):
    """ Dummy camera used for tests purposes. It prints a message to the console """

    def __init__(self):
        pass


    def capture(self):
        print("Capture picture")


