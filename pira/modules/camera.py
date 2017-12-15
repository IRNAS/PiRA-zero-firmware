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

        self.resolution = os.environ.get('CAMERA_RESOLUTION', '1280x720')
        self.video_duration = os.environ.get('CAMERA_VIDEO_DURATION', 'until-sleep')
        try:
            self.video_duration_min = datetime.timedelta(minutes=int(self.video_duration))
        except ValueError:
            self.video_duration_min = None

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

    def process(self, modules):
        now = datetime.datetime.now()

        # Do not record when charging.
        if self._boot.is_charging and not self.should_sleep_when_charging:
            print("We are charging, not recording.")
            return

        if self._camera:
            # Check if we need to stop recording.
            if self.video_duration_min is not None and now - self._recording_start >= self.video_duration_min:
                try:
                    self._camera.stop_recording()
                except:
                    pass

            return

        try:
            self._camera = picamera.PiCamera()
            self._camera.resolution = self.resolution
        except picamera.PiCameraError:
            print("ERROR: Failed to initialize camera.")
            return

        # Check for minimum light requirements if configured. If there is no light, shut down.
        if not self._check_light_conditions():
            print("Not enough light, requesting shutdown.")
            self._boot.shutdown()
            return

        # Store single snapshot.
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

        # Check if there is enough free space left.
        info = os.statvfs(CAMERA_STORAGE_PATH)
        free_space = (info.f_frsize * info.f_bavail / (1024.0 * 1024.0 * 1024.0))
        print("Storage free space:", free_space, "GiB")
        if free_space < 1:
            print("Not enough free space (less than 1 GiB), skipping video recording")
            return

        # Record a video of configured duration or until sleep.
        if self.video_duration == 'off':
            print("Not recording video as it is disabled.")
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

    def _check_light_conditions(self):
        """Check current light conditions."""
        image = None
        with picamera.array.PiRGBArray(self._camera) as output:
            self._camera.capture(output, format='rgb')
            image = output.array.astype(np.float32)

        # Compute light level.
        light_level = 0.2126 * image[..., 0] + 0.7152 * image[..., 1] + 0.0722 * image[..., 2]
        light_level = np.average(light_level)

        print("Detected light level:", light_level)

        self.light_level = light_level

        return light_level > self.minimum_light_level

    def shutdown(self, modules):
        """Shutdown module."""
        if self._camera:
            try:
                self._camera.stop_recording()
            except:
                pass

            self._camera.close()
            self._camera = None
