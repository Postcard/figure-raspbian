import time
import operator

from datetime import datetime

import RPi.GPIO

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



# RTC_DS1302 - Python Hardware Programming Education Project For Raspberry Pi
# Copyright (C) 2015 Jason Birch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#/****************************************************************************/
#/* RTC_DS1302                                                               */
#/* ------------------------------------------------------------------------ */
#/* V1.00 - 2015-08-26 - Jason Birch                                         */
#/* ------------------------------------------------------------------------ */
#/* Class to handle controlling a Real Time Clock IC DS1302.                 */
#/****************************************************************************/


class RTC_DS1302:
    RTC_DS1302_SCLK = settings.RTC_SCLK_PIN
    RTC_DS1302_CE = settings.RTC_RST_PIN
    RTC_DS1302_IO = settings.RTC_SDAT_PIN

    CLK_PERIOD = 0.00001

    DOW = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ]


    def __init__(self):
        # Turn off GPIO warnings.
        RPi.GPIO.setwarnings(False)
        # Configure Raspberry Pi GPIO interfaces.
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        # Initiate DS1302 communication.
        self.InitiateDS1302()
        # Make sure write protect is turned off.
        self.WriteByte(int("10001110", 2))
        self.WriteByte(int("00000000", 2))
        # Make sure trickle charge mode is turned off.
        self.WriteByte(int("10010000", 2))
        self.WriteByte(int("00000000", 2))
        # End DS1302 communication.
        self.EndDS1302()

    #/***********************************/
    #/* Write date and time to the RTC. */
    #/***********************************/
    def write_datetime(self, dt):
        year = dt.year % 100
        month = dt.month
        day = dt.day
        day_of_week = dt.weekday()
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        self._write_datetime(year, month, day, day_of_week, hour, minute, second)


    #/*************************************/
    #/* Read date and time from the RTC. */
    #/*************************************/
    def read_datetime(self):
        # Initiate DS1302 communication.
        self.InitiateDS1302()
        # Write address byte.
        self.WriteByte(int("10111111", 2))
        # Read date and time data.

        Byte = self.ReadByte()
        second = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self.ReadByte()
        minute = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self.ReadByte()
        hour = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self.ReadByte()
        day = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self.ReadByte()
        month = operator.mod(Byte, 16) + operator.div(Byte, 16) * 10
        Byte = self.ReadByte()
        _ = (operator.mod(Byte, 16) + operator.div(Byte, 16) * 10) - 1
        Byte = self.ReadByte()
        year = 2000 + operator.mod(Byte, 16) + operator.div(Byte, 16) * 10

        dt = datetime(year, month, day, hour, minute, second)

        # End DS1302 communication.
        self.EndDS1302()
        return dt

    #/*************************************************/
    #/* Close Raspberry Pi GPIO use before finishing. */
    #/*************************************************/
    def CloseGPIO(self):
        RPi.GPIO.cleanup()


    #/********************************************/
    #/* Start a transaction with the DS1302 RTC. */
    #/********************************************/
    def InitiateDS1302(self):
        RPi.GPIO.setup(self.RTC_DS1302_SCLK, RPi.GPIO.OUT, initial=0)
        RPi.GPIO.setup(self.RTC_DS1302_CE, RPi.GPIO.OUT, initial=0)
        RPi.GPIO.setup(self.RTC_DS1302_IO, RPi.GPIO.OUT, initial=0)
        RPi.GPIO.output(self.RTC_DS1302_SCLK, 0)
        RPi.GPIO.output(self.RTC_DS1302_IO, 0)
        time.sleep(self.CLK_PERIOD)
        RPi.GPIO.output(self.RTC_DS1302_CE, 1)


    #/***********************************************/
    #/* Complete a transaction with the DS1302 RTC. */
    #/***********************************************/
    def EndDS1302(self):
        RPi.GPIO.setup(self.RTC_DS1302_SCLK, RPi.GPIO.OUT, initial=0)
        RPi.GPIO.setup(self.RTC_DS1302_CE, RPi.GPIO.OUT, initial=0)
        RPi.GPIO.setup(self.RTC_DS1302_IO, RPi.GPIO.OUT, initial=0)
        RPi.GPIO.output(self.RTC_DS1302_SCLK, 0)
        RPi.GPIO.output(self.RTC_DS1302_IO, 0)
        time.sleep(self.CLK_PERIOD)
        RPi.GPIO.output(self.RTC_DS1302_CE, 0)


    #/*******************************************/
    #/* Write a byte of data to the DS1302 RTC. */
    #/*******************************************/
    def WriteByte(self, Byte):
        for Count in range(8):
            time.sleep(self.CLK_PERIOD)
            RPi.GPIO.output(self.RTC_DS1302_SCLK, 0)

            Bit = operator.mod(Byte, 2)
            Byte = operator.div(Byte, 2)
            time.sleep(self.CLK_PERIOD)
            RPi.GPIO.output(self.RTC_DS1302_IO, Bit)

            time.sleep(self.CLK_PERIOD)
            RPi.GPIO.output(self.RTC_DS1302_SCLK, 1)


    #/******************************************/
    #/* Read a byte of data to the DS1302 RTC. */
    #/******************************************/
    def ReadByte(self):
        RPi.GPIO.setup(self.RTC_DS1302_IO, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_DOWN)

        Byte = 0
        for Count in range(8):
            time.sleep(self.CLK_PERIOD)
            RPi.GPIO.output(self.RTC_DS1302_SCLK, 1)

            time.sleep(self.CLK_PERIOD)
            RPi.GPIO.output(self.RTC_DS1302_SCLK, 0)

            time.sleep(self.CLK_PERIOD)
            Bit = RPi.GPIO.input(self.RTC_DS1302_IO)
            Byte |= ((2 ** Count) * Bit)

        return Byte


    #/***********************************/
    #/* Write a message to the RTC RAM. */
    #/***********************************/
    def WriteRAM(self, Data):
        # Initiate DS1302 communication.
        self.InitiateDS1302()
        # Write address byte.
        self.WriteByte(int("11111110", 2))
        # Write data bytes.
        for Count in range(len(Data)):
            self.WriteByte(ord(Data[Count:Count + 1]))
        for Count in range(31 - len(Data)):
            self.WriteByte(ord(" "))
        # End DS1302 communication.
        self.EndDS1302()


    #/**********************************/
    #/* Read message from the RTC RAM. */
    #/**********************************/
    def ReadRAM(self):
    # Initiate DS1302 communication.
        self.InitiateDS1302()
        # Write address byte.
        self.WriteByte(int("11111111", 2))
        # Read data bytes.
        Data = ""
        for Count in range(31):
            Byte = self.ReadByte()
            Data += chr(Byte)
            # End DS1302 communication.
        self.EndDS1302()
        return Data

    def _write_datetime(self, Year, Month, Day, DayOfWeek, Hour, Minute, Second):
        # Initiate DS1302 communication.
        self.InitiateDS1302()
        # Write address byte.
        self.WriteByte(int("10111110", 2))
        # Write seconds data.
        self.WriteByte(operator.mod(Second, 10) | operator.div(Second, 10) * 16)
        # Write minute data.
        self.WriteByte(operator.mod(Minute, 10) | operator.div(Minute, 10) * 16)
        # Write hour data.
        self.WriteByte(operator.mod(Hour, 10) | operator.div(Hour, 10) * 16)
        # Write day data.
        self.WriteByte(operator.mod(Day, 10) | operator.div(Day, 10) * 16)
        # Write month data.
        self.WriteByte(operator.mod(Month, 10) | operator.div(Month, 10) * 16)
        # Write day of week data.
        self.WriteByte(operator.mod(DayOfWeek, 10) | operator.div(DayOfWeek, 10) * 16)
        # Write year of week data.
        self.WriteByte(operator.mod(Year, 10) | operator.div(Year, 10) * 16)
        # Make sure write protect is turned off.
        self.WriteByte(int("00000000", 2))
        # Make sure trickle charge mode is turned off.
        self.WriteByte(int("00000000", 2))
        # End DS1302 communication.
        self.EndDS1302()
