from __future__ import print_function

import datetime
import os


class Module(object):
    def __init__(self, boot):
        self._boot = boot
        self._ready = False

        # Initialize schedule.
        schedule_start = self._parse_time(os.environ.get('SCHEDULE_START', '08:00'))
        schedule_end = self._parse_time(os.environ.get('SCHEDULE_END', '18:00'))
        schedule_t_off = self._parse_duration(os.environ.get('SCHEDULE_T_OFF', '35'))  # Time in minutes.
        schedule_t_on = self._parse_duration(os.environ.get('SCHEDULE_T_ON', '15'))  # Time in minutes.

        if not schedule_start or not schedule_end or not schedule_t_off or not schedule_t_on:
            print("WARNING: Ignoring malformed schedule specification.")
            return

        self._started = datetime.datetime.now()
        self._schedule_start = schedule_start
        self._schedule_end = schedule_end
        self._on_duration = schedule_t_on
        self._off_duration = schedule_t_off
        self._ready = True

    def _parse_time(self, time):
        """Parse time string (HH:MM)."""
        try:
            hour, minute = time.split(':')
            return datetime.time(hour=int(hour), minute=int(minute), second=0)
        except (ValueError, IndexError):
            return None

    def _parse_duration(self, duration):
        """Parse duration string (in minutes)."""
        try:
            return datetime.timedelta(minutes=int(duration))
        except ValueError:
            return None

    def process(self, modules):
        """Check if we need to shutdown."""
        if not self._ready:
            return

        # Check if we have been online too long and shutdown.
        if (datetime.datetime.now() - self._started) >= self._on_duration:
            print("Have been online for too long, need to shutdown.")
            self._boot.shutdown()

    def shutdown(self, modules):
        """Compute next alarm before shutdown."""
        if not self._ready:
            return

        current_time = self._boot.rtc.current_time
        wakeup_time = None
        if current_time.time() > self._schedule_start and current_time.time() < self._schedule_end:
            wakeup_time = (current_time + self._off_duration).time()
        else:
            wakeup_time = self._schedule_start

        print("Scheduling next wakeup at {}.".format(wakeup_time.isoformat()))
        self._boot.rtc.alarm1_time = wakeup_time
