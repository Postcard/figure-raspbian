import os
import shutil
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

    def capture(self):
        self.camera.init(self.context)
        try:
            # Capture image
            error, filepath = gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE, self.context)
            # Create a CameraFile from the FilePath
            error, camerafile = gp.gp_camera_file_get(self.camera, filepath.folder, filepath.name, gp.GP_FILE_TYPE_NORMAL, self.context)
            # Create file path on the RaspberryPi
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            basename = "{scenario}_{now}.jpg".format(scenario=settings.SCENARIO, now=now)
            path = os.path.join(settings.SNAPSHOT_DIR, basename)
            # Save the file to the Raspberry Pi
            camerafile.save(path)
        finally:
            self.camera.exit(self.context)
        if settings.ENVIRONMENT is 'production':
            shutil.copy2(path, "/mnt/%s" % os.path.basename(path))
        im = Image.open(path)
        w, h = im.size
        left = (w - h) / 2
        top = 0
        right = w - left
        bottom = h
        im = im.crop((left, top, right, bottom))
        im = im.resize((512, 512), Image.ANTIALIAS)
        im.save(path)
        return path


class DummyCamera(Camera):
    """ Dummy camera used for tests purposes. It prints a message to the console """

    def __init__(self):
        pass

    def capture(self):
        print "Capture snapshot"
        return os.path.join(settings.FIGURE_DIR, 'resources/2_20150331.jpg')


