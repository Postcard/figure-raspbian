import time
import operator

from datetime import datetime

from gpiozero import OutputDevice, InputDevice

from .. import settings


class RTC(object):

    def read_datetime(self):
        raise NotImplementedError()

    def write_datetime(self, dt):
        raise NotImplementedError()

    def factory(*args, **kwargs):
        if settings.RTC == 'DS1302':
            return RTC_DS1302()
        return None

    factory = staticmethod(factory)


def transaction_decorate(func):
    """ Start and complete a transaction with the DS1302 RTC """
    from functools import wraps
    @wraps(func)
    def wrapper(self, *args, **kwargs):

        SCLK = OutputDevice(self.SCLK_PIN, initial_value=False)
        SDAT = OutputDevice(self.SDAT_PIN, initial_value=False)
        RST = OutputDevice(self.RST_PIN, initial_value=False)

        SCLK.off()
        SDAT.off()
        time.sleep(self.CLK_PERIOD)
        RST.on()

        SCLK.close()
        SDAT.close()
        RST.close()

        func(self, *args, **kwargs)

        SCLK = OutputDevice(self.SCLK_PIN, initial_value=False)
        SDAT = OutputDevice(self.SDAT_PIN, initial_value=False)
        RST = OutputDevice(self.RST_PIN, initial_value=False)

        SCLK.off()
        SDAT.off()
        time.sleep(self.CLK_PERIOD)
        RST.off()

        SCLK.close()
        SDAT.close()
        RST.close()

    return wrapper


class RTC_DS1302(RTC):
    """
    Inspired by https://github.com/BirchJD/RTC_DS1302
    """

    SCLK_PIN = settings.RTC_SCLK_PIN
    SDAT_PIN = settings.RTC_SDAT_PIN
    RST_PIN = settings.RTC_RST_PIN
    CLK_PERIOD = 0.00001

    def __init__(self, *args, **kwargs):
        super(RTC_DS1302, self).__init__(*args, **kwargs)
        self.initialize()

    @transaction_decorate
    def initialize(self):
        self._write_byte(int("10001110", 2))
        self._write_byte(int("00000000", 2))
        # Make sure trickle charge mode is turned off.
        self._write_byte(int("10010000", 2))
        self._write_byte(int("00000000", 2))

    def read_datetime(self):
        return self._read_date_time()

    def write_datetime(self, dt):
        year = dt.year % 100
        month = dt.month
        day = dt.day
        day_of_week = dt.weekday()
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        self._write_date_time(year, month, day, day_of_week, hour, minute, second)

    def _write_byte(self, Byte):
        for Count in range(8):
            time.sleep(self.CLK_PERIOD)
            SCLK = OutputDevice(self.SCLK_PIN, initial_value=False)
            SDAT = OutputDevice(self.SDAT_PIN, initial_value=False)
            SCLK.off()
            Bit = operator.mod(Byte, 2)
            Byte = operator.div(Byte, 2)
            time.sleep(self.CLK_PERIOD)
            SDAT.on() if Bit else SDAT.off()
            time.sleep(self.CLK_PERIOD)
            SCLK.on()
            SCLK.close()
            SDAT.close()

    def _read_byte(self):
        SDAT = InputDevice(self.SDAT_PIN, pull_up=False)
        SCLK = OutputDevice(self.SCLK_PIN, initial_value=False)
        Byte = 0
        for Count in range(8):
            time.sleep(self.CLK_PERIOD)
            SCLK.on()
            time.sleep(self.CLK_PERIOD)
            SCLK.off()
            time.sleep(self.CLK_PERIOD)
            Bit = 1 if SDAT.is_active() else 0
            Byte |= ((2 ** Count) * Bit)
        SDAT.close()
        SCLK.close()
        return Byte

    @transaction_decorate
    def _write_date_time(self, year, month, day, day_of_week, hour, minute, second):
        self._write_byte(int("10111110", 2))
        # Write seconds data.
        self._write_byte(operator.mod(second, 10) | operator.div(second, 10) * 16)
        # Write minute data.
        self._write_byte(operator.mod(minute, 10) | operator.div(minute, 10) * 16)
        # Write hour data.
        self._write_byte(operator.mod(hour, 10) | operator.div(hour, 10) * 16)
        # Write day data.
        self._write_byte(operator.mod(day, 10) | operator.div(day, 10) * 16)
        # Write month data.
        self._write_byte(operator.mod(month, 10) | operator.div(month, 10) * 16)
        # Write day of week data.
        self._write_byte(operator.mod(day_of_week, 10) | operator.div(day_of_week, 10) * 16)
        # Write year of week data.
        self._write_byte(operator.mod(year, 10) | operator.div(year, 10) * 16)
        # Make sure write protect is turned off.
        self._write_byte(int("00000000", 2))
        # Make sure trickle charge mode is turned off.
        self._write_byte(int("00000000", 2))

    @transaction_decorate
    def _read_date_time(self):
        # Read date and time data.
        Byte = self._read_byte()
        second = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self._read_byte()
        minute = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self._read_byte()
        hour = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self._read_byte()
        day = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self._read_byte()
        month = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self._read_byte()
        day_of_week = (operator.mod(Byte, 16) + operator.div(Byte, 16) * 10) - 1
        Byte = self._read_byte()
        year = 2000 + (operator.mod(Byte, 16) + operator.div(Byte, 16) * 10)
        return datetime(year, month, day, hour, minute, second)
