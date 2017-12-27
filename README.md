# PiRA-zero-firmware
Firmware for PiRa Zero board implementing hardware interface functions.

## Software support for hardware features
 * USB charger BQ24296 I2c
 * RTC DS3231 I2C
 * ADC MCP3021 I2C
 * Display SSD1306 I2C
 * RFM95 Lora SPI

## Board support package
 * GPIO for power scheduling
 * GPIO for power output

### Power scheduling
On boot:
 1. Detect power-up trigger
  * if BCM17 (Timer-EN) is LOW then
    * Self-enable, if reboot and BCM18 is HIGH
    * else Timer enable
    * corner case, reboot due to self enable and timer at the same time, must clear timer in any case
  * if BCM 22 is LOW then
    * RTC enable if alarm is high, check via I2C
    * else enabled due to charging
  * none of the above, handle by resetting all timing soruces
 1. Self-enable GPIO BCM 18 to stay turned on
 1. Reset timing sources
  * assert Done for Timer on BCM27
  * reset RTC alarms

 During operation:
  1. monitor BCM17 and BCM22 for changes, repeat Detect power-up if needed

 On Shutdown:
  1. Check RTC wakeup is at least 30s away from now.
  1. do shutdown


### Application specific features
 1. Capture camera image and check for daylight/minimal light in image (maybe https://github.com/pageauc/pi-timolo)
 1. WiFi connect and hotspot https://github.com/resin-io/resin-wifi-connect
 1. Capture video for some time if sufficient light is available
 1. Measure distance with MB7092XL-MaxSonar-WRMA1
 1. Send data to TheThingsNetwork
 1. Send data over RockBlock Iridium modem

## Fleet configuration variables
The following fleet configuration variables must be defined for correct operation:
 * `RESIN_HOST_CONFIG_dtoverlay` to value `pi3-miniuart-bt`
 * `RESIN_HOST_CONFIG_gpu_mem` to value `128`, required by camera
 * `RESIN_HOST_CONFIG_start_x` to value `1`, required by camera
 * `RESIN_SUPERVISOR_DELTA` to value `1`, so updates are faster, optional.

## Supported environment variables

The following environment variables can be used to configure the firmware:

* Global
  * `SLEEP_WHEN_CHARGING` (default `0`) when set to `1` the unit will sleep while it is charging.
  * `SLEEP_NEVER` (default `0`) when set to `1` the unit will never go to sleep.
  * `WIFI_WHEN_NOT_CHARGING` (default `1`) when set to `0` wifi will be disable while not charging.
  * `MODULES` a comma separated list of modules to load, the following is a list of all modules currently available `pira.modules.scheduler,pira.modules.ultrasonic,pira.modules.camera,pira.modules.lora,pira.modules.rockblock,pira.modules.debug,pira.modules.webserver`, delete the ones you do not wish to use.
  * `SHUTDOWN_STRATEGY` (default `reboot`) to configure if the unit will self-disable through GPIO and do a reboot (prevents hanging in shutdown if externally enabled by hardware) or `shutdown` strategy that will do a proper shutdown that is corruption safe, but may result in hanging in shutdown state.
  * `SHUTDOWN_VOLTAGE` (default `2.6`V) to configure when the system should shutdown. At 2.6V hardware shutdown will occur, suggested value is 2.3-3V. When this is triggered, the device will wake up next based on the configured interval, unless the battery voltage continues to fall under the hardware limit, then it will boot again when it charges. Note this shutdown will be aborted if `SLEEP_WHEN_CHARGING==0` or `SLEEP_NEVER==1`
* Scheduler
  * `SCHEDULE_START` (default `08:00`)
  * `SCHEDULE_END` (default `18:00`)
  * `SCHEDULE_T_ON` (default `15`)
  * `SCHEDULE_T_OFF` (default `35`)
* Camera
  * `CAMERA_RESOLUTION` (default `1280x720`, options are `1280x720`, `1920x1080`, `2592x1944` and some others. Mind fi copying resolution that you use the letter `x` not a multiply character.)
  * `CAMERA_VIDEO_DURATION` (default `until-sleep`, duration in minutes or `off`)
  * `CAMERA_MIN_LIGHT_LEVEL` (default `0.0`, minimum required for video to start recording)
* Rockblock
  * `ROCKBLOCK_REPORT_INTERVAL` (default `24`)
  * `ROCKBLOCK_RETRIES` (default `2`)
* LoRa
  * `LORA_DEVICE_ADDR`
  * `LORA_NWS_KEY`
  * `LORA_APPS_KEY`
  * `LORA_SPREAD_FACTOR` (default `7`)
