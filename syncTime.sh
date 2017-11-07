#!/bin/bash
# file: syncTime.sh
# from https://github.com/uugear/Witty-Pi-2
# This script can syncronize the time between system and RTC
#


# get RTC time
rtctime="$(get_rtc_time)"

# if RTC time is OK, write RTC time to system first
if [[ $rtctime != *"1999"* ]] && [[ $rtctime != *"2000"* ]]; then
  rtc_to_system
fi

#if $(has_internet) ; then
 # # now take new time from NTP
  #log 'Internet detected, apply NTP time to system and Witty Pi...'
  #force_ntp_update
  #system_to_rtc
#else
  # get system year
  sysyear="$(date +%Y)"
  if [[ $rtctime == *"1999"* ]] || [[ $rtctime == *"2000"* ]]; then
    # if you never set RTC time before
    log 'RTC time has not been set before (stays in year 1999/2000).'
    if [[ $sysyear != *"1969"* ]] && [[ $sysyear != *"1970"* ]]; then
      # your Raspberry Pi has a decent time
      system_to_rtc
    else
      log 'Neither system nor Witty Pi contains correct time.'
    fi
  fi
#fi

get_rtc_time()
{
  local rtc_ts=$(get_rtc_timestamp)
  if [ "$rtc_ts" == "" ] ; then
    echo 'N/A'
  else
    echo $(date +'%a %d %b %Y %H:%M:%S %Z' -d @$rtc_ts)
  fi
}

get_sys_time()
{
  echo $(date +'%a %d %b %Y %H:%M:%S %Z')
}

get_rtc_timestamp()
{
  load_rtc
  LANG=C
  local rtctime=$(hwclock | awk '{$6=$7="";print $0}');
  unload_rtc
  if [ "$rtctime" == "" ] ; then
    echo ''
  else
    local rtctimestamp=$(date -d "$rtctime" +%s)
    echo $rtctimestamp
  fi
}
