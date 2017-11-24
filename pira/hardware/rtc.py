import datetime
import smbus


def bcd_to_int(bcd):
    """Decode BCD-encoded integer to integer."""
    return (bcd & 0xF) + ((bcd & 0xF0) >> 4) * 10


def int_to_bcd(x, n=2):
    """
    Encode the n least significant decimal digits of x
    to packed binary coded decimal (BCD).
    Return packed BCD value.
    n defaults to 2 (digits).
    n=0 encodes all digits.
    """
    return int(str(x)[-n:], 0x10)


class RTC(object):
    I2C_ADDRESS = 0x68

    HOUR_12_24 = (1 << 6)
    HOUR_AM_PM = (1 << 5)

    ALARM_MASK = (1 << 7)

    REGISTER_CURRENT = 0x00
    REGISTER_ALARM1 = 0x07
    REGISTER_ALARM2 = 0x0b
    REGISTER_CONTROL = 0x0e
    REGISTER_STATUS = 0x0f
    REGISTER_TEMPERATURE_MSB = 0x11
    REGISTER_TEMPERATURE_LSB = 0x12

    CONTROL_A1IE = (1 << 0)
    CONTROL_A2IE = (1 << 1)
    CONTROL_INTCN = (1 << 2)

    STATUS_A1F = (1 << 0)
    STATUS_A2F = (1 << 1)

    OFFSET_SECOND = 0
    OFFSET_MINUTE = 1
    OFFSET_HOUR = 2
    OFFSET_DAY = 3
    OFFSET_DATE = 4
    OFFSET_MONTH = 5
    OFFSET_YEAR = 6

    YEAR_BASE = 2000

    def __init__(self, bus=1):
        self._i2c = smbus.SMBus(bus)

    def _read(self, register):
        try:
            return self._i2c.read_byte_data(RTC.I2C_ADDRESS, register)
        except IOError:
            return 0

    def _write(self, register, data):
        try:
            self._i2c.write_byte_data(RTC.I2C_ADDRESS, register, data)
        except IOError:
            pass

    def _decode_time(self, offset, has_seconds=True, has_month_year=True):
        length = 7
        if not has_seconds:
            length -= 1
        if not has_month_year:
            length -= 2

        values = [
            self._read(register) for register in range(offset, offset + length)
        ]

        if not has_seconds:
            values.insert(0, 0)
        if not has_month_year:
            values += [1, 0]

        # Bit 6 of hour: 12-hour mode.
        hour_pm = False
        if values[RTC.OFFSET_HOUR] & RTC.HOUR_12_24:
            if values[RTC.OFFSET_HOUR] & RTC.HOUR_AM_PM:
                hour_pm = True
                values[RTC.OFFSET_HOUR] ^= RTC.HOUR_AM_PM

            values[RTC.OFFSET_HOUR] ^= RTC.HOUR_12_24

        # Clear bit 7 in all values as this bit contains various alarm flags.
        values = [value & ~RTC.ALARM_MASK for value in values]

        second, minute, hour, day, date, month, year = [bcd_to_int(value) for value in values]
        if hour_pm:
            hour += 12

        # Values can be incorrect when certain alarm registers are not initialized.
        if not date:
            date = 1
        if not month:
            month = 1
        if second > 59:
            second = 0
        if minute > 59:
            minute = 0
        if hour > 23:
            hour = 0

        return datetime.datetime(
            year=RTC.YEAR_BASE + year,
            month=month,
            day=date,
            second=second,
            minute=minute,
            hour=hour,
        )

    def _set_alarm(self, register, value, has_seconds=True):
        values = []
        if has_seconds:
            values.append(value.second)

        values += [
            value.minute,
            value.hour,
        ]

        for offset, value in enumerate(values):
            self._write(register + offset, int_to_bcd(value))

        # Alarm when second, minute and hour match.
        self._write(register + len(values), RTC.ALARM_MASK)

        # Setup control register.
        control = self._read(RTC.REGISTER_CONTROL)
        control |= RTC.CONTROL_INTCN
        if register == RTC.REGISTER_ALARM1:
            control |= RTC.CONTROL_A1IE
        elif register == RTC.REGISTER_ALARM2:
            control |= RTC.CONTROL_A2IE
        self._write(RTC.REGISTER_CONTROL, control)

    @property
    def status(self):
        """Value of the status register."""
        return self._read(RTC.REGISTER_STATUS)

    @property
    def current_time(self):
        """Current RTC time."""
        return self._decode_time(RTC.REGISTER_CURRENT)

    @property
    def alarm1_time(self):
        """Alarm 1 time."""
        return self._decode_time(RTC.REGISTER_ALARM1, has_month_year=False)

    @alarm1_time.setter
    def alarm1_time(self, value):
        self._set_alarm(RTC.REGISTER_ALARM1, value)

    def alarm1_clear(self):
        """Clear alarm 1."""
        status = self.status
        status &= ~RTC.STATUS_A1F
        self._write(RTC.REGISTER_STATUS, status)

    @property
    def alarm2_time(self):
        """Alarm 2 time."""
        return self._decode_time(RTC.REGISTER_ALARM2, has_seconds=False, has_month_year=False)

    @alarm2_time.setter
    def alarm2_time(self, value):
        self._set_alarm(RTC.REGISTER_ALARM2, value, has_seconds=False)

    def alarm2_clear(self):
        """Clear alarm 2."""
        status = self.status
        status &= ~RTC.STATUS_A2F
        self._write(RTC.REGISTER_STATUS, status)

    @property
    def temperature(self):
        """Temperature."""
        msb = self._read(RTC.REGISTER_TEMPERATURE_MSB)
        lsb = self._read(RTC.REGISTER_TEMPERATURE_LSB)

        # Temperature is signed.
        sign = -1 if (msb >> 7) else 1
        msb &= 0b01111111

        return sign * ((msb << 2) | (lsb >> 6)) * 0.25
