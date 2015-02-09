
from setuptools import setup

setup(name="figure_raspbian",
      version="0.1",
      description="Control devices to run a Figure processus on a Raspberry Pi",
      author="benoitguigal",
      author_email="benoit.guigal@gmail.com",
      packages=['figureraspbian'],
      install_requires=[
          'python_epson_printer==1.5',
          'requests==2.5.1',
          'Pillow==2.6',
          'selenium',
          'gphoto2'
      ],
      dependency_links=['https://github.com/benoitguigal/python-epson-printer/tarball/master#egg=python_epson_printer-1.5']
)
