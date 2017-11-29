from .messages import MeasurementConfig

# Log events.
LOG_SYSTEM = 'system'
LOG_DEVICE_VOLTAGE = 'device.voltage'
LOG_DEVICE_TEMPERATURE = 'device.temperature'

# Measurement configuration.
MEASUREMENT_DEVICE_VOLTAGE = MeasurementConfig(LOG_DEVICE_VOLTAGE, lambda value: int(value * 1000))
MEASUREMENT_DEVICE_TEMPERATURE = MeasurementConfig(LOG_DEVICE_TEMPERATURE, lambda value: int(value + 128))
