#!/bin/bash


log '  Writing system time to RTC...'

modprobe rtc-ds1307
if [ ! -d /sys/class/i2c-adapter/i2c-1/1-0068 ]; then
local output=$((sh -c 'echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device') 2>&1)
if [ ! -z "$output" ] && [ "sh: echo: I/O error" != "$output" ] ; then
  log "$output"
fi
fi

local err=$((hwclock -w) 2>&1)
if [ "$err" == "" ] ; then
log '  Done :-)'
else
log '  Failed :-('
log "$err"
fi

rmmod rtc-ds1307
