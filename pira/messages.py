import collections
import io
import struct

# Measurement conversion configuration.
MeasurementConfig = collections.namedtuple('MeasurementConfig', ['log_type', 'conversion'])


def create_measurements_message(boot, timestamp, measurements):
    """Create measurements report message.

    Message format (network byte order):
    - 2 bytes: unsigned integer, number of measurements
    - 2 bytes: unsigned integer, average
    - 2 bytes: unsigned integer, min
    - 2 bytes: unsigned integer, max

    In case there is no measurements to report in the given time
    interval, None is returned.

    :param boot: Boot instance
    :param timestamp: Measuerements start timestamp
    :param measurements: List of measurement types to include, where each
        element is a MeasurementConfig instance
    """
    have_measurements = False
    message = io.BytesIO()
    for config in measurements:
        values = boot.log.query(timestamp, config.log_type, only_numeric=True)
        converter = config.conversion or int

        # Compute statistics.
        if values:
            count = len(values)
            average = converter(sum(values) / count)
            min_value = converter(min(values))
            max_value = converter(max(values))
            have_measurements = True
        else:
            count = 0
            average = 0
            min_value = 0
            max_value = 0

        message.write(struct.pack('!HHHH', count, average, min_value, max_value))

    if not have_measurements:
        return

    message = message.getvalue()
    return message
