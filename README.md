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

## Behavior sleep
 * `on` - never go to sleep
 * `charging` - never sleep when charging
 * `debug` - never go to sleep when debug conditions are met
 * `off` - go to sleep imediately

## Behavior wifi WIFI_ENABLE_MODE
* `on` - always on when device is turned on
* `charging` - only when charging and debug
* `debug` - only when debug
* `off` -  always off


## Supported environment variables

The following environment variables can be used to configure the firmware:

* Global
  * `SLEEP_ENABLE_MODE` (default `sleep`) , options are:
    * `off` - do not sleep
    * `charging` - do not sleep when charging
    * `debug` - sleep even if debug mode is enabled
    * `sleep` - never sleep
  * `WIFI_ENABLE_MODE` (default `on`) , options are:
    * `on` - always on when device is turned on
    * `charging` - only when charging
    * `debug` - only when debug
    * `off` -  always off
  * `WIFI_SSID` (default `pira-01`), on non-resin ONLY for now
  * `WIFI_PASSWORD` (default `pirapira`), on non-resin ONLY for now
  * `DEBUG_ENABLE_MODE` (default `none`), can be `gpio:5` where number can be any BCM pin to turn on debug
  * `MODULES` a comma separated list of modules to load, the following is a list of all modules currently available `pira.modules.scheduler,pira.modules.ultrasonic,pira.modules.camera,pira.modules.lora,pira.modules.rockblock,pira.modules.debug,pira.modules.webserver`, delete the ones you do not wish to use.
  * `SHUTDOWN_STRATEGY` (default `reboot`) to configure if the unit will self-disable through GPIO and do a reboot (prevents hanging in shutdown if externally enabled by hardware) or `shutdown` strategy that will do a proper shutdown that is corruption safe, but may result in hanging in shutdown state or  `safe` that will do same as shutdown but with reboot and hope system clears the self-enable pin.
  * `SHUTDOWN_VOLTAGE` (default `2.6`V) to configure when the system should shutdown. At 2.6V hardware shutdown will occur, suggested value is 2.3-3V. When this is triggered, the device will wake up next based on the configured interval, unless the battery voltage continues to fall under the hardware limit, then it will boot again when it charges. Note this shutdown will be aborted if in debug mode.
  * `LATITUDE` (default `0`) to define location, used for sunrise/sunset calculation
  * `LONGITUDE` (default `0`) to define location
* Scheduler
  * `SCHEDULE_START` (default `00:01`), option is also `sunrise` calculated automatically if lat/long are defined
  * `SCHEDULE_END` (default `23:59`), option is also `sunset`calculated automatically if lat/long are defined
  * `SCHEDULE_T_ON` (default `5`), remains on for specified time in minutes
  * `SCHEDULE_T_OFF` (default `55`), remains off for specified time in minutes
  * `POWER_THRESHOLD_HALF` (default `0`), voltage at which `SCHEDULE_T_OFF` time is doubled, suggested `3.7`
  * `POWER_THRESHOLD_QUART` (default `0`), voltage at which `SCHEDULE_T_OFF` time is quadrupled, suggested `3.4`
* Camera
  * `CAMERA_RESOLUTION` (default `1280x720`, options are `1280x720`, `1920x1080`, `2592x1952` and some others. Mind fi copying resolution that you use the letter `x` not a multiply character.)
  * `CAMERA_VIDEO_DURATION` (default `until-sleep`, duration in minutes or `off`)
  * `CAMERA_MIN_LIGHT_LEVEL` (default `0.0`, minimum required for video to start recording)
  * `CAMERA_FAIL_SHUTDOWN` (default `0`), can camera shutdown the device for example if not enough light, set to `1` to enable
  * `CAMERA_SNAPSHOT_INTERVAL` (default `off`, duration in minutes to be configured)
* Rockblock
  * `ROCKBLOCK_REPORT_INTERVAL` (default `24`)
  * `ROCKBLOCK_RETRIES` (default `2`)
* LoRa
  * `LORA_DEVICE_ADDR`
  * `LORA_NWS_KEY`
  * `LORA_APPS_KEY`
  * `LORA_SPREAD_FACTOR` (default `7`)
* Nodewatcher (to report measurements to Nodewatcher platform)
  * `NODEWATCHER_UUID`
  * `NODEWATCHER_HOST`
  * `NODEWATCHER_KEY`
* Sensors
  * `MCP3021_RATIO` (default `0.0217`) is the conversion value between raw reading and voltage, measure and calibrate for more precise readings
* CAN (MCP2515)
  * `CAN_SPEED` (default 500000) is the speed of the CAN Bus
* M2X
  * `M2X_KEY` (must have) is the key of your M2X account
  * `M2X_DEVICE_ID` (must have) is the device ID you are connecting to
  * `M2X_NAME` (default `DEMO_PI`) is the name of the set of data
* AZURE
  * `AZURE_ACCOUNT_NAME` (must have) is the name 
  * `AZURE_ACCOUNT_KEY` (must have) is the account key
  * `AZURE_CONTAINER_NAME` (default ImageExample) is the container name in the blob


 ### Using without Resin.io
 To use on a standard Raspbian Lite image complete the following steps:
  * Install Raspbian Lite
  * Install all required packages with `apt-get` and 'pip', see `Dockerfile.template` and `requirements.txt` for what is needed, possibly some other packages are required as well
  * Create the /data folder by running `sudo mkdir /data/`
  * Configure environmental variables by adding them to the end of `/etc/environment` file, for example `SLEEP_WHEN_CHARGING="1"`
  * Run the start script by (-E is required to read environment variables correctly):
  ```
  cd PiRA-zero-firmware
  sudo -E ./start.sh
  ```
 ### Using it with Resin.io Local Mode
 To use it with Local Mode (Development) with Resin.io
  * Download resin-cl
  * Rename Dockerfile.template to `Dockerfile`
  * Execute ```sudo ./resin local scan``` to scan the local network
  * To push the firmware ```sudo ./resin local push ID_HERE -s LOCATION```
  
 Extra useful things:
  * Enviroment variables place in: `.resin-sync.yml` like this: 
	```
	environment:
		- AZURE_ACCOUNT_NAME=rpiimages
	```
