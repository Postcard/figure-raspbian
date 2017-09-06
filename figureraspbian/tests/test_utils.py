
from unittest import TestCase
import mock
from .. import utils
import tempfile
import time
from datetime import datetime
import netifaces
import os

from PIL import Image


class TestUtils(TestCase):

    def test_url2name(self):
        """ it should convert a file url to its basename """
        url = 'http://api.figuredevices.com/static/css/ticket.css'
        name = utils.url2name(url)
        expected = 'ticket.css'
        self.assertEqual(name, expected)

    @mock.patch('figureraspbian.utils.urllib2')
    def test_download(self, mock_urllib2):
        """ it should download file if not present in local file system and return file path """
        tempdir = tempfile.mkdtemp()
        mock_filelike = mock.Mock()
        mock_urllib2.urlopen.return_value = mock_filelike
        mock_filelike.read.return_value = 'file content'
        utils.download('https://path/to/some/file.txt', tempdir)
        self.assertEqual(mock_urllib2.urlopen.call_count, 1)
        # try downloading again, it should do nothing as file is already present
        utils.download('https://path/to/some/file.txt', tempdir)
        self.assertEqual(mock_urllib2.urlopen.call_count, 1)
        # forcing the download should overwrite the file
        utils.download('https://path/to/some/file.txt', tempdir, force=True)
        self.assertEqual(mock_urllib2.urlopen.call_count, 2)

    @mock.patch('figureraspbian.utils.logger.info')
    def test_timeit(self, mock_info):
        """
        timeit should log time spend in a function
        """
        @utils.timeit
        def sleep():
            time.sleep(0.5)
            return "wake up"
        r = sleep()
        assert r == "wake up"
        assert mock_info.called

    def test_get_filename(self):
        filename = utils.get_file_name("CODES")
        assert filename == 'Figure_N5rIARTnVC1ySp0.jpg'

    def test_get_data_url(self):
        im = Image.new('L', (1, 1))
        im.format = 'JPEG'
        data_url = utils.get_data_url(im)
        expected = ("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh"
                    "0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQF"
                    "BgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJi"
                    "coKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2"
                    "t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APn+v//Z")
        self.assertEqual(data_url, expected)

    def test_pixels2cm(self):
        """
        pixels2cm should convert image pixels into how many cm will actually be printed on the ticket
        """
        cm = utils.pixels2cm(1098)
        self.assertAlmostEqual(cm, 14.5, delta=0.05)

    def test_new_paper_level(self):
        """ it should calculate new paper level based on old paper level and ticket printed length """
        new_paper_level = utils.new_paper_level(80.0, 900)
        self.assertAlmostEqual(new_paper_level, 79.85, delta=0.01)

    def test_new_aper_level_below_1(self):
        """ it should reset paper level to 10 if we go below 1 """
        new_paper_level = utils.new_paper_level(1.0, 900)
        self.assertEqual(new_paper_level, 10.0)

    @mock.patch("figureraspbian.utils.os.system")
    def test_set_system_time(self, mock_system):
        """ it should set system time from a datetime """
        dt = datetime(2017, 1, 1)
        utils.set_system_time(dt)
        mock_system.assert_called_with('date -s "2017-01-01 00:00:00"')

    @mock.patch("figureraspbian.utils.netifaces.ifaddresses")
    @mock.patch("figureraspbian.utils.netifaces.interfaces")
    def test_get_mac_addresses(self, mock_interfaces, mock_ifaddresses):
        mock_interfaces.return_value = ['lo0', 'en0']
        mock_ifaddresses.side_effect = [
            {netifaces.AF_LINK: [{'addr': '3c:15:c2:e3:b9:4e'}]},
            {netifaces.AF_LINK: [{'addr': '72:00:04:84:f5:60'}]}
        ]
        mac_addresses = utils.get_mac_addresses()
        expected = "lo0=3c:15:c2:e3:b9:4e,en0=72:00:04:84:f5:60"
        self.assertEqual(mac_addresses, expected)

    def test_render_jinja_template(self):
        """ it should render a jinja template stored in a file located at path with the given kwargs"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            template = "{{ foo }}{{ bar }}"
            tmp_file.write(template)
            path = tmp_file.name
        rendered = utils.render_jinja_template(path, foo="foo", bar="bar")
        os.remove(path)
        expected = "foobar"
        self.assertEqual(rendered, expected)

    @mock.patch("figureraspbian.utils.subprocess")
    def test_get_usb_devices(self, mock_subprocess):
        """ it should parse the output of lsusb """
        mock_subprocess.check_output.return_value = (
            "Bus 001 Device 005: ID 04b8:0e15 Seiko Epson Corp.\n"
            "Bus 001 Device 006: ID 04a9:327f Canon, Inc.")
        devices = utils.get_usb_devices()
        expected = [
            {'device': '/dev/bus/usb/001/005', 'vendor_id': '04b8', 'tag': 'Seiko Epson Corp.', 'product_id': '0e15'},
            {'device': '/dev/bus/usb/001/006', 'vendor_id': '04a9', 'tag': 'Canon, Inc.', 'product_id': '327f'}]
        self.assertEqual(devices, expected)

    def test_crop_to_square(self):
        """ it should crop a rectangle image to a square """
        im = Image.new('L', (200, 100))
        cropped = utils.crop_to_square(im)
        self.assertEqual(cropped.size, (100, 100))

    def test_resize_preserve_ratio(self):
        """ it should resize an image to a given height or width preserving the ratio """
        im = Image.new('L', (200, 100))
        resized = utils.resize_preserve_ratio(im, new_width=100)
        self.assertEqual(resized.size[1], 50)
        resized = utils.resize_preserve_ratio(im, new_height=10)
        self.assertEqual(resized.size[0], 20)

    def test_new_paper_level_after_successful_print(self):
        """ it should decrease the level of paper based on the ticket lenght """
        new_paper_level = utils.new_paper_level(56.0, 1000)
        self.assertAlmostEqual(new_paper_level, 55.83, 2)

    def test_new_paper_level_when_below_1(self):
        """ it should set paper level to 10 """
        new_paper_level = utils.new_paper_level(1.0, 1000)
        self.assertEqual(new_paper_level, 10.0)

    def test_new_paper_level_if_previous_paper_level_is_0(self):
        """ it should set paper level to 100 """
        new_paper_level = utils.new_paper_level(0.0, 1000)
        self.assertEqual(new_paper_level, 100.0)