from __future__ import print_function

import datetime
import io
import os

import numpy as np
import picamera
import picamera.array

# Image storage location.
CAMERA_STORAGE_PATH = '/data/camera'


class Module(object):
    def __init__(self, boot):
        self._boot = boot
        self._camera = None
        self._recording_start = None
        self._last_snapshot = None

        self.resolution = os.environ.get('CAMERA_RESOLUTION', '1280x720')
        self.camera_shutdown = os.environ.get('CAMERA_SHUTDOWN', '0')
        self.video_duration = os.environ.get('CAMERA_VIDEO_DURATION', 'until-sleep')
        self.snapshot_interval_conf = os.environ.get('SNAPSHOT_INTERVAL', 'off')

        try:
            self.video_duration_min = datetime.timedelta(minutes=int(self.video_duration))
        except ValueError:
            self.video_duration_min = None

        try:
            self.snapshot_interval= datetime.timedelta(minutes=int(self.snapshot_interval_conf))
        except ValueError:
            self.snapshot_interval = None

        self.light_level = 0.0
        try:
            self.minimum_light_level = float(os.environ.get('CAMERA_MIN_LIGHT_LEVEL', 0.0))
        except ValueError:
            self.minimum_light_level = 0.0

        # Ensure storage location exists.
        try:
            os.makedirs(CAMERA_STORAGE_PATH)
        except OSError:
            pass

        # Check how much space is left
        info = os.statvfs(CAMERA_STORAGE_PATH)
        free_space = (info.f_frsize * info.f_bavail / (1024.0 * 1024.0 * 1024.0))
        print("Storage free space:", free_space, "GiB")

        # Do not record or take snapshots when charging if so configured
        if self._boot.is_charging and not self.should_sleep_when_charging:
            print("We are charging, not recording.")
            return

        # Create the camera object
        try:
            self._camera = picamera.PiCamera()
            self._camera.resolution = self.resolution
        except picamera.PiCameraError:
            print("ERROR: Failed to initialize camera.")
            # ask the system to shut-down
            if self.camera_fail_shutdown:
                self._boot.shutdown()
                print("Requesting shutdown because of camera initialization fail.")
            return

        # Check for free space
        if free_space < 1:
            print("Not enough free space (less than 1 GiB), do not save snapshots or record")
            return
        else:
            # Store single snapshot only if above threshold, else do not record
            if not self._snapshot():
                # turn off video recording
                self._camera = None
                self.video_duration='off'
                # ask the system to shut-down
                if self.camera_fail_shutdown:
                    self._boot.shutdown()
                    print("Requesting shutdown because of low-light conditions.")
                return

        # Record a video of configured duration or until sleep.
        if self.video_duration == 'off':
            print("Not recording video as it is disabled.")
            return

        # Check if there is enough space to start recording
        print("Storage free space:", free_space, "GiB")
        if free_space < 2:
            print("Not enough free space (less than 2 GiB), skipping video recording")
            self._camera = None
            return

        print("Starting video recording (duration {}).".format(self.video_duration))
        self._camera.start_recording(
            os.path.join(
                CAMERA_STORAGE_PATH,
                'video-{year}-{month:02d}-{day:02d}-{hour:02d}-{minute:02d}-{second:02d}.h264'.format(
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    hour=now.hour,
                    minute=now.minute,
                    second=now.second,
                )
            ),
            format='h264'
        )
        self._recording_start = now

    def process(self, modules):
        # This runs if camera is initialized
        if self._camera:
            now = datetime.datetime.now()

            info = os.statvfs(CAMERA_STORAGE_PATH)
            free_space = (info.f_frsize * info.f_bavail / (1024.0 * 1024.0 * 1024.0))
            stop_recording=False

            # Stop recording if we happen to start charging
            if self._boot.is_charging and not self.should_sleep_when_charging:
                print("We are charging, stop recording.")
                stop_recording=True
            if free_space < 2:
                print("Not enough free space (less than 2 GiB), stop video recording")
                stop_recording=True
            # Check if duration of video is achieved.
            if self.video_duration_min is not None and now - self._recording_start >= self.video_duration_min:
                stop_recording=True
            # Stop recording
            if stop_recording:
                try:
                    self._camera.stop_recording()
                    print("Video recording has stopped after: ",now - self._recording_start)
                except:
                    pass

            # make snapshots if so defined and not recording
            if self.video_duration == 'off' and self.snapshot_interval is not None and now - self._last_snapshot >= self.snapshot_interval:
                self._snapshot()
        return

    def _check_light_conditions(self):
        """Check current light conditions."""
        image = None
        with picamera.array.PiRGBArray(self._camera) as output:
            self._camera.capture(output, format='rgb')
            image = output.array.astype(np.float32)

        # Compute light level.
        light_level = 0.2126 * image[..., 0] + 0.7152 * image[..., 1] + 0.0722 * image[..., 2]
        light_level = np.average(light_level)

        self.light_level = light_level

        return light_level > self.minimum_light_level

    def _snapshot(self):
        """Make a snapshot if there is enough light"""
        # Store single snapshot only if above threshold
        if self._check_light_conditions():
            now = datetime.datetime.now()
            self._last_snapshot = now

            self._camera.capture(
                os.path.join(
                    CAMERA_STORAGE_PATH,
                    'snapshot-{year}-{month:02d}-{day:02d}-{hour:02d}-{minute:02d}-{second:02d}-{light:.2f}.jpg'.format(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        hour=now.hour,
                        minute=now.minute,
                        second=now.second,
                        light=self.light_level,
                    )
                ),
                format='jpeg'
            )
            print("Snapshot taken at light level:", self.light_level)
            return True
        else:
            return False

    def shutdown(self, modules):
        """Shutdown module."""
        if self._camera:
            try:
                self._camera.stop_recording()
            except:
                pass

            self._camera.close()
            self._camera = None

    @property
    def should_sleep_when_charging(self):
        return os.environ.get('SLEEP_WHEN_CHARGING', '0') == '1'

    @property
    def camera_fail_shutdown(self):
        return os.environ.get('CAMERA_FAIL_SHUTDOWN', '0') == '1'
